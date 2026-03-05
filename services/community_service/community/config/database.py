from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from community.config.settings import get_settings

settings = get_settings()

# Normalise URL: handle both postgresql:// and postgres:// variants
_db_url = (
    settings.DATABASE_URL
    .replace("postgresql://", "postgresql+asyncpg://", 1)
    .replace("postgres://", "postgresql+asyncpg://", 1)
)

engine = create_async_engine(_db_url, echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        yield session
