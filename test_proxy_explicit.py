import requests
import sys
import os
from dotenv import load_dotenv
import pathlib

# 加载.env文件
current_dir = pathlib.Path(__file__).parent.resolve()
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

# 从.env文件中获取代理配置
proxy_url = os.environ.get('HTTP_PROXY')
if not proxy_url:
    print("错误：.env文件中未找到HTTP_PROXY配置")
    sys.exit(1)

# 显式指定代理配置
proxies = {
    "http": proxy_url,
    "https": proxy_url
}

print(f"使用显式代理配置: {proxies}")

try:
    # 尝试通过显式代理访问一个HTTPS网站
    print("\n尝试访问 https://httpbin.org/ip...")
    response = requests.get(
        "https://httpbin.org/ip", 
        proxies=proxies, 
        timeout=10,
        verify=False  # 禁用SSL验证，解决某些代理的证书问题
    )
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    print("代理测试成功!")
except Exception as e:
    print(f"代理测试失败: {e}")
    sys.exit(1)