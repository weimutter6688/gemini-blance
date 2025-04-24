import os
import requests
import sys
from dotenv import load_dotenv

# 重新加载.env文件
print("重新加载.env文件...")
load_dotenv(override=True)

# 打印当前环境变量中的代理设置
print(f"Current HTTP_PROXY: {os.environ.get('HTTP_PROXY')}")
print(f"Current HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")

try:
    # 尝试使用环境变量中的代理访问IPv6测试网站
    print("\n尝试使用环境变量代理访问 http://6.ipw.cn...")
    response = requests.get("http://6.ipw.cn", timeout=10)
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
    
    # 如果环境变量代理测试失败，尝试使用显式代理
    try:
        print("\n尝试使用显式代理配置...")
        # 从.env文件中获取代理配置
        proxy_url = os.environ.get('HTTP_PROXY')
        if not proxy_url:
            print("错误：.env文件中未找到HTTP_PROXY配置")
            sys.exit(1)
            
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        print(f"使用显式代理配置: {proxies}")
        
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
            print("成功获取IPv6地址，显式代理测试成功!")
        else:
            print("返回的不是IPv6地址，显式代理可能未正确工作")
    except Exception as e2:
        print(f"显式代理测试也失败: {e2}")
        sys.exit(1)