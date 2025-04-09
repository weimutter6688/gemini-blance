"""
日志路由模块
"""
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse

from app.core.security import verify_auth_token
from app.log.logger import get_log_routes_logger
from app.database.services import get_error_logs

# 创建路由
router = APIRouter(prefix="/api/logs", tags=["logs"])

logger = get_log_routes_logger()


@router.get("/errors", response_model=List[Dict[str, Any]])
async def get_error_logs_api(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    获取错误日志
    
    Args:
        request: 请求对象
        limit: 限制数量
        offset: 偏移量
    
    Returns:
        List[Dict[str, Any]]: 错误日志列表
    """
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning("Unauthorized access attempt to error logs")
        return RedirectResponse(url="/", status_code=302)
    
    try:
        logs = await get_error_logs(limit, offset)
        return logs
    except Exception as e:
        logger.error(f"Failed to get error logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get error logs: {str(e)}")
