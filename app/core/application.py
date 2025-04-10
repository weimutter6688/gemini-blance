"""
应用程序工厂模块，负责创建和配置FastAPI应用程序实例
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config.config import settings, sync_initial_settings
from app.log.logger import get_application_logger
from app.middleware.middleware import setup_middlewares
from app.exception.exceptions import setup_exception_handlers
from app.router.routes import setup_routers
from app.service.key.key_manager import get_key_manager_instance
from app.core.initialization import initialize_app
from app.database.connection import connect_to_db, disconnect_from_db
from app.database.initialization import initialize_database
from app.scheduler.key_checker import start_scheduler, stop_scheduler # 导入调度器函数

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
        # 初始化数据库
        initialize_database()
        logger.info("Database initialized successfully")
        
        # 连接到数据库
        await connect_to_db()
        
        # 同步初始配置（DB优先，然后同步回DB）
        await sync_initial_settings()

        # 初始化KeyManager (使用可能已从DB更新的settings)
        await get_key_manager_instance(settings.API_KEYS)
        logger.info("KeyManager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise

    # 启动调度器
    start_scheduler()
    logger.info("Scheduler started successfully.")

    yield  # 应用程序运行期间
    
    # 关闭事件
    logger.info("Application shutting down...")
    
    # 停止调度器
    stop_scheduler()
    logger.info("Scheduler stopped.")

    # 断开数据库连接
    await disconnect_from_db()

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
