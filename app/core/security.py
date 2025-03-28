from typing import Optional

from fastapi import Header, HTTPException

from app.config.config import settings
from app.log.logger import get_security_logger

logger = get_security_logger()


def verify_auth_token(token: str) -> bool:
    return token == settings.AUTH_TOKEN


class SecurityService:
    def __init__(self, allowed_tokens: list, auth_token: str):
        self.allowed_tokens = allowed_tokens
        self.auth_token = auth_token

    async def verify_key(self, key: str):
        if key not in self.allowed_tokens and key != self.auth_token:
            logger.error("Invalid key")
            raise HTTPException(status_code=401, detail="Invalid key")
        return key

    async def verify_authorization(
        self, authorization: Optional[str] = Header(None)
    ) -> str:
        if not authorization:
            logger.error("Missing Authorization header")
            raise HTTPException(status_code=401, detail="Missing Authorization header")

        if not authorization.startswith("Bearer "):
            logger.error("Invalid Authorization header format")
            raise HTTPException(
                status_code=401, detail="Invalid Authorization header format"
            )

        token = authorization.replace("Bearer ", "")
        if token not in self.allowed_tokens and token != self.auth_token:
            logger.error("Invalid token")
            raise HTTPException(status_code=401, detail="Invalid token")

        return token

    async def verify_goog_api_key(
        self, x_goog_api_key: Optional[str] = Header(None)
    ) -> str:
        """验证Google API Key"""
        if not x_goog_api_key:
            logger.error("Missing x-goog-api-key header")
            raise HTTPException(status_code=401, detail="Missing x-goog-api-key header")

        if (
            x_goog_api_key not in self.allowed_tokens
            and x_goog_api_key != self.auth_token
        ):
            logger.error("Invalid x-goog-api-key")
            raise HTTPException(status_code=401, detail="Invalid x-goog-api-key")

        return x_goog_api_key

    async def verify_auth_token(
        self, authorization: Optional[str] = Header(None)
    ) -> str:
        if not authorization:
            logger.error("Missing auth_token header")
            raise HTTPException(status_code=401, detail="Missing auth_token header")
        token = authorization.replace("Bearer ", "")
        if token != self.auth_token:
            logger.error("Invalid auth_token")
            raise HTTPException(status_code=401, detail="Invalid auth_token")

        return token

    async def verify_key_or_goog_api_key(
        self, key: Optional[str] = None , x_goog_api_key: Optional[str] = Header(None)
    ) -> str:
        """验证URL中的key或请求头中的x-goog-api-key"""
        # 如果URL中的key有效，直接返回
        if key in self.allowed_tokens or key == self.auth_token:
            return key
        
        # 否则检查请求头中的x-goog-api-key
        if not x_goog_api_key:
            logger.error("Invalid key and missing x-goog-api-key header")
            raise HTTPException(status_code=401, detail="Invalid key and missing x-goog-api-key header")
        
        if x_goog_api_key not in self.allowed_tokens and x_goog_api_key != self.auth_token:
            logger.error("Invalid key and invalid x-goog-api-key")
            raise HTTPException(status_code=401, detail="Invalid key and invalid x-goog-api-key")
        
        return x_goog_api_key