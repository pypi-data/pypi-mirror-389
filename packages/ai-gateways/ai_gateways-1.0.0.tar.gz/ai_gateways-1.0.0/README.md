# AI Gateway 统一调用包

统一的 AI Gateway 包，支持 Azure OpenAI、OpenRouter 和 Skywork 三种服务商，通过指定服务商和模型名即可最简化调用。

## 🚀 快速开始

### 1. 安装包

**方式一：从源码安装（推荐）**

```bash
# 克隆或下载项目
git clone <your-repo-url>
cd gateways

# 安装包（开发模式，修改代码后立即生效）
pip install -e .
```

**方式二：从本地安装**

```bash
# 在项目根目录执行
pip install .
```

**方式三：构建分发包后安装**

```bash
# 安装构建工具（如果还没有）
pip install setuptools wheel

# 构建分发包
python setup.py sdist bdist_wheel

# 安装分发包
pip install dist/ai-gateways-1.0.0.tar.gz
# 或使用 wheel 文件
pip install dist/ai_gateways-1.0.0-py3-none-any.whl
```

**方式四：发布到 PyPI 后安装（如果已发布）**

```bash
pip install ai-gateways
```

**安装完成后，包会自动安装所有依赖：**
- openai>=1.0.0
- python-dotenv>=1.0.0
- requests>=2.31.0
- urllib3>=1.26.0

### 2. 配置 API Key

**重要：** 你的 API key 是隐私信息，不会被包含在包中。你需要自己配置。

有两种方式配置 API key：

**方式一：使用代码配置（推荐，更安全）**

```python
from gateways import configure_api_keys, chat

# 配置 API key
configure_api_keys(
    azure_api_key="your-azure-api-key",
    azure_endpoint="https://your-endpoint.cognitiveservices.azure.com/",
    openrouter_api_key="your-openrouter-api-key",
)

# 使用
reply = chat("你好", "gpt-4o-mini", provider="azure")
```

**方式二：使用 .env 文件**

1. 复制模板文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填写你的真实 API key：

```bash
# Azure OpenAI（可选）
AZURE_OPENAI_API_KEY=your-azure-api-key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/

# OpenRouter（可选）
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_SITE_URL=https://your-site.com  # 可选
OPENROUTER_SITE_NAME=Your Site Name        # 可选

# Skywork（可选，支持 GPT 和 Gemini）
# 如果使用 GPT 模型，需要配置：
OPENAI_BASE_URL=your-openai-base-url
OPENAI_API_KEY=your-openai-api-key
# 如果使用 Gemini 模型，需要配置：
GOOGLE_BASE_URL=your-google-base-url
GOOGLE_API_KEY=your-google-api-key
```

**注意：** 
- `.env` 文件不会被上传到 PyPI，你的 API key 是安全的
- 所有服务商的 API key 都统一放在根目录的 `.env` 文件中
- 至少需要配置一个服务商的 API key
- 推荐使用 `configure_api_keys()` 函数配置，更安全

### 3. 使用

```python
from gateways import chat

# 使用统一模型名（推荐）✨
# 系统会自动将 'gpt-4o-mini' 映射到各服务商的实际模型名
reply = chat("你好", "gpt-4o-mini", provider="azure")      # Azure: gpt-4o-mini
reply = chat("你好", "gpt-4o-mini", provider="openrouter")  # OpenRouter: openai/gpt-4o-mini
reply = chat("你好", "gpt-4o", provider="skywork")         # Skywork: gpt-4o
reply = chat("你好", "gemini-2.5-pro", provider="skywork")  # Skywork: gemini-2.5-pro

# 如果不指定provider，会自动检测可用的服务商
reply = chat("你好", "gpt-4o-mini")  # 自动使用Azure（如果已配置）

# 也可以直接使用完整模型ID（向后兼容）
reply = chat("你好", "openai/gpt-4o-mini", provider="openrouter")
```

## 📖 API 文档

### `chat(prompt, model, provider=None, **kwargs)`

同步调用 AI 模型（最简单的方式）

**参数：**
- `prompt` (str): 用户消息
- `model` (str): **统一模型名称**（推荐），如 `'gpt-4o-mini'`
  - 系统会自动映射到各服务商的实际模型名
  - Azure: `'gpt-4o-mini'` → `'gpt-4o-mini'` (部署名称)
  - OpenRouter: `'gpt-4o-mini'` → `'openai/gpt-4o-mini'`
  - 也支持直接使用完整模型ID（如 `'openai/gpt-4o-mini'`），会直接使用
- `provider` (str, 可选): 服务商 (`'azure'` 或 `'openrouter'`)，如果为None则自动检测
- `**kwargs`: 其他参数（temperature, max_tokens等）

**返回：**
- `str`: 模型回复内容

**示例：**
```python
from gateways import chat

# 使用统一模型名（推荐）✨
reply = chat("解释什么是人工智能", "gpt-4o-mini", provider="azure", temperature=0.7)
reply = chat("解释什么是人工智能", "gpt-4o-mini", provider="openrouter")  # 自动映射为 openai/gpt-4o-mini

# 使用OpenRouter的其他模型
reply = chat("解释什么是人工智能", "claude-3-haiku", provider="openrouter")  # 自动映射为 anthropic/claude-3-haiku
reply = chat("解释什么是人工智能", "gemma-free", provider="openrouter")  # 自动映射为 google/gemma-3n-e2b-it:free

# 也可以直接使用完整模型ID（向后兼容）
reply = chat("解释什么是人工智能", "openai/gpt-4o-mini", provider="openrouter")
```

### `chat_async(prompt, model, provider=None, **kwargs)`

异步调用 AI 模型

**示例：**
```python
import asyncio
from gateways import chat_async

async def main():
    reply = await chat_async("你好", "gpt-4o-mini", provider="azure")
    print(reply)

asyncio.run(main())
```

### `chat_with_history(messages, model, provider=None, **kwargs)`

使用消息历史进行对话

**示例：**
```python
from gateways import chat_with_history

messages = [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
    {"role": "user", "content": "今天天气怎么样？"}
]

reply = chat_with_history(messages, "gpt-4o-mini", provider="azure")
```

### `get_client(provider=None, async_mode=False, **kwargs)`

获取客户端实例（高级用法）

**示例：**
```python
from gateways import get_client

client = get_client(provider="azure")
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "你好"}]
)
```

### `set_provider(provider)`

设置默认服务商

**示例：**
```python
from gateways import set_provider

set_provider("azure")  # 设置Azure为默认服务商
reply = chat("你好", "gpt-4o-mini")  # 自动使用Azure
```

### `configure_api_keys(...)`

通过代码配置 API key（优先于环境变量）

**参数：**
- `azure_api_key`: Azure OpenAI API key
- `azure_endpoint`: Azure OpenAI endpoint
- `openrouter_api_key`: OpenRouter API key
- `openrouter_site_url`: OpenRouter site URL（可选）
- `openrouter_site_name`: OpenRouter site name（可选）
- `skywork_openai_base_url`: Skywork OpenAI base URL
- `skywork_openai_api_key`: Skywork OpenAI API key
- `skywork_google_base_url`: Skywork Google base URL
- `skywork_google_api_key`: Skywork Google API key

**示例：**
```python
from gateways import configure_api_keys, chat

# 配置 API key
configure_api_keys(
    azure_api_key="your-azure-key",
    azure_endpoint="https://your-endpoint.cognitiveservices.azure.com/",
    openrouter_api_key="your-openrouter-key",
)

# 使用
reply = chat("你好", "gpt-4o-mini", provider="azure")
```

**注意：** 代码配置的 key 会优先于环境变量使用。

## 🎯 常用模型（统一模型名）

### 通用模型（所有服务商都支持）
- `gpt-4o-mini` - GPT-4o Mini（推荐，快速且经济）
- `gpt-4o` - GPT-4o（最新模型）
- `gpt-4-turbo` - GPT-4 Turbo

### OpenRouter 特有模型
- `claude-3-haiku` - Claude 3 Haiku（快速且便宜）
- `claude-3-sonnet` - Claude 3 Sonnet（平衡）
- `claude-3-opus` - Claude 3 Opus（最强）
- `gemma-free` - Google Gemma（免费）
- `gemini-free` - Google Gemini 2.0 Flash（免费）
- `gemini-pro` - Google Gemini Pro
- `llama-3.3-8b` - Llama 3.3 8B（免费）
- `llama-3.1-8b` - Llama 3.1 8B（免费）

### Skywork 特有模型
**GPT 模型：**
- `gpt-4o-mini` - GPT-4o Mini
- `gpt-4o` - GPT-4o
- `gpt-4o-2024-11-20` - GPT-4o 特定版本
- `gpt-4` - GPT-4
- `gpt-4.1` - GPT-4.1

**Gemini 模型：**
- `gemini-2.5-pro` - Gemini 2.5 Pro（最佳性能）
- `gemini-2.5-flash` - Gemini 2.5 Flash（快速）
- `gemini-2.0-flash` - Gemini 2.0 Flash
- `gemini-2.5-flash-preview` - Gemini 2.5 Flash 预览版
- `gemini-2.5-flash-lite` - Gemini 2.5 Flash Lite
- `gemini-2.0-flash-lite` - Gemini 2.0 Flash Lite

### 查看所有可用模型

```python
from gateways import get_available_models

# 查看所有服务商的模型映射
models = get_available_models()

# 查看特定服务商的模型
azure_models = get_available_models("azure")
openrouter_models = get_available_models("openrouter")
```

**注意：** 使用统一模型名时，系统会自动映射到各服务商的实际模型名。例如：
- `gpt-4o-mini` 在 Azure 中映射为 `gpt-4o-mini`
- `gpt-4o-mini` 在 OpenRouter 中映射为 `openai/gpt-4o-mini`

## 💡 使用示例

### 基础用法（使用统一模型名）

```python
from gateways import chat

# 使用统一模型名，系统自动映射
reply = chat("什么是人工智能？", "gpt-4o-mini", provider="azure")
print(reply)

# 同样的模型名，不同的服务商
reply_azure = chat("什么是人工智能？", "gpt-4o-mini", provider="azure")
reply_openrouter = chat("什么是人工智能？", "gpt-4o-mini", provider="openrouter")
```

### 指定参数

```python
from gateways import chat

reply = chat(
    "写一首关于春天的诗",
    "gpt-4o-mini",
    provider="azure",
    temperature=0.8,
    max_tokens=500
)
```

### 多轮对话

```python
from gateways import chat_with_history

messages = [
    {"role": "system", "content": "你是一个友好的助手"},
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
    {"role": "user", "content": "告诉我一个笑话"}
]

reply = chat_with_history(messages, "gpt-4o-mini", provider="azure")
print(reply)
```

### 异步调用

```python
import asyncio
from gateways import chat_async

async def main():
    tasks = [
        chat_async("什么是AI？", "gpt-4o-mini", provider="azure"),
        chat_async("什么是机器学习？", "gpt-4o-mini", provider="azure"),
    ]
    replies = await asyncio.gather(*tasks)
    for reply in replies:
        print(reply)

asyncio.run(main())
```

## 🔧 配置说明

### 自动检测服务商

如果不指定 `provider`，系统会按以下顺序自动检测：
1. 如果设置了默认服务商（通过 `set_provider()`），使用默认服务商
2. 如果配置了 Azure（`AZURE_OPENAI_API_KEY` 和 `AZURE_OPENAI_ENDPOINT`），使用 Azure
3. 如果配置了 OpenRouter（`OPENROUTER_API_KEY`），使用 OpenRouter
4. 如果都没有配置，抛出错误

### 环境变量

**Azure OpenAI:**
- `AZURE_OPENAI_API_KEY` - API密钥（必需）
- `AZURE_OPENAI_ENDPOINT` - 端点URL（必需）

**OpenRouter:**
- `OPENROUTER_API_KEY` - API密钥（必需）
- `OPENROUTER_SITE_URL` - 网站URL（可选）
- `OPENROUTER_SITE_NAME` - 网站名称（可选）

**Skywork:**
- `OPENAI_BASE_URL` - OpenAI API 基础URL（用于 GPT 模型）
- `OPENAI_API_KEY` - OpenAI API 密钥（用于 GPT 模型）
- `GOOGLE_BASE_URL` - Google API 基础URL（用于 Gemini 模型）
- `GOOGLE_API_KEY` - Google API 密钥（用于 Gemini 模型）

**注意：** 不再需要在子目录（`azure/`、`openrouter/` 或 `skywork/`）下单独配置 `.env` 文件，所有配置都统一在根目录的 `.env` 文件中。

## 📁 项目结构

```
gateways/
├── __init__.py          # 包入口
├── gateway.py           # 核心实现
├── requirements.txt     # 依赖
├── README.md           # 文档
├── azure/              # Azure相关文件
└── openrouter/         # OpenRouter相关文件
```

## ⚡ 特性

- ✅ **统一接口** - 一个API支持多个服务商
- ✅ **自动检测** - 自动选择可用的服务商
- ✅ **客户端缓存** - 自动复用连接，提高性能
- ✅ **同步/异步** - 支持同步和异步调用
- ✅ **简单易用** - 一行代码即可调用
- ✅ **灵活配置** - 支持环境变量和代码配置

## 🆘 故障排查

### 错误：未找到可用的服务商配置

确保至少配置了一个服务商的 API key 和必要的环境变量。

### 错误：不支持的提供商

确保 `provider` 参数是 `'azure'` 或 `'openrouter'`。

### Azure 调用失败

检查：
1. `AZURE_OPENAI_API_KEY` 是否正确
2. `AZURE_OPENAI_ENDPOINT` 是否正确
3. 模型部署名称是否正确

### OpenRouter 调用失败

检查：
1. `OPENROUTER_API_KEY` 是否正确
2. 账户余额是否充足
3. 模型ID是否正确（格式：`provider/model-name`）

