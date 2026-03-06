import uvicorn

from college.config.settings import get_settings


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "college.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
