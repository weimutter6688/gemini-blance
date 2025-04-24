# app/services/chat/api_client.py

from typing import Dict, Any, AsyncGenerator
import httpx
from abc import ABC, abstractmethod

# 导入日志记录器
from app.log.logger import get_gemini_logger
from app.core.constants import DEFAULT_TIMEOUT

# 初始化日志记录器
logger = get_gemini_logger()

class ApiClient(ABC):
    """API客户端基类"""

    @abstractmethod
    async def generate_content(self, payload: Dict[str, Any], model: str, api_key: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def stream_generate_content(self, payload: Dict[str, Any], model: str, api_key: str) -> AsyncGenerator[str, None]:
        pass


class GeminiApiClient(ApiClient):
    """Gemini API客户端"""

    def __init__(self, base_url: str, timeout: int = DEFAULT_TIMEOUT, proxy_enabled: bool = False, http_proxy: str = None, https_proxy: str = None):
        self.base_url = base_url
        self.timeout = timeout
        self.proxy_enabled = proxy_enabled
        self.http_proxy = http_proxy
        self.https_proxy = https_proxy
        self.transport = None
        self.proxies = None
        
        # 记录不使用代理的地址列表
        self.no_proxy_hosts = [
            "localhost",
            "127.0.0.1",
            "::1",
            ".local",
            "mysql"  # 容器内部服务名
        ]
        
        # 使用 Transport 方式配置代理
        if self.proxy_enabled and (http_proxy or https_proxy):
            # 优先使用 HTTPS 代理，如果没有则使用 HTTP 代理
            proxy_url = https_proxy or http_proxy
            if proxy_url:
                # httpx.AsyncHTTPTransport不支持no_proxy参数
                self.transport = httpx.AsyncHTTPTransport(
                    proxy=proxy_url,  # 直接使用URL字符串
                    verify=False      # 禁用SSL验证
                )
                print(f"\n[代理配置] 已启用代理 (Transport 模式):")
                print(f"  - 代理URL: {proxy_url}")
            
            # 同时保留原有的 proxies 字典方式，作为备选
            self.proxies = {
                "http://": http_proxy,
                "https://": https_proxy
            }
            print(f"  - HTTP代理: {http_proxy}")
            print(f"  - HTTPS代理: {https_proxy}")
            
            # 不再设置环境变量，只在应用级别使用代理
            print(f"  - 使用应用级别代理，不设置环境变量")
        else:
            print("\n[代理配置] 未启用代理")

    def _get_real_model(self, model: str) -> str:
        if model.endswith("-search"):
            model = model[:-7]
        if model.endswith("-image"):
            model = model[:-6]

        return model
        
    def _is_local_url(self, url: str) -> bool:
        """检查URL是否是本地地址，如果是，则不使用代理"""
        from urllib.parse import urlparse
        import re
        
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname or ""
        
        # 检查是否是localhost或127.0.0.1，不考虑端口号
        if hostname == "localhost" or hostname == "127.0.0.1" or hostname == "::1":
            return True
            
        # 检查是否是本地域名
        if hostname.endswith(".local"):
            return True
            
        # 检查是否是容器内部服务名
        if hostname == "mysql":
            return True
            
        # 检查是否是localhost加端口号的形式
        localhost_pattern = re.compile(r'^localhost:\d+$')
        if localhost_pattern.match(parsed_url.netloc):
            return True
            
        # 检查是否是127.0.0.1加端口号的形式
        local_ip_pattern = re.compile(r'^127\.0\.0\.1:\d+$')
        if local_ip_pattern.match(parsed_url.netloc):
            return True
        
        return False

    async def generate_content(self, payload: Dict[str, Any], model: str, api_key: str) -> Dict[str, Any]:
        timeout = httpx.Timeout(self.timeout, read=self.timeout)
        model = self._get_real_model(model)
        url = f"{self.base_url}/models/{model}:generateContent?key={api_key}"

        print(f"\n[发送请求] URL: {self.base_url}/models/{model}:generateContent")
        
        # 检查URL是否是本地地址
        is_local = self._is_local_url(url)
        if is_local:
            logger.debug(f"URL {url} is local, not using proxy")
            # 对本地地址不使用代理
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                verify=False
            ) as client:
                logger.debug(f"Making non-stream request to local URL {url} without proxy.")
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    error_content = response.text
                    raise Exception(f"API call failed with status code {response.status_code}, {error_content}")
                return response.json()
        elif self.transport:
            # 对非本地地址使用代理
            logger.debug(f"Using transport with proxy for non-stream request to {url}")
            async with httpx.AsyncClient(
                transport=self.transport,
                timeout=timeout,
                follow_redirects=True,
                verify=False  # 禁用SSL验证，解决某些代理的证书问题
            ) as client:
                logger.debug(f"Making non-stream request to {url} with transport proxy.")
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    error_content = response.text
                    raise Exception(f"API call failed with status code {response.status_code}, {error_content}")
                return response.json()
        else:
            # 回退到原有的 proxies 字典方式
            logger.debug(f"Using proxies dictionary for non-stream request")
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                proxies=self.proxies,
                verify=False  # 禁用SSL验证，解决某些代理的证书问题
            ) as client:
                logger.debug(f"Making non-stream request to {url} with proxies dictionary.")
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    error_content = response.text
                    raise Exception(f"API call failed with status code {response.status_code}, {error_content}")
                return response.json()

    async def stream_generate_content(self, payload: Dict[str, Any], model: str, api_key: str) -> AsyncGenerator[str, None]:
        # 增加超时时间，特别是读取超时，以处理流式响应
        timeout = httpx.Timeout(self.timeout, read=self.timeout * 2)
        model = self._get_real_model(model)
        url = f"{self.base_url}/models/{model}:streamGenerateContent?alt=sse&key={api_key}"

        print(f"\n[发送请求] URL: {self.base_url}/models/{model}:streamGenerateContent")
        
        # 检查URL是否是本地地址
        is_local = self._is_local_url(url)
        if is_local:
            logger.debug(f"URL {url} is local, not using proxy")
            # 对本地地址不使用代理
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                verify=False
            ) as client:
                logger.debug(f"Making stream request to local URL {url} without proxy.")
                async with client.stream(method="POST", url=url, json=payload) as response:
                    if response.status_code != 200:
                        error_content = await response.aread()
                        error_msg = error_content.decode("utf-8")
                        raise Exception(f"API call failed with status code {response.status_code}, {error_msg}")
                    async for line in response.aiter_lines():
                        yield line
        elif self.transport:
            # 对非本地地址使用代理
            logger.debug(f"Using transport with proxy for stream request to {url}")
            # 尝试直接连接，不使用代理
            try:
                logger.debug(f"Attempting direct connection without proxy for stream request to {url}")
                async with httpx.AsyncClient(
                    timeout=timeout,
                    follow_redirects=True,
                    verify=False
                ) as client:
                    async with client.stream(method="POST", url=url, json=payload) as response:
                        if response.status_code != 200:
                            error_content = await response.aread()
                            error_msg = error_content.decode("utf-8")
                            raise Exception(f"API call failed with status code {response.status_code}, {error_msg}")
                        async for line in response.aiter_lines():
                            yield line
                        return  # 如果直接连接成功，提前返回
            except Exception as e:
                logger.warning(f"Direct connection failed, falling back to proxy: {str(e)}")
                
            # 如果直接连接失败，回退到使用代理
            logger.debug(f"Falling back to proxy for stream request to {url}")
            async with httpx.AsyncClient(
                transport=self.transport,
                timeout=timeout,
                follow_redirects=True,
                verify=False  # 禁用SSL验证，解决某些代理的证书问题
            ) as client:
                logger.debug(f"Making stream request to {url} with transport proxy.")
                async with client.stream(method="POST", url=url, json=payload) as response:
                    if response.status_code != 200:
                        error_content = await response.aread()
                        error_msg = error_content.decode("utf-8")
                        raise Exception(f"API call failed with status code {response.status_code}, {error_msg}")
                    async for line in response.aiter_lines():
                        yield line
        else:
            # 回退到原有的 proxies 字典方式
            logger.debug(f"Using proxies dictionary for stream request")
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                proxies=self.proxies,
                verify=False  # 禁用SSL验证，解决某些代理的证书问题
            ) as client:
                logger.debug(f"Making stream request to {url} with proxies dictionary.")
                async with client.stream(method="POST", url=url, json=payload) as response:
                    if response.status_code != 200:
                        error_content = await response.aread()
                        error_msg = error_content.decode("utf-8")
                        raise Exception(f"API call failed with status code {response.status_code}, {error_msg}")
                    async for line in response.aiter_lines():
                        yield line
