"""
Search index tables.

Two tables mirror data from college_service and community_service:

  college_index   — stores indexed college records
  community_index — stores indexed community records

Both carry a tsvector `search_vector` column that is populated at upsert
time via `setweight(to_tsvector(...))` raw SQL so we stay compatible with
async SQLAlchemy without requiring generated-column support.

GIN indexes on `search_vector` make full-text lookups O(log N) even at
millions of rows.  A second GIN index on `name` using the pg_trgm ops-class
supports fuzzy / prefix matching for short queries.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from search.models.base import Base


class CollegeIndex(Base):
    __tablename__ = "college_index"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    contact_email: Mapped[str] = mapped_column(String, default="", server_default="")
    physical_address: Mapped[str] = mapped_column(String, default="", server_default="")
    community_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Populated via raw SQL on every upsert — do NOT write from Python
    search_vector: Mapped[str] = mapped_column(TSVECTOR, nullable=True)

    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        # Full-text search index
        Index("idx_college_fts", "search_vector", postgresql_using="gin"),
        # Trigram index for fuzzy / prefix matching
        Index(
            "idx_college_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )


class CommunityIndex(Base):
    __tablename__ = "community_index"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    community_type: Mapped[str] = mapped_column(String, nullable=False)
    parent_colleges: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list, server_default="{}"
    )
    member_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Populated via raw SQL on every upsert
    search_vector: Mapped[str] = mapped_column(TSVECTOR, nullable=True)

    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_community_fts", "search_vector", postgresql_using="gin"),
        Index(
            "idx_community_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )
