import json

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.log.logger import get_request_logger

logger = get_request_logger()


# 添加中间件类
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 记录请求路径
        logger.info(f"Request path: {request.url.path}")

        # 获取并记录请求体
        try:
            body = await request.body()
            if body:
                body_str = body.decode()
                # 尝试格式化JSON
                try:
                    formatted_body = json.loads(body_str)
                    logger.info(
                        f"Formatted request body:\n{json.dumps(formatted_body, indent=2, ensure_ascii=False)}"
                    )
                except json.JSONDecodeError:
                    logger.info("Request body is not valid JSON.")
        except Exception as e:
            logger.error(f"Error reading request body: {str(e)}")

        # 重置请求的接收器，以便后续处理器可以继续读取请求体
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request._receive = receive

        response = await call_next(request)
        return response
