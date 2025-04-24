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

async def test_proxy():
    # 从.env文件中获取代理配置
    proxy_url = os.environ.get('HTTP_PROXY')
    if not proxy_url:
        print("错误：.env文件中未找到HTTP_PROXY配置")
        sys.exit(1)
    
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
    except Exception as e:
        print(f"应用级别代理测试失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_proxy())