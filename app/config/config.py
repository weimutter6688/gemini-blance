"""
应用程序配置模块
"""
from typing import List
from pydantic_settings import BaseSettings

from app.core.constants import API_VERSION, DEFAULT_CREATE_IMAGE_MODEL, DEFAULT_FILTER_MODELS, DEFAULT_MODEL, DEFAULT_STREAM_CHUNK_SIZE, DEFAULT_STREAM_LONG_TEXT_THRESHOLD, DEFAULT_STREAM_MAX_DELAY, DEFAULT_STREAM_MIN_DELAY, DEFAULT_STREAM_SHORT_TEXT_THRESHOLD, DEFAULT_TIMEOUT


class Settings(BaseSettings):
    """应用程序配置"""
    # API相关配置
    API_KEYS: List[str]
    ALLOWED_TOKENS: List[str]
    BASE_URL: str = f"https://generativelanguage.googleapis.com/{API_VERSION}"
    AUTH_TOKEN: str = ""
    MAX_FAILURES: int = 3
    TEST_MODEL: str = DEFAULT_MODEL
    TIME_OUT: int = DEFAULT_TIMEOUT
    
    # 模型相关配置
    SEARCH_MODELS: List[str] = ["gemini-2.0-flash-exp"]
    IMAGE_MODELS: List[str] = ["gemini-2.0-flash-exp"]
    FILTERED_MODELS: List[str] = DEFAULT_FILTER_MODELS
    TOOLS_CODE_EXECUTION_ENABLED: bool = False
    SHOW_SEARCH_LINK: bool = True
    SHOW_THINKING_PROCESS: bool = True
    
    # 图像生成相关配置
    PAID_KEY: str = ""
    CREATE_IMAGE_MODEL: str = DEFAULT_CREATE_IMAGE_MODEL
    UPLOAD_PROVIDER: str = "smms"
    SMMS_SECRET_TOKEN: str = ""
    PICGO_API_KEY: str = ""
    CLOUDFLARE_IMGBED_URL: str = ""
    CLOUDFLARE_IMGBED_AUTH_CODE: str = ""
    
    # 流式输出优化器配置
    STREAM_OPTIMIZER_ENABLED: bool = False
    STREAM_MIN_DELAY: float = DEFAULT_STREAM_MIN_DELAY
    STREAM_MAX_DELAY: float = DEFAULT_STREAM_MAX_DELAY
    STREAM_SHORT_TEXT_THRESHOLD: int = DEFAULT_STREAM_SHORT_TEXT_THRESHOLD
    STREAM_LONG_TEXT_THRESHOLD: int = DEFAULT_STREAM_LONG_TEXT_THRESHOLD
    STREAM_CHUNK_SIZE: int = DEFAULT_STREAM_CHUNK_SIZE
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置默认AUTH_TOKEN（如果未提供）
        if not self.AUTH_TOKEN and self.ALLOWED_TOKENS:
            self.AUTH_TOKEN = self.ALLOWED_TOKENS[0]
    
    class Config:
        env_file = ".env"


# 创建全局配置实例
settings = Settings()
