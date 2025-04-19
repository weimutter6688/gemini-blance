"""
代理测试路由模块
"""
import httpx
from fastapi import APIRouter, HTTPException

from app.config.config import settings
from app.log.logger import get_routes_logger # Import an existing logger function

router = APIRouter(prefix="/api/proxy", tags=["proxy"])
logger = get_routes_logger() # Use the imported logger function

@router.get("/test")
async def test_proxy_connection():
    """
    测试当前配置的代理连接是否可用。
    尝试通过代理访问 https://httpbin.org/ip。
    """
    if not settings.PROXY_ENABLED:
        return {"status": "disabled", "message": "代理未启用 (PROXY_ENABLED is false)"}

    http_proxy = settings.HTTP_PROXY
    https_proxy = settings.HTTPS_PROXY

    if not http_proxy and not https_proxy:
        return {"status": "disabled", "message": "代理已启用但未配置代理地址 (HTTP_PROXY/HTTPS_PROXY is not set)"}

    # 优先使用 HTTPS 代理，如果 HTTPS 代理不存在，则使用 HTTP 代理作为 HTTPS 请求的代理
    # httpx 会自动处理 http:// 代理用于 https:// 请求的情况
    proxies = {}
    if https_proxy:
        proxies["https://"] = https_proxy
        logger.info(f"使用 HTTPS 代理进行测试: {https_proxy}")
    elif http_proxy:
        proxies["https://"] = http_proxy # Use HTTP proxy for HTTPS requests if HTTPS_PROXY is not set
        proxies["http://"] = http_proxy
        logger.info(f"未配置 HTTPS 代理，尝试使用 HTTP 代理进行 HTTPS 测试: {http_proxy}")
    
    if not proxies.get("https://"):
         return {"status": "error", "message": "无法确定用于 HTTPS 测试的代理地址"}


    test_url = "https://httpbin.org/ip"
    timeout = httpx.Timeout(10.0, connect=5.0) # 设置超时时间

    # Check if proxy is configured in settings (for reporting purposes)
    proxy_configured = settings.PROXY_ENABLED and (settings.HTTP_PROXY or settings.HTTPS_PROXY)
    proxy_to_report = settings.HTTPS_PROXY or settings.HTTP_PROXY if proxy_configured else None

    try:
        # Rely on httpx picking up os.environ variables set in config.py
        logger.info(f"Proxy configured in settings: {proxy_configured}. Relying on httpx os.environ detection.")
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            logger.info(f"尝试连接到: {test_url}. httpx should use os.environ proxies.")
            response = await client.get(test_url)
            response.raise_for_status() # 如果状态码不是 2xx，则引发异常

            # 尝试解析响应内容
            try:
                data = response.json()
                origin_ip = data.get("origin", "无法解析 IP")
                logger.info(f"通过代理连接成功，响应状态码: {response.status_code}, 来源 IP: {origin_ip}")
                # Report the proxy that *should* have been used based on settings
                return {
                    "status": "success",
                    "message": f"成功连接到 {test_url} (httpx should have used env proxy if set)",
                    "proxy_configured_in_settings": proxy_to_report,
                    "origin_ip_seen_by_target": origin_ip,
                    "status_code": response.status_code
                }
            except Exception as json_e:
                 logger.error(f"通过代理连接成功，但解析响应 JSON 失败: {json_e}")
                 # Report the proxy that *should* have been used based on settings
                 return {
                    "status": "success_parsing_failed",
                    "message": f"成功连接到 {test_url} (状态码: {response.status_code})，但解析响应失败 (httpx should have used env proxy if set)。",
                    "proxy_configured_in_settings": proxy_to_report,
                    "status_code": response.status_code,
                    "raw_response": response.text[:500] # 返回部分原始响应
                 }

    except httpx.TimeoutException as e:
        logger.error(f"通过代理连接超时: {e}")
        raise HTTPException(status_code=504, detail=f"连接代理或目标服务器超时: {e}")
    except httpx.ProxyError as e:
        logger.error(f"代理错误: {e}")
        raise HTTPException(status_code=502, detail=f"代理连接错误: {e}")
    except httpx.RequestError as e:
        logger.error(f"请求错误: {e}")
        raise HTTPException(status_code=500, detail=f"无法通过代理发出请求: {e}")
    except Exception as e:
        logger.error(f"测试代理连接时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail=f"测试代理时发生未知错误: {e}")