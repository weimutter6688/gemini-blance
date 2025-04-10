"""
日志路由模块
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse

from app.core.security import verify_auth_token
from app.log.logger import get_log_routes_logger
from app.database.services import get_error_logs, get_error_logs_count

# 创建路由
router = APIRouter(prefix="/api/logs", tags=["logs"])

logger = get_log_routes_logger()


# Define a response model that includes the total count for pagination
class ErrorLogResponse(BaseModel):
    logs: List[Dict[str, Any]]
    total: int

@router.get("/errors", response_model=ErrorLogResponse)
async def get_error_logs_api(
    request: Request,
    limit: int = Query(20, ge=1, le=1000), # Default to 20 to match frontend
    offset: int = Query(0, ge=0),
    key_search: Optional[str] = Query(None, description="Search term for Gemini key (partial match)"),
    error_search: Optional[str] = Query(None, description="Search term for error type or log message"),
    start_date: Optional[datetime] = Query(None, description="Start datetime for filtering (YYYY-MM-DDTHH:MM)"),
    end_date: Optional[datetime] = Query(None, description="End datetime for filtering (YYYY-MM-DDTHH:MM)")
):
    """
    获取错误日志
    
    Args:
        request: 请求对象
        limit: 限制数量
        offset: 偏移量
    
    Returns:
        ErrorLogResponse: An object containing the list of logs and the total count.
    """
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning("Unauthorized access attempt to error logs")
        return RedirectResponse(url="/", status_code=302)
    
    try:
        # Fetch logs with search parameters
        logs = await get_error_logs(
            limit=limit,
            offset=offset,
            key_search=key_search,
            error_search=error_search,
            start_date=start_date,
            end_date=end_date
        )
        # Fetch total count with the same search parameters
        total_count = await get_error_logs_count(
            key_search=key_search,
            error_search=error_search,
            start_date=start_date,
            end_date=end_date
        )
        return ErrorLogResponse(logs=logs, total=total_count)
    except Exception as e:
        logger.exception(f"Failed to get error logs: {str(e)}") # Use logger.exception for stack trace
        raise HTTPException(status_code=500, detail=f"Failed to get error logs: {str(e)}")
