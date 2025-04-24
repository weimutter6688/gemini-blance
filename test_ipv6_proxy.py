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
    # 尝试通过显式代理访问IPv6测试网站
    print("\n尝试访问 http://6.ipw.cn...")
    response = requests.get(
        "http://6.ipw.cn", 
        proxies=proxies, 
        timeout=10
    )
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text.strip()}")
    
    # 验证返回的是IPv6地址
    ipv6 = response.text.strip()
    if ":" in ipv6:  # 简单检查是否包含冒号，IPv6地址的特征
        print("成功获取IPv6地址，代理测试成功!")
    else:
        print("返回的不是IPv6地址，代理可能未正确工作")
except Exception as e:
    print(f"代理测试失败: {e}")
    sys.exit(1)