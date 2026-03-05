import uvicorn

from community.config.settings import get_settings


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "community.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
