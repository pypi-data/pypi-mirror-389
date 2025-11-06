"""
统一的 AI Gateway
支持 Azure OpenAI、OpenRouter 和 Skywork
"""

import os
import requests
import base64
import mimetypes
import urllib3
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
from openai import AzureOpenAI, AsyncAzureOpenAI

# 禁用SSL警告（用于Skywork Gemini API）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _robust_gemini_json_parse(response: requests.Response) -> Dict[str, Any]:
    """
    解析 Gemini API 的 JSON 响应，使用与 skywork/llm_api.py 相同的逻辑
    """
    import json
    import re
    
    try:
        return response.json()
    except json.JSONDecodeError as initial_err:
        original_text = response.text
        
        # Strategy 1: Remove common control characters
        try:
            cleaned_text = re.sub(r'[\x00-\x1f\x7f]', '', original_text)
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Escape special characters
        try:
            cleaned_text = original_text.replace('\\', '\\\\')
            cleaned_text = cleaned_text.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '\\r')
            cleaned_text = cleaned_text.replace('\t', '\\t').replace('\b', '\\b').replace('\f', '\\f')
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass

        # Strategy 3: Thorough character cleanup
        try:
            cleaned_text = ''.join(char for char in original_text if ord(char) >= 32 or char in '\n\r\t')
            cleaned_text = cleaned_text.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass

        # Strategy 4: Regex extract the outermost JSON object
        try:
            json_match = re.search(r'\{.*\}', original_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            pass
            
        # All strategies failed
        raise initial_err

# 自动加载环境变量（从根目录的.env文件）
# 所有服务商的API key都统一放在根目录的.env文件中
load_dotenv()  # 加载根目录的.env文件

# 支持的提供商
PROVIDERS = ['azure', 'openrouter', 'skywork']

# 全局客户端缓存
_clients = {}
_async_clients = {}
_default_provider = None

# 全局 API key 配置（通过代码配置的 key）
_configured_keys = {
    'azure': {'api_key': None, 'endpoint': None},
    'openrouter': {'api_key': None, 'site_url': None, 'site_name': None},
    'skywork': {
        'openai': {'base_url': None, 'api_key': None},
        'google': {'base_url': None, 'api_key': None}
    }
}


def configure_api_keys(
    azure_api_key: Optional[str] = None,
    azure_endpoint: Optional[str] = None,
    openrouter_api_key: Optional[str] = None,
    openrouter_site_url: Optional[str] = None,
    openrouter_site_name: Optional[str] = None,
    skywork_openai_base_url: Optional[str] = None,
    skywork_openai_api_key: Optional[str] = None,
    skywork_google_base_url: Optional[str] = None,
    skywork_google_api_key: Optional[str] = None,
):
    """
    通过代码配置 API key（优先于环境变量）
    
    这种方式可以让用户在不使用 .env 文件的情况下配置 API key。
    配置的 key 会优先于环境变量使用。
    
    Args:
        azure_api_key: Azure OpenAI API key
        azure_endpoint: Azure OpenAI endpoint
        openrouter_api_key: OpenRouter API key
        openrouter_site_url: OpenRouter site URL（可选）
        openrouter_site_name: OpenRouter site name（可选）
        skywork_openai_base_url: Skywork OpenAI base URL
        skywork_openai_api_key: Skywork OpenAI API key
        skywork_google_base_url: Skywork Google base URL
        skywork_google_api_key: Skywork Google API key
    
    Example:
        >>> from gateways import configure_api_keys, chat
        >>> configure_api_keys(
        ...     azure_api_key="your-azure-key",
        ...     azure_endpoint="https://your-endpoint.cognitiveservices.azure.com/",
        ...     openrouter_api_key="your-openrouter-key"
        ... )
        >>> reply = chat("你好", "gpt-4o-mini", provider="azure")
    """
    global _configured_keys
    
    if azure_api_key:
        _configured_keys['azure']['api_key'] = azure_api_key
    if azure_endpoint:
        _configured_keys['azure']['endpoint'] = azure_endpoint
    
    if openrouter_api_key:
        _configured_keys['openrouter']['api_key'] = openrouter_api_key
    if openrouter_site_url:
        _configured_keys['openrouter']['site_url'] = openrouter_site_url
    if openrouter_site_name:
        _configured_keys['openrouter']['site_name'] = openrouter_site_name
    
    if skywork_openai_base_url:
        _configured_keys['skywork']['openai']['base_url'] = skywork_openai_base_url
    if skywork_openai_api_key:
        _configured_keys['skywork']['openai']['api_key'] = skywork_openai_api_key
    if skywork_google_base_url:
        _configured_keys['skywork']['google']['base_url'] = skywork_google_base_url
    if skywork_google_api_key:
        _configured_keys['skywork']['google']['api_key'] = skywork_google_api_key
    
    # 清除客户端缓存，使用新的配置
    _clients.clear()
    _async_clients.clear()


def _get_config_value(key: str, provider: str, sub_key: Optional[str] = None) -> Optional[str]:
    """
    获取配置值（优先使用代码配置，其次使用环境变量）
    
    Args:
        key: 配置键名
        provider: 服务商名称
        sub_key: 子键（用于 skywork 的 openai/google）
    
    Returns:
        配置值
    """
    # 优先使用代码配置的 key
    if provider == 'azure':
        if key == 'api_key' and _configured_keys['azure']['api_key']:
            return _configured_keys['azure']['api_key']
        if key == 'endpoint' and _configured_keys['azure']['endpoint']:
            return _configured_keys['azure']['endpoint']
    elif provider == 'openrouter':
        if key == 'api_key' and _configured_keys['openrouter']['api_key']:
            return _configured_keys['openrouter']['api_key']
        if key == 'site_url' and _configured_keys['openrouter']['site_url']:
            return _configured_keys['openrouter']['site_url']
        if key == 'site_name' and _configured_keys['openrouter']['site_name']:
            return _configured_keys['openrouter']['site_name']
    elif provider == 'skywork':
        if sub_key == 'openai':
            if key == 'base_url' and _configured_keys['skywork']['openai']['base_url']:
                return _configured_keys['skywork']['openai']['base_url']
            if key == 'api_key' and _configured_keys['skywork']['openai']['api_key']:
                return _configured_keys['skywork']['openai']['api_key']
        elif sub_key == 'google':
            if key == 'base_url' and _configured_keys['skywork']['google']['base_url']:
                return _configured_keys['skywork']['google']['base_url']
            if key == 'api_key' and _configured_keys['skywork']['google']['api_key']:
                return _configured_keys['skywork']['google']['api_key']
    
    # 如果代码配置没有，使用环境变量
    env_key_map = {
        ('azure', 'api_key'): 'AZURE_OPENAI_API_KEY',
        ('azure', 'endpoint'): 'AZURE_OPENAI_ENDPOINT',
        ('openrouter', 'api_key'): 'OPENROUTER_API_KEY',
        ('openrouter', 'site_url'): 'OPENROUTER_SITE_URL',
        ('openrouter', 'site_name'): 'OPENROUTER_SITE_NAME',
        ('skywork', 'openai', 'base_url'): 'OPENAI_BASE_URL',
        ('skywork', 'openai', 'api_key'): 'OPENAI_API_KEY',
        ('skywork', 'google', 'base_url'): 'GOOGLE_BASE_URL',
        ('skywork', 'google', 'api_key'): 'GOOGLE_API_KEY',
    }
    
    env_key = env_key_map.get((provider, key) if not sub_key else (provider, sub_key, key))
    if env_key:
        return os.getenv(env_key)
    
    return None


def _get_azure_client(api_version: str = "2024-12-01-preview", async_mode: bool = False):
    """获取 Azure OpenAI 客户端"""
    cache_key = f"azure_{api_version}_{async_mode}"
    
    if cache_key in (_async_clients if async_mode else _clients):
        return (_async_clients if async_mode else _clients)[cache_key]
    
    endpoint = _get_config_value('endpoint', 'azure')
    api_key = _get_config_value('api_key', 'azure')
    
    if not endpoint:
        raise ValueError(
            "请设置 Azure OpenAI Endpoint\n"
            "方式1: configure_api_keys(azure_endpoint='your-endpoint')\n"
            "方式2: 创建 .env 文件，添加: AZURE_OPENAI_ENDPOINT=your-endpoint\n"
            "方式3: export AZURE_OPENAI_ENDPOINT='your-endpoint'"
        )
    if not api_key:
        raise ValueError(
            "请设置 Azure OpenAI API Key\n"
            "方式1: configure_api_keys(azure_api_key='your-key')\n"
            "方式2: 创建 .env 文件，添加: AZURE_OPENAI_API_KEY=your-key\n"
            "方式3: export AZURE_OPENAI_API_KEY='your-key'"
        )
    
    if async_mode:
        client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        _async_clients[cache_key] = client
    else:
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        _clients[cache_key] = client
    
    return client


def _get_openrouter_client(async_mode: bool = False):
    """获取 OpenRouter 客户端"""
    cache_key = f"openrouter_{async_mode}"
    
    if cache_key in (_async_clients if async_mode else _clients):
        return (_async_clients if async_mode else _clients)[cache_key]
    
    api_key = _get_config_value('api_key', 'openrouter')
    if not api_key:
        raise ValueError(
            "请设置 OpenRouter API Key\n"
            "方式1: configure_api_keys(openrouter_api_key='your-key')\n"
            "方式2: 创建 .env 文件，添加: OPENROUTER_API_KEY=your-key\n"
            "方式3: export OPENROUTER_API_KEY='your-key'"
        )
    
    # 构建额外headers
    extra_headers = {}
    site_url = _get_config_value('site_url', 'openrouter')
    site_name = _get_config_value('site_name', 'openrouter')
    if site_url:
        extra_headers["HTTP-Referer"] = site_url
    if site_name:
        extra_headers["X-Title"] = site_name
    
    if async_mode:
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        client._extra_headers = extra_headers
        _async_clients[cache_key] = client
    else:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        client._extra_headers = extra_headers
        _clients[cache_key] = client
    
    return client


def _get_skywork_client(model: str, async_mode: bool = False):
    """
    获取 Skywork 客户端（根据模型名自动选择 GPT 或 Gemini）
    
    Args:
        model: 模型名称，用于判断使用 GPT 还是 Gemini API
        async_mode: 是否使用异步客户端（Skywork 暂不支持异步）
    
    Returns:
        客户端实例（OpenAI 客户端用于 GPT，或返回 'gemini' 标识用于 Gemini）
    """
    if async_mode:
        # Skywork 暂不支持异步，返回同步客户端
        pass
    
    # 根据模型名判断使用 GPT 还是 Gemini
    if 'gpt' in model.lower():
        # 使用 GPT API
        base_url = _get_config_value('base_url', 'skywork', 'openai')
        api_key = _get_config_value('api_key', 'skywork', 'openai')
        
        if not base_url or not api_key:
            raise ValueError(
                "请设置 Skywork OpenAI 配置（用于 GPT 模型）\n"
                "方式1: 使用 configure_api_keys(skywork_openai_base_url=..., skywork_openai_api_key=...)\n"
                "方式2: 创建 .env 文件，添加: OPENAI_BASE_URL=your-url, OPENAI_API_KEY=your-key\n"
                "方式3: export OPENAI_BASE_URL='your-url' OPENAI_API_KEY='your-key'"
            )
        
        return OpenAI(base_url=base_url, api_key=api_key)
    elif 'gemini' in model.lower():
        # 返回标识符，在调用时使用 Gemini API
        base_url = _get_config_value('base_url', 'skywork', 'google')
        api_key = _get_config_value('api_key', 'skywork', 'google')
        
        if not base_url or not api_key:
            raise ValueError(
                "请设置 Skywork Google 配置（用于 Gemini 模型）\n"
                "方式1: 使用 configure_api_keys(skywork_google_base_url=..., skywork_google_api_key=...)\n"
                "方式2: 创建 .env 文件，添加: GOOGLE_BASE_URL=your-url, GOOGLE_API_KEY=your-key\n"
                "方式3: export GOOGLE_BASE_URL='your-url' GOOGLE_API_KEY='your-key'"
            )
        
        return {'type': 'gemini', 'base_url': base_url, 'api_key': api_key}
    else:
        raise ValueError(f"Skywork 不支持的模型: {model}")


def get_client(provider: Optional[str] = None, async_mode: bool = False, **kwargs):
    """
    获取客户端实例
    
    Args:
        provider: 服务商 ('azure'、'openrouter' 或 'skywork')，如果为None则使用默认
        async_mode: 是否使用异步客户端
        **kwargs: 其他参数（如api_version用于Azure，model用于skywork）
    
    Returns:
        客户端实例
    """
    provider = provider or _default_provider or _detect_provider()
    
    if provider not in PROVIDERS:
        raise ValueError(f"不支持的提供商: {provider}，支持: {PROVIDERS}")
    
    if provider == 'azure':
        api_version = kwargs.get('api_version', '2024-12-01-preview')
        return _get_azure_client(api_version, async_mode)
    elif provider == 'openrouter':
        return _get_openrouter_client(async_mode)
    elif provider == 'skywork':
        model = kwargs.get('model', 'gpt-4o')
        return _get_skywork_client(model, async_mode)
    else:
        raise ValueError(f"未知的提供商: {provider}")


def _detect_provider():
    """自动检测可用的提供商"""
    # 检查 Azure
    if _get_config_value('api_key', 'azure') and _get_config_value('endpoint', 'azure'):
        return 'azure'
    # 检查 OpenRouter
    elif _get_config_value('api_key', 'openrouter'):
        return 'openrouter'
    # 检查 Skywork
    elif (_get_config_value('base_url', 'skywork', 'openai') and _get_config_value('api_key', 'skywork', 'openai')) or \
         (_get_config_value('base_url', 'skywork', 'google') and _get_config_value('api_key', 'skywork', 'google')):
        return 'skywork'
    else:
        raise ValueError(
            "未找到任何可用的服务商配置。请使用以下方式之一配置：\n"
            "1. 使用 configure_api_keys() 函数配置\n"
            "2. 创建 .env 文件并设置环境变量\n"
            "3. 设置系统环境变量\n"
            "\n配置要求：\n"
            "Azure: azure_api_key 和 azure_endpoint\n"
            "OpenRouter: openrouter_api_key\n"
            "Skywork: (skywork_openai_base_url 和 skywork_openai_api_key) 或 (skywork_google_base_url 和 skywork_google_api_key)"
        )


def set_provider(provider: str):
    """
    设置默认服务商
    
    Args:
        provider: 服务商名称 ('azure' 或 'openrouter')
    """
    global _default_provider
    if provider not in PROVIDERS:
        raise ValueError(f"不支持的提供商: {provider}，支持: {PROVIDERS}")
    _default_provider = provider


def chat(
    prompt: str,
    model: str,
    provider: Optional[str] = None,
    **kwargs
) -> str:
    """
    同步调用 AI 模型（最简单的方式）
    
    Args:
        prompt: 用户消息
        model: 统一模型名称（如 'gpt-4o-mini'），会自动映射到各服务商的实际模型名
            也支持直接使用完整模型ID（如 'openai/gpt-4o-mini'），会直接使用
        provider: 服务商 ('azure'、'openrouter' 或 'skywork')，如果为None则自动检测
        **kwargs: 其他参数（temperature, max_tokens等）
    
    Returns:
        模型回复内容（字符串）
    
    Example:
        >>> from gateways import chat
        >>> # 使用统一模型名（推荐）
        >>> reply = chat("你好", "gpt-4o-mini", provider="azure")
        >>> reply = chat("你好", "gpt-4o-mini", provider="openrouter")
        >>> reply = chat("你好", "gpt-4o", provider="skywork")
        >>> reply = chat("你好", "gemini-2.5-pro", provider="skywork")
        >>> # 也可以直接使用完整模型ID
        >>> reply = chat("你好", "openai/gpt-4o-mini", provider="openrouter")
    """
    provider = provider or _default_provider or _detect_provider()
    
    # 映射模型名称
    actual_model = _map_model_name(model, provider)
    
    # Skywork 需要特殊处理
    if provider == 'skywork':
        return _chat_skywork(prompt, actual_model, **kwargs)
    
    client = get_client(provider, async_mode=False, model=actual_model, **kwargs)
    
    messages = kwargs.pop('messages', None)
    if messages is None:
        messages = [{"role": "user", "content": prompt}]
    
    # OpenRouter需要特殊处理extra_headers
    extra_headers = getattr(client, '_extra_headers', None)
    
    completion = client.chat.completions.create(
        model=actual_model,
        messages=messages,
        extra_headers=extra_headers,
        **kwargs
    )
    
    return completion.choices[0].message.content


def _chat_skywork(prompt: str, model: str, **kwargs) -> str:
    """
    Skywork 专用调用函数（处理 GPT 和 Gemini 两种不同的 API）
    """
    system_prompt = kwargs.pop('system_prompt', "You are a helpful assistant.")
    messages = kwargs.pop('messages', None)
    
    if messages is None:
        user_content = prompt
    else:
        # 处理消息历史
        user_content = messages[-1].get('content', prompt) if messages else prompt
        if messages and len(messages) > 1:
            system_prompt = messages[0].get('content', system_prompt) if messages[0].get('role') == 'system' else system_prompt
    
    # 判断是 GPT 还是 Gemini
    if 'gpt' in model.lower():
        # 使用 GPT API
        client = _get_skywork_client(model, async_mode=False)
        
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            **kwargs
        )
        
        return completion.choices[0].message.content
    elif 'gemini' in model.lower():
        # 使用 Gemini API
        gemini_config = _get_skywork_client(model, async_mode=False)
        
        headers = {
            "Authorization": f"Bearer {gemini_config['api_key']}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            **kwargs
        }
        
        response = requests.post(
            gemini_config['base_url'],
            headers=headers,
            json=data,
            timeout=120,
            verify=False
        )
        response.raise_for_status()
        
        # 使用与 skywork/llm_api.py 相同的解析逻辑
        response_json = _robust_gemini_json_parse(response)
        
        # 检查是否有错误
        if "code" in response_json and "code_msg" in response_json:
            error_msg = response_json.get("code_msg", "未知错误")
            raise ValueError(f"Gemini API 错误: {error_msg}")
        
        if "choices" not in response_json:
            raise ValueError(f"Gemini API 响应格式错误: {response_json}")
        
        return response_json["choices"][0]["message"]["content"]
    else:
        raise ValueError(f"Skywork 不支持的模型: {model}")


async def chat_async(
    prompt: str,
    model: str,
    provider: Optional[str] = None,
    **kwargs
) -> str:
    """
    异步调用 AI 模型
    
    Args:
        prompt: 用户消息
        model: 统一模型名称（如 'gpt-4o-mini'），会自动映射到各服务商的实际模型名
        provider: 服务商 ('azure'、'openrouter' 或 'skywork')
        **kwargs: 其他参数
    
    Returns:
        模型回复内容（字符串）
    
    Example:
        >>> import asyncio
        >>> from gateways import chat_async
        >>> async def main():
        ...     reply = await chat_async("你好", "gpt-4o-mini", provider="azure")
        ...     print(reply)
        >>> asyncio.run(main())
    """
    provider = provider or _default_provider or _detect_provider()
    
    # 映射模型名称
    actual_model = _map_model_name(model, provider)
    
    # Skywork 暂不支持异步，使用同步调用
    if provider == 'skywork':
        import asyncio
        return await asyncio.to_thread(_chat_skywork, prompt, actual_model, **kwargs)
    
    client = get_client(provider, async_mode=True, model=actual_model, **kwargs)
    
    messages = kwargs.pop('messages', None)
    if messages is None:
        messages = [{"role": "user", "content": prompt}]
    
    # OpenRouter需要特殊处理extra_headers
    extra_headers = getattr(client, '_extra_headers', None)
    
    completion = await client.chat.completions.create(
        model=actual_model,
        messages=messages,
        extra_headers=extra_headers,
        **kwargs
    )
    
    return completion.choices[0].message.content


def chat_with_history(
    messages: List[Dict[str, str]],
    model: str,
    provider: Optional[str] = None,
    **kwargs
) -> str:
    """
    使用消息历史进行对话（同步）
    
    Args:
        messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
        model: 统一模型名称（如 'gpt-4o-mini'），会自动映射到各服务商的实际模型名
        provider: 服务商 ('azure' 或 'openrouter')
        **kwargs: 其他参数
    
    Returns:
        模型回复内容
    
    Example:
        >>> from gateways import chat_with_history
        >>> messages = [
        ...     {"role": "user", "content": "你好"},
        ...     {"role": "assistant", "content": "你好！"},
        ...     {"role": "user", "content": "今天天气怎么样？"}
        ... ]
        >>> reply = chat_with_history(messages, "gpt-4o-mini", provider="azure")
    """
    return chat("", model=model, provider=provider, messages=messages, **kwargs)


# 模型名称映射（统一模型名 -> 各服务商实际模型名）
_MODEL_MAPPING = {
    'azure': {
        # Azure使用部署名称，通常直接使用模型名
        'gpt-4o-mini': 'gpt-4o-mini',
        'gpt-4o': 'gpt-4o',
        'gpt-4-turbo': 'gpt-4-turbo',
        'gpt-35-turbo': 'gpt-35-turbo',
    },
    'openrouter': {
        # OpenRouter使用完整模型ID格式：provider/model-name
        'gpt-4o-mini': 'openai/gpt-4o-mini',
        'gpt-4o': 'openai/gpt-4o',
        'gpt-4-turbo': 'openai/gpt-4-turbo',
        'gpt-4': 'openai/gpt-4',
        'gpt-3.5-turbo': 'openai/gpt-3.5-turbo',
        'claude-3-haiku': 'anthropic/claude-3-haiku',
        'claude-3-sonnet': 'anthropic/claude-3-sonnet',
        'claude-3-opus': 'anthropic/claude-3-opus',
        'gemma-free': 'google/gemma-3n-e2b-it:free',
        'gemini-free': 'google/gemini-2.0-flash-exp:free',
        'gemini-pro': 'google/gemini-pro',
        'llama-3.3-8b': 'meta-llama/llama-3.3-8b-instruct:free',
        'llama-3.1-8b': 'meta-llama/llama-3.1-8b-instruct:free',
    },
    'skywork': {
        # Skywork支持GPT和Gemini模型
        'gpt-4o-mini': 'gpt-4o-mini',
        'gpt-4o': 'gpt-4o',
        'gpt-4o-2024-11-20': 'gpt-4o-2024-11-20',
        'gpt-4': 'gpt-4',
        'gpt-4.1': 'gpt-4.1',
        'gemini-2.0-flash': 'gemini-2.0-flash',
        'gemini-2.5-pro-preview-05-06': 'gemini-2.5-pro-preview-05-06',
        'gemini-2.5-pro': 'gemini-2.5-pro',
        'gemini-2.5-flash-preview': 'gemini-2.5-flash-preview',
        'gemini-2.5-flash': 'gemini-2.5-flash',
        'gemini-2.5-flash-preview-thinking': 'gemini-2.5-flash-preview-thinking',
        'gemini-2.5-flash-lite': 'gemini-2.5-flash-lite',
        'gemini-2.0-flash-lite': 'gemini-2.0-flash-lite',
    }
}


def _map_model_name(model: str, provider: str) -> str:
    """
    将统一模型名映射到各服务商的实际模型名
    
    Args:
        model: 统一模型名（如 'gpt-4o-mini'）
        provider: 服务商名称
    
    Returns:
        实际模型名（如果映射不到，返回原始模型名）
    """
    mapping = _MODEL_MAPPING.get(provider, {})
    # 如果找到映射，返回映射后的名称
    # 如果找不到，返回原始模型名（支持直接使用完整模型ID）
    return mapping.get(model, model)


def get_available_models(provider: Optional[str] = None) -> Dict[str, str]:
    """
    获取可用的模型列表
    
    Args:
        provider: 服务商名称，如果为None则返回所有服务商的模型
    
    Returns:
        模型映射字典
    """
    if provider:
        if provider not in PROVIDERS:
            raise ValueError(f"不支持的提供商: {provider}，支持: {PROVIDERS}")
        return _MODEL_MAPPING.get(provider, {}).copy()
    else:
        return {p: _MODEL_MAPPING[p].copy() for p in PROVIDERS}

