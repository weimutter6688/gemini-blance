import os
import requests
import json
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

# 从.env文件中读取API密钥
api_keys_str = os.environ.get('API_KEYS')
if not api_keys_str:
    print("错误：.env文件中未找到API_KEYS配置")
    sys.exit(1)

try:
    api_keys = json.loads(api_keys_str)
    if not api_keys:
        print("API_KEYS数组为空")
        sys.exit(1)
    
    api_key = api_keys[0]
except Exception as e:
    print(f"解析API密钥失败: {e}")
    sys.exit(1)
print(f"使用API密钥: {api_key}")

# 构建请求
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
headers = {
    "Content-Type": "application/json"
}
payload = {
    "contents": [
        {
            "role": "user",
            "parts": [{"text": "hi"}]
        }
    ]
}

try:
    # 尝试通过代理访问Gemini API
    print(f"\n尝试访问Gemini API: {url}")
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("Gemini API测试成功!")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)[:200]}...")
    else:
        print(f"Gemini API测试失败: {response.text}")
        sys.exit(1)
except Exception as e:
    print(f"Gemini API测试失败: {e}")
    sys.exit(1)