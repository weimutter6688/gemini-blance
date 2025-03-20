"""
应用程序入口模块
"""

import uvicorn

from app.core.application import create_app
from app.log.logger import get_main_logger

# 创建应用程序实例
app = create_app()

# 配置日志
logger = get_main_logger()

if __name__ == "__main__":
    logger.info("Starting application server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
