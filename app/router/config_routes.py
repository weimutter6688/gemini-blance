"""
配置路由模块
"""
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core.security import verify_auth_token
from app.log.logger import get_config_routes_logger
from app.service.config.config_service import ConfigService

# 创建路由
router = APIRouter(prefix="/api/config", tags=["config"])

logger = get_config_routes_logger()


@router.get("", response_model=Dict[str, Any])
async def get_config(request: Request):
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning("Unauthorized access attempt to config page")
        return RedirectResponse(url="/", status_code=302)
    return ConfigService.get_config()


@router.put("", response_model=Dict[str, Any])
async def update_config(config_data: Dict[str, Any], request: Request):
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning("Unauthorized access attempt to config page")
        return RedirectResponse(url="/", status_code=302)
    try:
        return ConfigService.update_config(config_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset", response_model=Dict[str, Any])
async def reset_config(request: Request):
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning("Unauthorized access attempt to config page")
        return RedirectResponse(url="/", status_code=302)
    try:
        return ConfigService.reset_config()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
