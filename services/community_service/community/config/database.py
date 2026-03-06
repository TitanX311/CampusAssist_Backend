from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from community.config.settings import get_settings

settings = get_settings()

# Normalise URL: handle both postgresql:// and postgres:// variants
_db_url = (
    settings.DATABASE_URL
    .replace("postgresql://", "postgresql+asyncpg://", 1)
    .replace("postgres://", "postgresql+asyncpg://", 1)
)

engine = create_async_engine(
    _db_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    # asyncpg's prepared-statement cache conflicts with SELECT … FOR UPDATE;
    # disabling it forces the simple-query protocol and fixes the issue.
    connect_args={"statement_cache_size": 0},
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
