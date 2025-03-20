"""
路由配置模块，负责设置和配置应用程序的路由
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.security import verify_auth_token
from app.log.logger import get_routes_logger
from app.router import gemini_routes, openai_routes
from app.service.key.key_manager import get_key_manager_instance

logger = get_routes_logger()

# 配置Jinja2模板
templates = Jinja2Templates(directory="app/templates")


def setup_routers(app: FastAPI) -> None:
    """
    设置应用程序的路由

    Args:
        app: FastAPI应用程序实例
    """
    # 包含API路由
    app.include_router(openai_routes.router)
    app.include_router(gemini_routes.router)
    app.include_router(gemini_routes.router_v1beta)

    # 添加页面路由
    setup_page_routes(app)

    # 添加健康检查路由
    setup_health_routes(app)


def setup_page_routes(app: FastAPI) -> None:
    """
    设置页面相关的路由

    Args:
        app: FastAPI应用程序实例
    """

    @app.get("/", response_class=HTMLResponse)
    async def auth_page(request: Request):
        """认证页面"""
        return templates.TemplateResponse("auth.html", {"request": request})

    @app.post("/auth")
    async def authenticate(request: Request):
        """处理认证请求"""
        try:
            form = await request.form()
            auth_token = form.get("auth_token")
            if not auth_token:
                logger.warning("Authentication attempt with empty token")
                return RedirectResponse(url="/", status_code=302)

            if verify_auth_token(auth_token):
                logger.info("Successful authentication")
                response = RedirectResponse(url="/keys", status_code=302)
                response.set_cookie(
                    key="auth_token", value=auth_token, httponly=True, max_age=3600
                )
                return response
            logger.warning("Failed authentication attempt with invalid token")
            return RedirectResponse(url="/", status_code=302)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return RedirectResponse(url="/", status_code=302)

    @app.get("/keys", response_class=HTMLResponse)
    async def keys_page(request: Request):
        """密钥管理页面"""
        try:
            auth_token = request.cookies.get("auth_token")
            if not auth_token or not verify_auth_token(auth_token):
                logger.warning("Unauthorized access attempt to keys page")
                return RedirectResponse(url="/", status_code=302)

            key_manager = await get_key_manager_instance()
            keys_status = await key_manager.get_keys_by_status()
            total = len(keys_status["valid_keys"]) + len(keys_status["invalid_keys"])
            logger.info(f"Keys status retrieved successfully. Total keys: {total}")
            return templates.TemplateResponse(
                "keys_status.html",
                {
                    "request": request,
                    "valid_keys": keys_status["valid_keys"],
                    "invalid_keys": keys_status["invalid_keys"],
                    "total": total,
                },
            )
        except Exception as e:
            logger.error(f"Error retrieving keys status: {str(e)}")
            raise


def setup_health_routes(app: FastAPI) -> None:
    """
    设置健康检查相关的路由

    Args:
        app: FastAPI应用程序实例
    """

    @app.get("/health")
    async def health_check(request: Request):
        """健康检查端点"""
        logger.info("Health check endpoint called")
        return {"status": "healthy"}
