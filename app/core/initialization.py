"""
应用程序初始化模块
"""
from pathlib import Path
from typing import List

from app.log.logger import get_initialization_logger

logger = get_initialization_logger()


def ensure_directories_exist(directories: List[str]) -> None:
    """
    确保指定的目录存在，如果不存在则创建
    
    Args:
        directories: 要确保存在的目录列表
    """
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {str(e)}")


def initialize_app() -> None:
    """
    初始化应用程序，确保所需的目录和文件都存在
    """
    # 确保必要的目录存在
    required_directories = [
        "app/static/css",
        "app/static/js",
        "app/static/icons",
        "app/templates",
    ]
    
    ensure_directories_exist(required_directories)
    logger.info("Application initialization completed")
