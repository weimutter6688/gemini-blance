from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    API_KEYS: List[str]
    ALLOWED_TOKENS: List[str]
    BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    SEARCH_MODELS: List[str] = ["gemini-2.0-flash-exp"]
    IMAGE_MODELS: List[str] = ["gemini-2.0-flash-exp"]
    FILTERED_MODELS: List[str] = ["gemini-1.0-pro-vision-latest", "gemini-pro-vision", "chat-bison-001", "text-bison-001", "embedding-gecko-001"]
    TOOLS_CODE_EXECUTION_ENABLED: bool = False
    SHOW_SEARCH_LINK: bool = True
    SHOW_THINKING_PROCESS: bool = True
    AUTH_TOKEN: str = ""
    MAX_FAILURES: int = 3
    PAID_KEY: str = ""
    CREATE_IMAGE_MODEL: str = "imagen-3.0-generate-002"
    UPLOAD_PROVIDER: str = "smms"
    SMMS_SECRET_TOKEN: str = ""
    PICGO_API_KEY: str = ""
    CLOUDFLARE_IMGBED_URL: str = ""
    CLOUDFLARE_IMGBED_AUTH_CODE: str = ""
    TEST_MODEL: str = "gemini-1.5-flash"
    
    # 流式输出优化器配置
    STREAM_MIN_DELAY: float = 0.016
    STREAM_MAX_DELAY: float = 0.024
    STREAM_SHORT_TEXT_THRESHOLD: int = 10
    STREAM_LONG_TEXT_THRESHOLD: int = 50
    STREAM_CHUNK_SIZE: int = 5

    def __init__(self):
        super().__init__()
        if not self.AUTH_TOKEN:
            self.AUTH_TOKEN = self.ALLOWED_TOKENS[0] if self.ALLOWED_TOKENS else ""

    class Config:
        env_file = ".env"


settings = Settings()
