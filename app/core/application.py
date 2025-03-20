"""
应用程序工厂模块，负责创建和配置FastAPI应用程序实例
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config.config import settings
from app.log.logger import get_application_logger
from app.middleware.middleware import setup_middlewares
from app.exception.exceptions import setup_exception_handlers
from app.router.routes import setup_routers
from app.service.key.key_manager import get_key_manager_instance
from app.core.initialization import initialize_app

logger = get_application_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用程序生命周期管理器
    
    Args:
        app: FastAPI应用实例
    """
    # 启动事件
    logger.info("Application starting up...")
    try:
        # 初始化KeyManager
        await get_key_manager_instance(settings.API_KEYS)
        logger.info("KeyManager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize KeyManager: {str(e)}")
        raise
    
    yield  # 应用程序运行期间
    
    # 关闭事件
    logger.info("Application shutting down...")

def create_app() -> FastAPI:
    """
    创建并配置FastAPI应用程序实例
    
    Returns:
        FastAPI: 配置好的FastAPI应用程序实例
    """
    # 初始化应用程序
    initialize_app()
    
    # 创建FastAPI应用
    app = FastAPI(
        title="Gemini Balance API",
        description="Gemini API代理服务，支持负载均衡和密钥管理",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # 配置静态文件
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
    # 配置中间件
    setup_middlewares(app)
    
    # 配置异常处理器
    setup_exception_handlers(app)
    
    # 配置路由
    setup_routers(app)
    
    return app
