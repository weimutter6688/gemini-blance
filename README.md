# 🚀 Gemini 代理服务（支持openai/gemini格式）

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📝 项目简介

本项目是一个基于 FastAPI 框架开发的高性能、易于部署的Gemini OpenAI兼容 和 Gemini API 代理服务。它不仅兼容 OpenAI 的 API 接口，还支持 Google 的 Gemini 原生接口。该代理服务内置了多 API Key 轮询、负载均衡、自动重试、访问控制（Bearer Token 认证）、流式响应等功能，旨在简化 AI 应用的开发和部署流程。

**核心功能与优势:**

- **多协议支持**: 无缝切换 OpenAI兼容 和 Gemini 协议。
- **智能 API Key 管理**: 自动轮询多个 API Key，实现负载均衡和故障转移。
- **安全访问控制**: 使用 Bearer Token 进行身份验证，保护 API 访问。
- **流式响应支持**: 提供实时的流式数据传输，提升用户体验。
- **内置工具支持**: 支持代码执行和 Google 搜索等工具, 丰富模型功能 (可选)。
- **灵活配置**: 通过环境变量或 `.env` 文件轻松配置。
- **易于部署**: 提供 Docker 一键部署，也支持手动部署。
- **健康检查**: 提供健康检查接口，方便监控服务状态。
- **图片生成支持**: 支持使用OpenAI的DALL-E模型生成图片

## 🛠️ 技术栈

- **FastAPI**: 高性能 Web 框架。
- **Python 3.9+**: 编程语言。
- **Pydantic**: 数据验证和设置管理。
- **httpx**: 异步 HTTP 客户端。
- **uvicorn**: ASGI 服务器。
- **Docker**: 容器化部署 (可选)。

## 🚀 快速开始

### 环境要求

- Python 3.9 或更高版本
- Docker (可选，推荐用于生产环境)

### 📦 安装与配置

1. **克隆项目**:

    ```bash
    git clone https://github.com/snailyp/gemini-balance.git
    cd gemini-balance
    ```

2. **安装依赖**:

    ```bash
    pip install -r requirements.txt
    ```

3. **配置**:

    创建 `.env` 文件，并按以下分类配置环境变量：

    ```env
    # 基础配置
    BASE_URL="https://generativelanguage.googleapis.com/v1beta"  # Gemini API 基础 URL，默认无需修改
    MAX_FAILURES=3  # 允许单个key失败的次数，默认3次
    TIME_OUT=300    # 请求超时时间，默认300s

    # 认证与安全配置
    API_KEYS=["your-gemini-api-key-1", "your-gemini-api-key-2"]  # Gemini API 密钥列表，用于负载均衡
    ALLOWED_TOKENS=["your-access-token-1", "your-access-token-2"]  # 允许访问的 Token 列表
    AUTH_TOKEN=""  # 超级管理员token，具有所有权限，默认使用 ALLOWED_TOKENS 的第一个

    # 模型功能配置
    TEST_MODEL="gemini-1.5-flash" # 用于测试密钥是否可用的模型名
    SEARCH_MODELS=["gemini-2.0-flash-exp"]  # 支持搜索功能的模型列表
    IMAGE_MODELS=["gemini-2.0-flash-exp"] # 支持绘图功能的模型列表
    TOOLS_CODE_EXECUTION_ENABLED=false  # 是否启用代码执行工具，默认false
    SHOW_SEARCH_LINK=true  # 是否在响应中显示搜索结果链接，默认true
    SHOW_THINKING_PROCESS=true  # 是否显示模型思考过程，默认true
    FILTERED_MODELS=["gemini-1.0-pro-vision-latest", "gemini-pro-vision", "chat-bison-001", "text-bison-001", "embedding-gecko-001"] # 被禁用的模型列表

    # 图片生成配置
    PAID_KEY="your-paid-api-key"  # 付费版API Key，用于图片生成等高级功能
    CREATE_IMAGE_MODEL="imagen-3.0-generate-002"  # 图片生成模型，默认使用imagen-3.0
    
    # 图片上传配置
    UPLOAD_PROVIDER="smms"  # 图片上传提供商，目前支持smms、picgo、cloudflare_imgbed
    SMMS_SECRET_TOKEN="your-smms-token"  # SM.MS图床的API Token
    PICGO_API_KEY="your-picogo-apikey"  # PicoGo图床的API Key 可在 `https://www.picgo.net/settings/api` 获取
    CLOUDFLARE_IMGBED_URL="https://xxxxxxx.pages.dev/upload" # CloudFlare 图床上传地址，可自行搭建：`https://github.com/MarSeventh/CloudFlare-ImgBed`
    CLOUDFLARE_IMGBED_AUTH_CODE="your-cloudflare-imgber-auth-code" # CloudFlare图床的鉴权key，可在项目后台设置，若无鉴权则可直接置空。

    # stream_optimizer 相关配置
    # 是否启用流式输出优化，默认false
    STREAM_OPTIMIZER_ENABLED=false  
    STREAM_MIN_DELAY=0.016
    STREAM_MAX_DELAY=0.024
    STREAM_SHORT_TEXT_THRESHOLD=10
    STREAM_LONG_TEXT_THRESHOLD=50
    STREAM_CHUNK_SIZE=5
    ```

   ### 配置说明

   #### 基础配置

    - `BASE_URL`: Gemini API 的基础 URL
      - 默认值: `https://generativelanguage.googleapis.com/v1beta`
      - 说明: 通常无需修改，除非 API 地址发生变化
    - `MAX_FAILURES`: API Key 允许的最大失败次数
      - 默认值: `3`
      - 说明: 超过此次数后，Key 将被暂时标记为无效
    - `TIME_OUT`: 请求超时时间
      - 默认值: `300`
      - 说明: 单位为秒

   #### 认证与安全配置

    - `API_KEYS`: Gemini API 密钥列表
      - 格式: JSON 数组字符串
      - 用途: 支持多个 Key 轮询，实现负载均衡
      - 建议: 至少配置 2 个 Key 以保证服务可用性
    - `ALLOWED_TOKENS`: 访问令牌列表
      - 格式: JSON 数组字符串
      - 用途: 用于客户端认证
      - 安全提示: 请使用足够复杂的令牌
    - `AUTH_TOKEN`: 超级管理员令牌
      - 可选配置，留空则使用 ALLOWED_TOKENS 的第一个
      - 具有查看 API Key 状态等特权操作权限

   #### 模型功能配置

    - `TEST_MODEL`: 用于测试密钥可用性的模型
      - 默认值: `"gemini-1.5-flash"`
    - `SEARCH_MODELS`: 搜索功能支持的模型
      - 默认值: `["gemini-2.0-flash-exp"]`
      - 说明: 仅列表中的模型可使用搜索功能
    - `IMAGE_MODELS`: 绘图功能支持的模型
      - 默认值: `["gemini-2.0-flash-exp"]`
      - 说明: 仅列表中的模型可使用绘图功能
    - `FILTERED_MODELS`: 被禁用的模型列表
      - 默认值: `["gemini-1.0-pro-vision-latest", "gemini-pro-vision", "chat-bison-001", "text-bison-001", "embedding-gecko-001"]`
      - 说明: 列表中的模型将被禁用
    - `TOOLS_CODE_EXECUTION_ENABLED`: 代码执行功能
      - 默认值: `false`
      - 安全提示: 生产环境建议禁用
    - `SHOW_SEARCH_LINK`: 搜索结果链接显示
      - 默认值: `true`
      - 用途: 控制搜索结果中是否包含原始链接
    - `SHOW_THINKING_PROCESS`: 思考过程显示
      - 默认值: `true`
      - 用途: 显示模型的推理过程，便于调试

   #### 图片生成配置

    - `PAID_KEY`: 付费版 API Key
      - 用途: 用于图片生成等高级功能
      - 说明: 需要单独申请的付费版 Key
    - `CREATE_IMAGE_MODEL`: 图片生成模型
      - 默认值: `imagen-3.0-generate-002`
      - 说明: 当前支持的最新图片生成模型

   #### 图片上传配置

    - `UPLOAD_PROVIDER`: 图片上传服务提供商
      - 默认值: `smms`
      - 可选值: `smms`, `picgo`, `cloudflare_imgbed`
      - 说明:  用于选择图片上传的服务提供商。目前支持 SM.MS 图床, PicGo 图床, 以及 Cloudflare ImgBed。

    - `SMMS_SECRET_TOKEN`: SM.MS API Token
      - 用途: 用于图片上传到 SM.MS 图床的身份验证。
      - 获取方式: 需要在 [SM.MS 官网](https://sm.ms/) 注册并获取。

    - `PICGO_API_KEY`: PicGo API Key
      - 用途: 用于图片上传到 PicGo 图床的身份验证。
      - 获取方式: 可在 [PicGo 官网](https://www.picgo.net/settings/api) 的设置页面 API 选项中获取。

    - `CLOUDFLARE_IMGBED_URL`: Cloudflare ImgBed 上传地址
      - 用途:  指定 Cloudflare ImgBed 图床的上传 API 地址。
      - 获取方式:  如果您自行搭建了 Cloudflare ImgBed 服务，请填写您的服务部署地址。参考 [Cloudflare-ImgBed 项目](https://github.com/MarSeventh/CloudFlare-ImgBed) 自行搭建。
      - 注意:  URL 必须以 `https://` 开头，并指向 `/upload` 路径 ，例如 `https://cloudflare-imgbed-7b0.pages.dev/upload`。

    - `CLOUDFLARE_IMGBED_AUTH_CODE`: Cloudflare ImgBed 鉴权 Key
      - 用途:  用于 Cloudflare ImgBed 图床的身份验证。
      - 说明:  如果您的 Cloudflare ImgBed 服务启用了鉴权，请填写鉴权 Key。若未启用鉴权，则留空即可。
      - 获取方式:  在 Cloudflare ImgBed 项目的后台设置中获取，或在搭建时自行设置。

   #### 流式输出优化配置

    - `STREAM_OPTIMIZER_ENABLED`: 是否启用流式输出优化
      - 默认值: `false`
      - 说明: 是否启用流式输出优化
    - `STREAM_MIN_DELAY`: 最小延迟时间
      - 默认值: `0.016`（秒）
      - 说明: 长文本输出时使用的最小延迟时间，值越小输出速度越快
    - `STREAM_MAX_DELAY`: 最大延迟时间
      - 默认值: `0.024`（秒）
      - 说明: 短文本输出时使用的最大延迟时间，值越大输出速度越慢
    - `STREAM_SHORT_TEXT_THRESHOLD`: 短文本阈值
      - 默认值: `10`（字符）
      - 说明: 小于此长度的文本被视为短文本，将使用最大延迟输出
    - `STREAM_LONG_TEXT_THRESHOLD`: 长文本阈值
      - 默认值: `50`（字符）
      - 说明: 大于此长度的文本被视为长文本，将使用最小延迟并分块输出
    - `STREAM_CHUNK_SIZE`: 长文本分块大小
      - 默认值: `5`（字符）
      - 说明: 长文本分块输出时，每个块的大小

### ▶️ 运行

#### 使用 Docker (推荐)

1. **构建镜像**:

    ```bash
    docker build -t gemini-balance .
    ```

2. **运行容器**:

    ```bash
    docker run -d -p 8000:8000 --env-file .env gemini-balance
    ```

    - `-d`: 后台运行。
    - `-p 8000:8000`: 将容器的 8000 端口映射到主机的 8000 端口。
    - `--env-file .env`: 使用 `.env` 文件设置环境变量。

#### 手动运行

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- `--reload`: 开启热重载，方便开发调试 (生产环境不建议开启)。

## 🔌 API 接口

### 认证

所有 API 请求都需要在 Header 中添加 `Authorization` 字段，值为 `Bearer <your-token>`，其中 `<your-token>` 需要替换为你在 `.env` 文件中配置的 `ALLOWED_TOKENS` 中的一个或者 `AUTH_TOKEN`。

### API 路由

本服务提供两种API路由：

1. **OpenAI 兼容路由** (推荐)
   - 基础路径: `/v1`
   - 完全兼容OpenAI API格式
   - 支持所有Gemini模型

2. **Gemini 原生路由**
   - 基础路径: `/gemini/v1beta` 或 `/v1beta`
   - 遵循Google原生API格式
   - 适用于需要直接使用Gemini API的场景

### OpenAI兼容路由

#### 获取模型列表

- **URL**: `/v1/models`
- **Method**: `GET`
- **Header**: `Authorization: Bearer <your-token>`
- **Response**: 返回支持的所有模型列表，包括最新的`gemini-2.0-flash-exp-search`等模型

#### 聊天补全 (Chat Completions)

- **URL**: `/v1/chat/completions`
- **Method**: `POST`
- **Header**: `Authorization: Bearer <your-token>`
- **Body** (JSON):

    ```json
    {
        "messages": [
            {
                "role": "user",
                "content": "你好"
            }
        ],
        "model": "gemini-1.5-flash",
        "temperature": 0.7,
        "stream": false,
        "tools": [],
        "max_tokens": 8192,
        "stop": [],
        "top_p": 0.9,
        "top_k": 40
    }
    ```

  - `messages`: 消息列表，格式与 OpenAI API 相同
  - `model`: 模型名称，支持所有Gemini模型，包括:
    - `gemini-1.5-flash`: 快速响应模型
    - `gemini-2.0-flash-exp`: 实验性快速响应模型
    - `gemini-2.0-flash-exp-search`: 支持搜索功能的实验性模型
  - `stream`: 是否开启流式响应，`true` 或 `false`
  - `tools`: 使用的工具列表
  - 其他参数：与 OpenAI API 兼容的参数，如 `temperature`, `max_tokens` 等

### Gemini原生路由

#### 获取模型列表

- **URL**: `/gemini/v1beta/models` 或 `/v1beta/models`
- **Method**: `GET`
- **Header**: `Authorization: Bearer <your-token>`

#### 生成内容

- **URL**: `/gemini/v1beta/models/{model_name}:generateContent`
- **Method**: `POST`
- **Header**: `Authorization: Bearer <your-token>`

#### 流式生成内容

- **URL**: `/gemini/v1beta/models/{model_name}:streamGenerateContent`
- **Method**: `POST`
- **Header**: `Authorization: Bearer <your-token>`

### 获取词向量 (Embeddings)

- **URL**: `/v1/embeddings`
- **Method**: `POST`
- **Header**: `Authorization: Bearer <your-token>`
- **Body** (JSON):

    ```json
    {
        "input": "你的文本",
        "model": "text-embedding-004"
    }
    ```

  - `input`: 输入文本。
  - `model`: 模型名称。

### 健康检查

- **URL**: `/health`
- **Method**: `GET`

### Web界面功能

#### 验证页面 (auth.html)

- **URL**: `/auth`
- **说明**: 提供了一个简洁的Web界面用于验证访问令牌
- **功能特点**:
  - 现代化的渐变背景设计
  - 响应式布局，完美支持移动端
  - 毛玻璃效果的卡片设计
  - 优雅的动画效果（淡入、滑动、悬浮）
  - 安全的令牌验证机制
  - 清晰的错误提示功能
  - PWA支持，可安装为本地应用
  - 底部版权信息和GitHub链接
  - 支持暗色主题适配

#### API密钥状态管理 (keys_status.html)

- **URL**: `/v1/keys/list`
- **Method**: `GET`
- **Header**: `Authorization: Bearer <your-auth-token>`
- **功能特点**:
  - 只有使用 `AUTH_TOKEN` 才能访问此接口
  - 分类展示API密钥状态（有效/无效）
  - 可折叠的密钥列表分组
  - 每个密钥显示:
    - 状态标识（有效/无效）
    - 密钥内容
    - 失败次数统计
  - 高级功能:
    - 一键复制单个密钥
    - 批量复制分组密钥（JSON格式）
    - 实时刷新功能
    - 回到顶部/底部快捷按钮
  - 界面特性:
    - 响应式设计，适配各种屏幕
    - 优雅的动画效果
    - 操作反馈（复制成功提示）
    - PWA支持
    - 暗色主题适配

### 图片生成 (Image Generation)

- **URL**: `/v1/images/generations`
- **Method**: `POST`
- **Header**: `Authorization: Bearer <your-auth-token>`
- **说明**: Body示例和参数说明

    ```json
    {
    "model": "dall-e-3",
    "prompt": "{n:2} {ratio:16:9} 汉服美女",
    "n": 1,
    "size": "1024x1024"
    }
    ```

    **Prompt参数说明:**

    prompt支持通过特殊标记来控制生成参数：

    1. 图片数量控制:
       - 格式: `{n:数量}`
       - 示例: `{n:2} 一只可爱的猫` - 生成2张图片
       - 取值范围: 1-4
       - 说明: 如果在prompt中指定了n，将覆盖请求body中的n参数

    2. 图片比例控制:
       - 格式: `{ratio:宽:高}`
       - 示例: `{ratio:16:9} 一片森林` - 生成16:9比例的图片
       - 支持的比例: "1:1"、"3:4"、"4:3"、"9:16"、"16:9"
       - 说明: 如果指定了size参数，将优先使用size对应的比例

    3. 参数组合:
       - 示例: `{n:2} {ratio:16:9} 一片美丽的森林` - 生成2张16:9比例的图片
       - 说明: 这些参数标记会自动从prompt中移除，不会影响实际的图片生成提示词

    > 注意：n的取值范围[1,4], ratio取值范围"1:1"、"3:4"、"4:3"、"9:16" 和 "16:9"

## 📚 代码结构

```plaintext
.
├── app/
│   ├── api/                # API 路由
│   │   ├── gemini_routes.py   # Gemini 模型路由
│   │   └── openai_routes.py   # OpenAI 兼容路由
│   ├── core/               # 核心组件
│   │   ├── config.py         # 配置管理
│   │   ├── logger.py         # 日志配置
│   │   └── security.py       # 安全认证
│   ├── middleware/         # 中间件
│   │   └── request_logging_middleware.py  # 请求日志中间件
│   ├── schemas/            # 数据模型
│   │   ├── gemini_models.py  # Gemini 原始请求/响应模型
│   │   └── openai_models.py  # OpenAI 兼容请求/响应模型
│   ├── services/           # 服务层
│   │   ├── chat/           # 聊天相关服务
│   │   │   ├── api_client.py # API 客户端
│   │   │   ├── message_converter.py # 消息转换器
│   │   │   ├── response_handler.py # 响应处理器
│   │   │   └── retry_handler.py #重试处理器
│   │   ├── gemini_chat_service.py   # Gemini 原始聊天服务
│   │   ├── openai_chat_service.py   # OpenAI 兼容聊天服务
│   │   ├── embedding_service.py # 向量服务
│   │   ├── key_manager.py    # API Key 管理
│   │   └── model_service.py  # 模型服务
│   └── main.py              # 主程序入口
├── Dockerfile              # Dockerfile
├── requirements.txt       # 项目依赖
└── README.md               # 项目说明
```

## 🔒 安全性

- **API Key 轮询**: 自动轮换 API Key，提高可用性和负载均衡。
- **Bearer Token 认证**: 保护 API 端点，防止未经授权的访问。
- **请求日志记录**: 记录详细的请求信息，便于调试和审计 (可选，通过取消 `app.add_middleware(RequestLoggingMiddleware)` 的注释来启用)。
- **自动重试**: 在 API 请求失败时自动重试，提高服务的稳定性。

## 🤝 贡献

欢迎任何形式的贡献！如果你发现 bug、有新功能建议或者想改进代码，请随时提交 Issue 或 Pull Request。

1. Fork 本项目。
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)。
3. 提交你的改动 (`git commit -m 'Add some AmazingFeature'`)。
4. 推送到你的分支 (`git push origin feature/AmazingFeature`)。
5. 创建一个新的 Pull Request。

## ❓ 常见问题解答 (FAQ)

**Q: 如何获取 Gemini API Key？**

A: 请参考 Gemini API 的官方文档，申请 API Key。

**Q: 如何配置多个 API Key？**

A: 在 `.env` 文件的 `API_KEYS` 变量中，用列表的形式添加多个 Key，例如：`API_KEYS=["key1", "key2", "key3"]`。

**Q: 为什么我的 API Key 总是失败？**

A: 请检查以下几点：

- API Key 是否正确。
- API Key 是否已过期或被禁用。
- 是否超出了 API Key 的速率限制或配额。
- 网络连接是否正常。

**Q: 如何启用流式响应？**

A: 在请求的 Body 中，将 `stream` 参数设置为 `true` 即可。

**Q: 如何启用代码执行工具？**

A: 在 `.env` 文件的 `TOOLS_CODE_EXECUTION_ENABLED` 变量中, 设置为 `true` 即可。

## 📄 许可证

本项目采用 MIT 许可证。有关详细信息，请参阅 [LICENSE](LICENSE) 文件 (你需要创建一个 LICENSE 文件)。
