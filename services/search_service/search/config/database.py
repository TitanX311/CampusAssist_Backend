from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from search.config.settings import get_settings

settings = get_settings()

_db_url = (
    settings.DATABASE_URL
    .replace("postgresql://", "postgresql+asyncpg://", 1)
    .replace("postgres://", "postgresql+asyncpg://", 1)
)

engine = create_async_engine(
    _db_url,
    echo=settings.DEBUG,
    # Connection pool tuning for high query volume
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
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
