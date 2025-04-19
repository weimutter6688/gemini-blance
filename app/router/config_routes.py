"""
配置路由模块
"""
from typing import Any, Dict, List, Optional # Import List and Optional
from pydantic import BaseModel # Import BaseModel
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core.security import verify_auth_token
from app.log.logger import get_config_routes_logger
from app.service.config.config_service import ConfigService

# 创建路由
router = APIRouter(prefix="/api/config", tags=["config"])

logger = get_config_routes_logger()

# Define a specific response model mirroring Settings structure
class ConfigResponse(BaseModel):
    HTTP_PROXY: Optional[str] = None
    HTTPS_PROXY: Optional[str] = None
    PROXY_ENABLED: bool = False
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str
    API_KEYS: List[str]
    ALLOWED_TOKENS: List[str]
    BASE_URL: str
    AUTH_TOKEN: str
    MAX_FAILURES: int
    TEST_MODEL: str
    TIME_OUT: int
    MAX_RETRIES: int
    SEARCH_MODELS: List[str]
    IMAGE_MODELS: List[str]
    FILTERED_MODELS: List[str]
    TOOLS_CODE_EXECUTION_ENABLED: bool
    SHOW_SEARCH_LINK: bool
    SHOW_THINKING_PROCESS: bool
    PAID_KEY: str
    CREATE_IMAGE_MODEL: str
    UPLOAD_PROVIDER: str
    SMMS_SECRET_TOKEN: str
    PICGO_API_KEY: str
    CLOUDFLARE_IMGBED_URL: str
    CLOUDFLARE_IMGBED_AUTH_CODE: str
    STREAM_OPTIMIZER_ENABLED: bool
    STREAM_MIN_DELAY: float
    STREAM_MAX_DELAY: float
    STREAM_SHORT_TEXT_THRESHOLD: int
    STREAM_LONG_TEXT_THRESHOLD: int
    STREAM_CHUNK_SIZE: int
    CHECK_INTERVAL_HOURS: int
    TIMEZONE: str

    # Add Config class to handle potential extra fields if needed, though usually not necessary for response models
    class Config:
        extra = 'ignore' # Or 'allow' if you expect extra fields sometimes


@router.get("", response_model=ConfigResponse) # Use the specific response model
async def get_config(request: Request):
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning("Unauthorized access attempt to config page")
        return RedirectResponse(url="/", status_code=302)
    return await ConfigService.get_config()


@router.put("", response_model=Dict[str, Any])
async def update_config(config_data: Dict[str, Any], request: Request):
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning("Unauthorized access attempt to config page")
        return RedirectResponse(url="/", status_code=302)
    try:
        return await ConfigService.update_config(config_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset", response_model=Dict[str, Any])
async def reset_config(request: Request):
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning("Unauthorized access attempt to config page")
        return RedirectResponse(url="/", status_code=302)
    try:
        return await ConfigService.reset_config()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
