import uvicorn

from comment.config.settings import get_settings

settings = get_settings()

if __name__ == "__main__":
    uvicorn.run(
        "comment.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
