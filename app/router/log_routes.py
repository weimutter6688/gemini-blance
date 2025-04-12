"""
日志路由模块
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request, Query, Path

from app.core.security import verify_auth_token
from app.log.logger import get_log_routes_logger
# 假设这些服务函数已更新或添加
from app.database.services import get_error_logs, get_error_logs_count, get_error_log_details

# 创建路由
router = APIRouter(prefix="/api/logs", tags=["logs"])

logger = get_log_routes_logger()


# Define a response model that includes the total count for pagination
# 用于列表响应的模型，假设 get_error_logs 返回包含 error_code 的字典
class ErrorLogListItem(BaseModel):
    id: int
    gemini_key: Optional[str] = None
    error_type: Optional[str] = None
    error_code: Optional[int] = None # 列表显示错误码 (应为整数)
    model_name: Optional[str] = None
    request_time: Optional[datetime] = None

class ErrorLogListResponse(BaseModel):
    logs: List[ErrorLogListItem] # 使用定义的模型列表
    total: int

@router.get("/errors", response_model=ErrorLogListResponse)
async def get_error_logs_api(
    request: Request,
    limit: int = Query(10, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    key_search: Optional[str] = Query(None, description="Search term for Gemini key (partial match)"),
    error_search: Optional[str] = Query(None, description="Search term for error type or log message"), # 数据库查询需处理
    start_date: Optional[datetime] = Query(None, description="Start datetime for filtering"),
    end_date: Optional[datetime] = Query(None, description="End datetime for filtering")
):
    """
    获取错误日志列表 (返回错误码)

    Args:
        request: 请求对象
        limit: 限制数量
        offset: 偏移量
        key_search: 密钥搜索
        error_search: 错误搜索 (可能搜索类型或日志内容，由DB层决定)
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        ErrorLogListResponse: An object containing the list of logs (with error_code) and the total count.
    """
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning("Unauthorized access attempt to error logs list")
        # API 返回 401 更合适
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # 假设 get_error_logs 现在返回包含 error_code 的字典列表
        # 并且可以接受 include_error_code 参数 (如果需要显式指定)
        logs_data = await get_error_logs(
            limit=limit,
            offset=offset,
            key_search=key_search,
            error_search=error_search, # 数据库查询需要处理这个
            start_date=start_date,
            end_date=end_date,
            # include_error_code=True # 如果需要显式传递
        )
        # Fetch total count with the same search parameters
        total_count = await get_error_logs_count(
            key_search=key_search,
            error_search=error_search,
            start_date=start_date,
            end_date=end_date
        )
        # 验证并转换数据以匹配 Pydantic 模型
        validated_logs = [ErrorLogListItem(**log) for log in logs_data]
        return ErrorLogListResponse(logs=validated_logs, total=total_count)
    except Exception as e:
        logger.exception(f"Failed to get error logs list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get error logs list: {str(e)}")


# 新增：获取错误日志详情的路由
class ErrorLogDetailResponse(BaseModel):
    id: int
    gemini_key: Optional[str] = None
    error_type: Optional[str] = None
    error_log: Optional[str] = None # 详情接口返回完整的 error_log
    request_msg: Optional[str] = None # 详情接口返回 request_msg
    model_name: Optional[str] = None
    request_time: Optional[datetime] = None

@router.get("/errors/{log_id}/details", response_model=ErrorLogDetailResponse)
async def get_error_log_detail_api(request: Request, log_id: int = Path(..., ge=1)):
    """
    根据日志 ID 获取错误日志的详细信息 (包括 error_log 和 request_msg)
    """
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning(f"Unauthorized access attempt to error log details for ID: {log_id}")
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # 假设存在一个函数 get_error_log_details(log_id) 来获取完整信息
        log_details = await get_error_log_details(log_id=log_id)
        if not log_details:
            raise HTTPException(status_code=404, detail="Error log not found")

        # 假设 get_error_log_details 返回一个字典或兼容 Pydantic 的对象
        return ErrorLogDetailResponse(**log_details)
    except HTTPException as http_exc:
        # Re-raise HTTPException (like 404)
        raise http_exc
    except Exception as e:
        logger.exception(f"Failed to get error log details for ID {log_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get error log details: {str(e)}")
