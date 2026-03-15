from src.main import app
from src.utils.settings import settings
from src.utils.logger import logger

if __name__ == "__main__":
    import uvicorn
    logger.info(f"启动服务器，监听地址: {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    uvicorn.run(app, host=settings.SERVER_HOST, port=settings.SERVER_PORT)
