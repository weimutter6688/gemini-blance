import httpx
import asyncio
import json
import sys
import os
from dotenv import load_dotenv
import pathlib

# 加载.env文件
current_dir = pathlib.Path(__file__).parent.resolve()
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

async def test_gemini_api():
    # 从.env文件中读取API密钥
    api_keys = []
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('API_KEYS='):
                    api_keys_str = line.strip().split('=', 1)[1]
                    api_keys = json.loads(api_keys_str)
                    break
    except Exception as e:
        print(f"读取API密钥失败: {e}")
        sys.exit(1)

    if not api_keys:
        print("未找到API密钥")
        sys.exit(1)

    api_key = api_keys[0]
    print(f"使用API密钥: {api_key}")

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
        async with httpx.AsyncClient(
            transport=transport,
            timeout=30,
            follow_redirects=True
        ) as client:
            response = await client.post(url, headers=headers, json=payload)
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

if __name__ == "__main__":
    asyncio.run(test_gemini_api())