import uvicorn

from post.config.settings import get_settings

settings = get_settings()

if __name__ == "__main__":
    uvicorn.run(
        "post.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
