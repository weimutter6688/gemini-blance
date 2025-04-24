import os
import requests
import sys
from dotenv import load_dotenv
import pathlib

# 加载.env文件
current_dir = pathlib.Path(__file__).parent.resolve()
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

# 打印当前环境变量中的代理设置
print(f"Current HTTP_PROXY: {os.environ.get('HTTP_PROXY')}")
print(f"Current HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")

try:
    # 尝试通过代理访问一个HTTPS网站
    print("\n尝试访问 https://httpbin.org/ip...")
    response = requests.get("https://httpbin.org/ip", timeout=10)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    print("代理测试成功!")
except Exception as e:
    print(f"代理测试失败: {e}")
    sys.exit(1)