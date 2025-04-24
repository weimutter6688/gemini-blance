import httpx
import asyncio
import sys
import os
from dotenv import load_dotenv
import pathlib

# 加载.env文件
current_dir = pathlib.Path(__file__).parent.resolve()
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

# 打印环境变量
print("\n===== 容器环境变量 =====")
print(f"PROXY_ENABLED: {os.environ.get('PROXY_ENABLED')}")
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")
print(f"CONTAINER_HTTP_PROXY: {os.environ.get('CONTAINER_HTTP_PROXY')}")
print("========================\n")

async def test_proxy():
    # 从.env文件中获取代理配置，而不是硬编码
    proxy_url = os.environ.get('HTTP_PROXY')
    if not proxy_url:
        print("错误：.env文件中未找到HTTP_PROXY配置")
        return
    
    print(f"注意：这里使用的是从.env文件中获取的代理配置: {proxy_url}")
    
    # 创建与应用程序类似的transport配置
    transport = httpx.AsyncHTTPTransport(
        proxy=proxy_url,
        verify=False  # 禁用SSL验证，解决某些代理的证书问题
    )
    
    print(f"使用应用级别代理配置: {proxy_url}")
    
    try:
        # 尝试通过代理访问IPv6测试网站
        print("\n尝试访问 http://6.ipw.cn...")
        async with httpx.AsyncClient(
            transport=transport,
            timeout=10,
            follow_redirects=True
        ) as client:
            response = await client.get("http://6.ipw.cn")
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text.strip()}")
            
            # 验证返回的是IPv6地址
            ipv6 = response.text.strip()
            if ":" in ipv6:  # 简单检查是否包含冒号，IPv6地址的特征
                print("成功获取IPv6地址，应用级别代理测试成功!")
            else:
                print("返回的不是IPv6地址，应用级别代理可能未正确工作")
                
        # 尝试通过代理访问Gemini API
        print("\n尝试访问 https://generativelanguage.googleapis.com/v1beta/models...")
        async with httpx.AsyncClient(
            transport=transport,
            timeout=10,
            follow_redirects=True
        ) as client:
            response = await client.get("https://generativelanguage.googleapis.com/v1beta/models")
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")
            print("成功访问Gemini API，应用级别代理测试成功!")
    except Exception as e:
        print(f"应用级别代理测试失败: {e}")
        sys.exit(1)

async def test_proxy_with_env():
    """使用环境变量中的代理配置进行测试"""
    # 从环境变量获取代理配置
    proxy_enabled = os.environ.get('PROXY_ENABLED', 'false').lower() == 'true'
    http_proxy = os.environ.get('HTTP_PROXY')
    
    if not proxy_enabled:
        print("\n环境变量中的代理未启用 (PROXY_ENABLED=false)")
        return
    
    if not http_proxy:
        print("\n环境变量中的HTTP_PROXY未设置")
        return
    
    print(f"\n===== 使用环境变量中的代理配置进行测试 =====")
    print(f"代理URL: {http_proxy}")
    
    # 创建transport配置
    transport = httpx.AsyncHTTPTransport(
        proxy=http_proxy,
        verify=False  # 禁用SSL验证，解决某些代理的证书问题
    )
    
    try:
        # 尝试通过代理访问IPv6测试网站
        print("\n尝试访问 http://6.ipw.cn...")
        async with httpx.AsyncClient(
            transport=transport,
            timeout=10,
            follow_redirects=True
        ) as client:
            response = await client.get("http://6.ipw.cn")
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text.strip()}")
            
            # 验证返回的是IPv6地址
            ipv6 = response.text.strip()
            if ":" in ipv6:  # 简单检查是否包含冒号，IPv6地址的特征
                print("成功获取IPv6地址，环境变量代理测试成功!")
            else:
                print("返回的不是IPv6地址，环境变量代理可能未正确工作")
    except Exception as e:
        print(f"环境变量代理测试失败: {e}")

async def test_proxy_like_app():
    """使用与应用程序完全相同的方式创建和使用代理配置"""
    print(f"\n===== 使用与应用程序相同的方式进行测试 =====")
    
    # 模拟应用程序中的代理配置初始化
    proxy_enabled = os.environ.get('PROXY_ENABLED', 'false').lower() == 'true'
    http_proxy = os.environ.get('HTTP_PROXY')
    https_proxy = os.environ.get('HTTPS_PROXY')
    
    print(f"代理启用状态: {proxy_enabled}")
    print(f"HTTP代理: {http_proxy}")
    print(f"HTTPS代理: {https_proxy}")
    
    transport = None
    proxies = None
    
    # 使用与应用程序相同的逻辑创建transport
    if proxy_enabled and (http_proxy or https_proxy):
        # 优先使用 HTTPS 代理，如果没有则使用 HTTP 代理
        proxy_url = https_proxy or http_proxy
        if proxy_url:
            transport = httpx.AsyncHTTPTransport(
                proxy=proxy_url,  # 直接使用URL字符串
                verify=False,     # 禁用SSL验证
            )
            print(f"创建了transport，使用代理: {proxy_url}")
        
        # 同时保留原有的 proxies 字典方式，作为备选
        proxies = {
            "http://": http_proxy,
            "https://": https_proxy
        }
        print(f"创建了proxies字典: {proxies}")
    else:
        print("代理未启用或未配置")
        return
    
    try:
        # 尝试通过代理访问IPv6测试网站
        print("\n尝试访问 http://6.ipw.cn...")
        async with httpx.AsyncClient(
            transport=transport,
            timeout=10,
            follow_redirects=True,
            verify=False
        ) as client:
            response = await client.get("http://6.ipw.cn")
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text.strip()}")
            
            # 验证返回的是IPv6地址
            ipv6 = response.text.strip()
            if ":" in ipv6:  # 简单检查是否包含冒号，IPv6地址的特征
                print("成功获取IPv6地址，应用程序方式代理测试成功!")
            else:
                print("返回的不是IPv6地址，应用程序方式代理可能未正确工作")
                
        # 尝试通过代理访问Gemini API
        print("\n尝试访问 https://generativelanguage.googleapis.com/v1beta/models...")
        async with httpx.AsyncClient(
            transport=transport,
            timeout=10,
            follow_redirects=True,
            verify=False
        ) as client:
            response = await client.get("https://generativelanguage.googleapis.com/v1beta/models")
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")
            print("成功访问Gemini API，应用程序方式代理测试成功!")
    except Exception as e:
        print(f"应用程序方式代理测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_proxy())
    # 测试使用环境变量中的代理配置
    asyncio.run(test_proxy_with_env())
    # 测试使用与应用程序完全相同的方式
    asyncio.run(test_proxy_like_app())