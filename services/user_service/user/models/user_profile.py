import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserProfile(Base):
    """
    Local cache of user profile + stats.

    The canonical identity data lives in auth_service.  This table caches it
    so that the user service can serve responses without hitting auth_service on
    every request.  ``last_synced_at`` drives cache invalidation.

    ACID notes
    ----------
    * All write paths use ``SELECT … FOR UPDATE`` (``get_by_id_for_update``) to
      prevent lost-update anomalies when two concurrent requests for the same
      user both see a stale cache and race to refresh it.
    * The engine is built with ``statement_cache_size=0`` (asyncpg quirk) and
      ``pool_pre_ping=True``.
    * Session commit/rollback is handled by the ``get_db`` dependency so every
      mutation either fully commits or fully rolls back.
    """

    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    picture: Mapped[str | None] = mapped_column(String, nullable=True)
    user_type: Mapped[str] = mapped_column(String, nullable=False, default="USER")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Aggregated stats (refreshed on demand, bounded by STATS_CACHE_TTL_SECONDS)
    post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    community_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    joined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
