"""
Search repository — all raw SQL for maximum PostgreSQL FTS performance.

Query strategy (applied to both college and community tables):

1. Full-text search via tsvector @@ websearch_to_tsquery()
   - weighted (name = A, address/email = B/C for colleges)
   - ranked by ts_rank_cd (covers-density ranking)

2. Trigram similarity fallback via similarity(name, :q) > threshold
   - catches short/misspelled queries missed by FTS
   - uses GIN(gin_trgm_ops) index

3. Combined relevance score = ts_rank + 0.4 × trgm_similarity
   - results ordered by score DESC, then name ASC

4. COUNT(*) OVER() window function returns total without a second query.

For combined (all) searches, both tables are UNION ALL'd and re-ranked.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text, bindparam
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Minimum trigram similarity to include a result (0–1)
_TRGM_THRESHOLD = "0.15"


class SearchRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Upsert ──────────────────────────────────────────────────────────────

    async def upsert_college(self, college: dict[str, Any]) -> None:
        """Insert or update a college in the search index with weighted tsvector."""
        # Note: _sv suffix params are duplicates used only in the tsvector expression.
        # asyncpg raises AmbiguousParameterError when the same $N param appears in both
        # a VARCHAR column position and a text function — separate names avoids this.
        await self.db.execute(
            text("""
                INSERT INTO college_index
                    (id, name, contact_email, physical_address, community_count,
                     search_vector, indexed_at)
                VALUES (
                    :id, :name, :contact_email, :physical_address, :community_count,
                    setweight(to_tsvector('english', unaccent(coalesce(:name_sv, ''))), 'A') ||
                    setweight(to_tsvector('english', unaccent(coalesce(:address_sv, ''))), 'B') ||
                    setweight(to_tsvector('english', unaccent(coalesce(:email_sv, ''))), 'C'),
                    NOW()
                )
                ON CONFLICT (id) DO UPDATE SET
                    name             = EXCLUDED.name,
                    contact_email    = EXCLUDED.contact_email,
                    physical_address = EXCLUDED.physical_address,
                    community_count  = EXCLUDED.community_count,
                    search_vector    = EXCLUDED.search_vector,
                    indexed_at       = NOW()
            """),
            {
                "id": str(college["id"]),
                "name": college.get("name", ""),
                "name_sv": college.get("name", ""),
                "contact_email": college.get("contact_email", ""),
                "email_sv": college.get("contact_email", ""),
                "physical_address": college.get("physical_address", ""),
                "address_sv": college.get("physical_address", ""),
                "community_count": len(college.get("communities", [])),
            },
        )

    async def upsert_community(self, community: dict[str, Any]) -> None:
        """Insert or update a community in the search index."""
        # Note: CAST(:parent_colleges AS text[]) avoids SQLAlchemy text() parser bug where
        # :param::type[] is misread (the '::' right after the param name trips the parser).
        # bindparam with ARRAY(String) tells asyncpg the exact wire type to use.
        await self.db.execute(
            text("""
                INSERT INTO community_index
                    (id, name, community_type, parent_colleges, member_count,
                     search_vector, indexed_at)
                VALUES (
                    :id, :name, :community_type,
                    CAST(:parent_colleges AS text[]),
                    :member_count,
                    setweight(to_tsvector('english', unaccent(coalesce(:name_sv, ''))), 'A'),
                    NOW()
                )
                ON CONFLICT (id) DO UPDATE SET
                    name            = EXCLUDED.name,
                    community_type  = EXCLUDED.community_type,
                    parent_colleges = EXCLUDED.parent_colleges,
                    member_count    = EXCLUDED.member_count,
                    search_vector   = EXCLUDED.search_vector,
                    indexed_at      = NOW()
            """).bindparams(
                bindparam("parent_colleges", type_=ARRAY(String))
            ),
            {
                "id": str(community["id"]),
                "name": community.get("name", ""),
                "name_sv": community.get("name", ""),
                "community_type": community.get("type", "PUBLIC"),
                "parent_colleges": [str(c) for c in community.get("parent_colleges", [])],
                "member_count": len(community.get("member_users", [])),
            },
        )

    async def delete_college(self, college_id: str) -> None:
        await self.db.execute(
            text("DELETE FROM college_index WHERE id = :id"), {"id": college_id}
        )

    async def delete_community(self, community_id: str) -> None:
        await self.db.execute(
            text("DELETE FROM community_index WHERE id = :id"), {"id": community_id}
        )

    async def clear_all(self) -> None:
        await self.db.execute(text("TRUNCATE college_index, community_index"))

    # ── Search ───────────────────────────────────────────────────────────────

    async def search_colleges(
        self, q: str, page: int, page_size: int
    ) -> tuple[list[dict], int]:
        rows = (
            await self.db.execute(
                text(f"""
                    SELECT
                        id, name, contact_email, physical_address, community_count,
                        ts_rank_cd(search_vector,
                            websearch_to_tsquery('english', unaccent(:q))) AS fts_rank,
                        similarity(name, :q) AS trgm_rank,
                        COUNT(*) OVER() AS total
                    FROM college_index
                    WHERE
                        search_vector @@ websearch_to_tsquery('english', unaccent(:q))
                        OR similarity(name, :q) > {_TRGM_THRESHOLD}
                    ORDER BY
                        (ts_rank_cd(search_vector,
                            websearch_to_tsquery('english', unaccent(:q)))
                         + similarity(name, :q) * 0.4) DESC,
                        name ASC
                    LIMIT :lim OFFSET :off
                """),
                {"q": q, "lim": page_size, "off": (page - 1) * page_size},
            )
        ).fetchall()

        total = int(rows[0].total) if rows else 0
        return (
            [
                {
                    "id": r.id,
                    "name": r.name,
                    "type": "college",
                    "score": round(float(r.fts_rank) + float(r.trgm_rank) * 0.4, 4),
                    "contact_email": r.contact_email,
                    "physical_address": r.physical_address,
                    "community_count": r.community_count,
                    "community_type": None,
                    "parent_colleges": None,
                    "member_count": None,
                }
                for r in rows
            ],
            total,
        )

    async def search_communities(
        self, q: str, page: int, page_size: int, college_id: str | None = None
    ) -> tuple[list[dict], int]:
        filter_clause = ""
        params: dict[str, Any] = {
            "q": q,
            "lim": page_size,
            "off": (page - 1) * page_size,
        }
        if college_id:
            filter_clause = "AND :college_id = ANY(parent_colleges)"
            params["college_id"] = college_id

        rows = (
            await self.db.execute(
                text(f"""
                    SELECT
                        id, name, community_type, parent_colleges, member_count,
                        ts_rank_cd(search_vector,
                            websearch_to_tsquery('english', unaccent(:q))) AS fts_rank,
                        similarity(name, :q) AS trgm_rank,
                        COUNT(*) OVER() AS total
                    FROM community_index
                    WHERE (
                        search_vector @@ websearch_to_tsquery('english', unaccent(:q))
                        OR similarity(name, :q) > {_TRGM_THRESHOLD}
                    )
                    {filter_clause}
                    ORDER BY
                        (ts_rank_cd(search_vector,
                            websearch_to_tsquery('english', unaccent(:q)))
                         + similarity(name, :q) * 0.4) DESC,
                        name ASC
                    LIMIT :lim OFFSET :off
                """),
                params,
            )
        ).fetchall()

        total = int(rows[0].total) if rows else 0
        return (
            [
                {
                    "id": r.id,
                    "name": r.name,
                    "type": "community",
                    "score": round(float(r.fts_rank) + float(r.trgm_rank) * 0.4, 4),
                    "contact_email": None,
                    "physical_address": None,
                    "community_count": None,
                    "community_type": r.community_type,
                    "parent_colleges": list(r.parent_colleges or []),
                    "member_count": r.member_count,
                }
                for r in rows
            ],
            total,
        )

    async def search_all(
        self, q: str, page: int, page_size: int
    ) -> tuple[list[dict], int]:
        """
        UNION search across both tables in a single query.
        Merges and re-ranks in the DB — no Python-side merging needed.
        """
        rows = (
            await self.db.execute(
                text(f"""
                    WITH ranked AS (
                        SELECT
                            id, name,
                            'college'::text AS result_type,
                            contact_email,
                            physical_address,
                            community_count,
                            NULL::text           AS community_type,
                            NULL::text[]         AS parent_colleges,
                            NULL::int            AS member_count,
                            ts_rank_cd(search_vector,
                                websearch_to_tsquery('english', unaccent(:q))) AS fts_rank,
                            similarity(name, :q) AS trgm_rank
                        FROM college_index
                        WHERE
                            search_vector @@ websearch_to_tsquery('english', unaccent(:q))
                            OR similarity(name, :q) > {_TRGM_THRESHOLD}

                        UNION ALL

                        SELECT
                            id, name,
                            'community'::text AS result_type,
                            NULL::text        AS contact_email,
                            NULL::text        AS physical_address,
                            NULL::int         AS community_count,
                            community_type,
                            parent_colleges,
                            member_count,
                            ts_rank_cd(search_vector,
                                websearch_to_tsquery('english', unaccent(:q))) AS fts_rank,
                            similarity(name, :q) AS trgm_rank
                        FROM community_index
                        WHERE
                            search_vector @@ websearch_to_tsquery('english', unaccent(:q))
                            OR similarity(name, :q) > {_TRGM_THRESHOLD}
                    )
                    SELECT *, COUNT(*) OVER() AS total
                    FROM ranked
                    ORDER BY (fts_rank + trgm_rank * 0.4) DESC, name ASC
                    LIMIT :lim OFFSET :off
                """),
                {"q": q, "lim": page_size, "off": (page - 1) * page_size},
            )
        ).fetchall()

        total = int(rows[0].total) if rows else 0
        return (
            [
                {
                    "id": r.id,
                    "name": r.name,
                    "type": r.result_type,
                    "score": round(float(r.fts_rank) + float(r.trgm_rank) * 0.4, 4),
                    "contact_email": r.contact_email,
                    "physical_address": r.physical_address,
                    "community_count": r.community_count,
                    "community_type": r.community_type,
                    "parent_colleges": list(r.parent_colleges) if r.parent_colleges else None,
                    "member_count": r.member_count,
                }
                for r in rows
            ],
            total,
        )

    # ── Stats ────────────────────────────────────────────────────────────────

    async def index_stats(self) -> dict[str, Any]:
        row = (
            await self.db.execute(
                text("""
                    SELECT
                        (SELECT COUNT(*) FROM college_index)   AS college_count,
                        (SELECT COUNT(*) FROM community_index) AS community_count,
                        (SELECT MAX(indexed_at) FROM (
                            SELECT indexed_at FROM college_index
                            UNION ALL
                            SELECT indexed_at FROM community_index
                        ) t) AS last_indexed_at
                """)
            )
        ).fetchone()
        return {
            "college_count": int(row.college_count),
            "community_count": int(row.community_count),
            "last_indexed_at": row.last_indexed_at.isoformat() if row.last_indexed_at else None,
        }
