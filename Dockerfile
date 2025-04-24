FROM python:3.10-slim

WORKDIR /app

# 设置构建时代理参数
ARG HTTP_PROXY

# 如果提供了代理参数，则设置环境变量用于构建过程
ENV HTTP_PROXY=${HTTP_PROXY}
ENV NO_PROXY=localhost,127.0.0.1,::1,.local,mysql

# 复制依赖文件
COPY ./requirements.txt /app

# 使用国内镜像源安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码
COPY ./app /app/app

# 复制测试脚本
COPY ./test_proxy_in_container.py /app/

# 确保files目录存在
RUN mkdir -p /app/files

# 设置默认环境变量
ENV API_KEYS='["your_api_key_1"]'
ENV ALLOWED_TOKENS='["your_token_1"]'
ENV BASE_URL=https://generativelanguage.googleapis.com/v1beta
ENV TOOLS_CODE_EXECUTION_ENABLED=false
ENV IMAGE_MODELS='["gemini-2.0-flash-exp"]'
ENV SEARCH_MODELS='["gemini-2.0-flash-exp","gemini-2.0-pro-exp"]'

# 代理相关环境变量 - 这些会被.env文件或docker-compose中的环境变量覆盖
ENV PROXY_ENABLED=false

# 暴露端口
EXPOSE 8000

# 运行应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
