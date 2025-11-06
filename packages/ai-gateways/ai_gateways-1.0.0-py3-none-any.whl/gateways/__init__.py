"""
统一的 AI Gateway 包
支持 Azure OpenAI、OpenRouter 和 Skywork 三种服务商
"""

from .gateway import chat, chat_async, chat_with_history, get_client, set_provider, get_available_models, configure_api_keys

__all__ = [
    'chat',
    'chat_async',
    'chat_with_history',
    'get_client',
    'set_provider',
    'get_available_models',
    'configure_api_keys',
]

__version__ = '1.0.0'

