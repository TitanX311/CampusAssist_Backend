import uvicorn

from admin.config.settings import get_settings


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "admin.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
