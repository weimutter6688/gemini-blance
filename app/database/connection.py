"""
数据库连接池模块
"""
from databases import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base

from app.config.config import settings
from app.log.logger import get_database_logger

logger = get_database_logger()

# 数据库URL
DATABASE_URL = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建元数据对象
metadata = MetaData()

# 创建基类
Base = declarative_base(metadata=metadata)

# 创建数据库连接池，并配置连接池参数
# pool_recycle=3600: 回收空闲超过1小时的连接，防止MySQL服务器超时断开
database = Database(DATABASE_URL, min_size=5, max_size=20, pool_recycle=3600)


async def connect_to_db():
    """
    连接到数据库
    """
    try:
        await database.connect()
        logger.info("Connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise


async def disconnect_from_db():
    """
    断开数据库连接
    """
    try:
        await database.disconnect()
        logger.info("Disconnected from database")
    except Exception as e:
        logger.error(f"Failed to disconnect from database: {str(e)}")
