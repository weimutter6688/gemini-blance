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
        
        # 使用 Transport 方式配置代理
        if self.proxy_enabled and (http_proxy or https_proxy):
            # 优先使用 HTTPS 代理，如果没有则使用 HTTP 代理
            proxy_url = https_proxy or http_proxy
            if proxy_url:
                self.transport = httpx.AsyncHTTPTransport(
                    proxy=proxy_url,  # 直接使用URL字符串
                    verify=False,     # 禁用SSL验证
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
            
            # 确保环境变量中也设置了代理，这对某些底层库很重要
            import os
            if http_proxy:
                os.environ['HTTP_PROXY'] = http_proxy
                print(f"  - 设置环境变量 HTTP_PROXY: {http_proxy}")
            if https_proxy:
                os.environ['HTTPS_PROXY'] = https_proxy
                print(f"  - 设置环境变量 HTTPS_PROXY: {https_proxy}")
        else:
            print("\n[代理配置] 未启用代理")

    def _get_real_model(self, model: str) -> str:
        if model.endswith("-search"):
            model = model[:-7]
        if model.endswith("-image"):
            model = model[:-6]

        return model

    async def generate_content(self, payload: Dict[str, Any], model: str, api_key: str) -> Dict[str, Any]:
        timeout = httpx.Timeout(self.timeout, read=self.timeout)
        model = self._get_real_model(model)

        print(f"\n[发送请求] URL: {self.base_url}/models/{model}:generateContent")
        # 移除容易混淆的代理打印语句，因为代理在下面设置
        # if self.proxy_enabled and self.proxies:
        #     print(f"[发送请求] 使用代理: {self.proxies.get('https://', self.proxies.get('http://', '未设置'))}")

        # 使用配置的 transport 或 proxies
        if self.transport:
            logger.debug(f"Using transport with proxy for non-stream request")
            async with httpx.AsyncClient(
                transport=self.transport,
                timeout=timeout,
                follow_redirects=True,
                verify=False  # 禁用SSL验证，解决某些代理的证书问题
            ) as client:
                url = f"{self.base_url}/models/{model}:generateContent?key={api_key}"
                logger.debug(f"Making non-stream request to {url} with transport proxy.")
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    error_content = response.text
                    raise Exception(f"API call failed with status code {response.status_code}, {error_content}")
                return response.json()
        else:
            # 回退到原有的 proxies 方式或环境变量
            logger.debug(f"Using proxies dictionary or os.environ for non-stream request")
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                proxies=self.proxies,
                verify=False  # 禁用SSL验证，解决某些代理的证书问题
            ) as client:
                url = f"{self.base_url}/models/{model}:generateContent?key={api_key}"
                logger.debug(f"Making non-stream request to {url}. httpx should use proxies or os.environ.")
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    error_content = response.text
                    raise Exception(f"API call failed with status code {response.status_code}, {error_content}")
                return response.json()

    async def stream_generate_content(self, payload: Dict[str, Any], model: str, api_key: str) -> AsyncGenerator[str, None]:
        timeout = httpx.Timeout(self.timeout, read=self.timeout)
        model = self._get_real_model(model)

        print(f"\n[发送请求] URL: {self.base_url}/models/{model}:streamGenerateContent")
        # 移除容易混淆的代理打印语句，因为代理在下面设置
        # if self.proxy_enabled and self.proxies:
        #     print(f"[发送请求] 使用代理: {self.proxies.get('https://', self.proxies.get('http://', '未设置'))}")

        # 使用配置的 transport 或 proxies
        if self.transport:
            logger.debug(f"Using transport with proxy for stream request")
            async with httpx.AsyncClient(
                transport=self.transport,
                timeout=timeout,
                follow_redirects=True,
                verify=False  # 禁用SSL验证，解决某些代理的证书问题
            ) as client:
                url = f"{self.base_url}/models/{model}:streamGenerateContent?alt=sse&key={api_key}"
                logger.debug(f"Making stream request to {url} with transport proxy.")
                async with client.stream(method="POST", url=url, json=payload) as response:
                    if response.status_code != 200:
                        error_content = await response.aread()
                        error_msg = error_content.decode("utf-8")
                        raise Exception(f"API call failed with status code {response.status_code}, {error_msg}")
                    async for line in response.aiter_lines():
                        yield line
        else:
            # 回退到原有的 proxies 方式或环境变量
            logger.debug(f"Using proxies dictionary or os.environ for stream request")
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                proxies=self.proxies,
                verify=False  # 禁用SSL验证，解决某些代理的证书问题
            ) as client:
                url = f"{self.base_url}/models/{model}:streamGenerateContent?alt=sse&key={api_key}"
                logger.debug(f"Making stream request to {url}. httpx should use proxies or os.environ.")
                async with client.stream(method="POST", url=url, json=payload) as response:
                    if response.status_code != 200:
                        error_content = await response.aread()
                        error_msg = error_content.decode("utf-8")
                        raise Exception(f"API call failed with status code {response.status_code}, {error_msg}")
                    async for line in response.aiter_lines():
                        yield line
