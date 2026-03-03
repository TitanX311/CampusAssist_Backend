import uvicorn

from auth.config.settings import get_settings


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "auth.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )