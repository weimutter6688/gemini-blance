# app/service/stats_service.py

import datetime
from sqlalchemy import select, func

from app.database.connection import database
from app.database.models import RequestLog
from app.log.logger import get_stats_logger

logger = get_stats_logger()

async def get_calls_in_last_seconds(seconds: int) -> int:
    """获取过去 N 秒内的调用次数 (包括成功和失败)"""
    try:
        cutoff_time = datetime.datetime.now() - datetime.timedelta(seconds=seconds)
        query = select(func.count(RequestLog.id)).where(
            RequestLog.request_time >= cutoff_time
        )
        count_result = await database.fetch_one(query)
        return count_result[0] if count_result else 0
    except Exception as e:
        logger.error(f"Failed to get calls in last {seconds} seconds: {e}")
        return 0 # Return 0 on error

async def get_calls_in_last_minutes(minutes: int) -> int:
    """获取过去 N 分钟内的调用次数 (包括成功和失败)"""
    return await get_calls_in_last_seconds(minutes * 60)

async def get_calls_in_last_hours(hours: int) -> int:
    """获取过去 N 小时内的调用次数 (包括成功和失败)"""
    return await get_calls_in_last_seconds(hours * 3600)

async def get_calls_in_current_month() -> int:
    """获取当前自然月内的调用次数 (包括成功和失败)"""
    try:
        now = datetime.datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = select(func.count(RequestLog.id)).where(
            RequestLog.request_time >= start_of_month
        )
        count_result = await database.fetch_one(query)
        return count_result[0] if count_result else 0
    except Exception as e:
        logger.error(f"Failed to get calls in current month: {e}")
        return 0 # Return 0 on error

async def get_api_usage_stats() -> dict:
    """获取所有需要的 API 使用统计数据"""
    try:
        calls_1m = await get_calls_in_last_minutes(1)
        calls_1h = await get_calls_in_last_hours(1)
        calls_24h = await get_calls_in_last_hours(24)
        calls_month = await get_calls_in_current_month()

        return {
            "calls_1m": calls_1m,
            "calls_1h": calls_1h,
            "calls_24h": calls_24h,
            "calls_month": calls_month,
        }
    except Exception as e:
        logger.error(f"Failed to get API usage stats: {e}")
        # Return default values on error
        return {
            "calls_1m": 0,
            "calls_1h": 0,
            "calls_24h": 0,
            "calls_month": 0,
        }


async def get_api_call_details(period: str) -> list[dict]:
    """
    获取指定时间段内的 API 调用详情

    Args:
        period: 时间段标识 ('1m', '1h', '24h')

    Returns:
        包含调用详情的字典列表，每个字典包含 timestamp, key, model, status

    Raises:
        ValueError: 如果 period 无效
    """
    now = datetime.datetime.now()
    if period == '1m':
        start_time = now - datetime.timedelta(minutes=1)
    elif period == '1h':
        start_time = now - datetime.timedelta(hours=1)
    elif period == '24h':
        start_time = now - datetime.timedelta(hours=24)
    else:
        raise ValueError(f"无效的时间段标识: {period}")

    try:
        query = select(
            RequestLog.request_time.label("timestamp"),
            RequestLog.api_key.label("key"),
            RequestLog.model_name.label("model"),
            RequestLog.status_code # We might need to map this to 'success'/'failure' later
        ).where(
            RequestLog.request_time >= start_time
        ).order_by(RequestLog.request_time.desc()) # Order by most recent first

        results = await database.fetch_all(query)

        # Convert results to list of dicts and map status_code
        details = []
        for row in results:
            status = 'success' if 200 <= row['status_code'] < 300 else 'failure'
            details.append({
                "timestamp": row['timestamp'].isoformat(), # Use ISO format for JS compatibility
                "key": row['key'],
                "model": row['model'],
                "status": status
            })
        logger.info(f"Retrieved {len(details)} API call details for period '{period}'")
        return details

    except Exception as e:
        logger.error(f"Failed to get API call details for period '{period}': {e}")
        # Re-raise the exception to be handled by the route
        raise