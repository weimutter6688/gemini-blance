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