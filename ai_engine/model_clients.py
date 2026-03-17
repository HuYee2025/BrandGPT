"""
AI模型客户端 - 支持多种大模型
"""
import json
import requests
from typing import Generator, Optional
from openai import OpenAI
import anthropic


class BaseModelClient:
    """模型客户端基类"""

    def __init__(self, api_key: str, model_name: str, **kwargs):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens', 4000)

    def chat(self, messages: list, stream: bool = False) -> str | Generator:
        """发送聊天请求"""
        raise NotImplementedError


class OpenAIClient(BaseModelClient):
    """OpenAI GPT模型客户端"""

    def __init__(self, api_key: str, model_name: str = 'gpt-4', **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        self.client = OpenAI(api_key=api_key)

    def chat(self, messages: list, stream: bool = False) -> str | Generator:
        """发送聊天请求"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=stream
        )

        if stream:
            return self._stream_response(response)
        return response.choices[0].message.content

    def _stream_response(self, response):
        """处理流式响应"""
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class ClaudeClient(BaseModelClient):
    """Claude模型客户端"""

    def __init__(self, api_key: str, model_name: str = 'claude-3-sonnet-20240229', **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        self.client = anthropic.Anthropic(api_key=api_key)

    def chat(self, messages: list, stream: bool = False) -> str | Generator:
        """发送聊天请求"""

        # 转换消息格式
        claude_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                continue  # system消息单独处理
            claude_messages.append({
                'role': msg['role'],
                'content': msg['content']
            })

        # 添加system prompt
        system_prompt = None
        for msg in messages:
            if msg['role'] == 'system':
                system_prompt = msg['content']
                break

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=claude_messages,
            stream=stream
        )

        if stream:
            return self._stream_response(response)
        return response.content[0].text

    def _stream_response(self, response):
        """处理流式响应"""
        for chunk in response:
            if chunk.type == 'content_block_delta':
                if chunk.delta.type == 'text_delta':
                    yield chunk.delta.text


class BaiduClient(BaseModelClient):
    """百度文心一言模型客户端"""

    def __init__(self, api_key: str, model_name: str = 'ernie-4.0-8k', **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        self.api_base = 'https://qianfan.baidubce.com/v2'

    def chat(self, messages: list, stream: bool = False) -> str | Generator:
        """发送聊天请求"""
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                formatted_messages.insert(0, {'role': 'user', 'content': msg['content']})
            else:
                formatted_messages.append({'role': msg['role'], 'content': msg['content']})

        url = f"{self.api_base}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        data = {
            'model': self.model_name,
            'messages': formatted_messages,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

        response = requests.post(url, json=data, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()

        return result['choices'][0]['message']['content']


class AlibabaClient(BaseModelClient):
    """阿里通义千问模型客户端"""

    def __init__(self, api_key: str, model_name: str = 'qwen-turbo', **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        self.api_base = 'https://dashscope.aliyuncs.com/api/v1'

    def chat(self, messages: list, stream: bool = False) -> str | Generator:
        """发送聊天请求"""
        url = f"{self.api_base}/services/aigc/text-generation/generation"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-DashScope-Os': 'HTTP'
        }

        # 提取system prompt
        system_prompt = ''
        formatted_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                system_prompt = msg['content']
            else:
                formatted_messages.append(msg)

        data = {
            'model': self.model_name,
            'input': {
                'messages': formatted_messages,
                'system': system_prompt
            },
            'parameters': {
                'temperature': self.temperature,
                'max_tokens': self.max_tokens
            }
        }

        response = requests.post(url, json=data, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()

        return result['output']['text']


class TencentClient(BaseModelClient):
    """腾讯混元模型客户端"""

    def __init__(self, api_key: str, model_name: str = 'hunyuan-pro', **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        self.api_base = 'https://hunyuan.tencentcloudapi.com'

    def chat(self, messages: list, stream: bool = False) -> str | Generator:
        """发送聊天请求"""
        import hmac
        import hashlib
        import time
        from datetime import datetime, timezone, timedelta

        # 生成签名
        timestamp = int(time.time())
        date = datetime.fromtimestamp(timestamp, tz=timezone(timedelta(hours=8))).strftime('%Y-%m-%d')

        def sign(secret_key, date):
            def _create_hash(hmac_str):
                return hmac.new(secret_key.encode('utf-8'), hmac_str.encode('utf-8'), hashlib.sha256).hexdigest()
            signature = _create_hash(f"date: {date}")
            return signature

        signature = sign(self.api_key, date)

        headers = {
            'Content-Type': 'application/json',
            'X-Date': date,
            'Authorization': f'HMAC256-SHA256 Credential={self.api_key}, SignedHeaders=date, Signature={signature}'
        }

        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            if msg['role'] != 'system':
                formatted_messages.append({'role': msg['role'], 'content': msg['content']})
            else:
                formatted_messages.insert(0, {'role': 'user', 'content': msg['content']})

        data = {
            'Model': self.model_name,
            'Messages': formatted_messages,
            'Temperature': self.temperature,
            'MaxTokens': self.max_tokens
        }

        # 简化版请求 - 使用API Key直接
        url = f"{self.api_base}?Action=ChatCompletions&Version=2023-09-01&Model={self.model_name}"
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.api_key}'}
        data = {
            'Messages': formatted_messages,
            'Temperature': self.temperature,
            'MaxTokens': self.max_tokens
        }

        response = requests.post(url, json=data, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()

        return result['Choices'][0]['Message']['Content']


class ZhipuClient(BaseModelClient):
    """智谱AI GLM模型客户端"""

    def __init__(self, api_key: str, model_name: str = 'glm-4', **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        self.api_base = 'https://open.bigmodel.cn/api/paas/v4'

    def chat(self, messages: list, stream: bool = False) -> str | Generator:
        """发送聊天请求"""
        url = f"{self.api_base}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                formatted_messages.insert(0, {'role': 'user', 'content': msg['content']})
            else:
                formatted_messages.append({'role': msg['role'], 'content': msg['content']})

        data = {
            'model': self.model_name,
            'messages': formatted_messages,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

        response = requests.post(url, json=data, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()

        return result['choices'][0]['message']['content']


class MoonshotClient(BaseModelClient):
    """月之暗面 Moonshot模型客户端"""

    def __init__(self, api_key: str, model_name: str = 'moonshot-v1-8k', **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        self.api_base = 'https://api.moonshot.cn/v1'

    def chat(self, messages: list, stream: bool = False) -> str | Generator:
        """发送聊天请求"""
        url = f"{self.api_base}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        data = {
            'model': self.model_name,
            'messages': messages,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

        response = requests.post(url, json=data, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()

        return result['choices'][0]['message']['content']


class YiClient(BaseModelClient):
    """零一万物 Yi模型客户端"""

    def __init__(self, api_key: str, model_name: str = 'yi-medium', **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        self.api_base = 'https://api.lingyiwanwu.com/v1'

    def chat(self, messages: list, stream: bool = False) -> str | Generator:
        """发送聊天请求"""
        url = f"{self.api_base}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        data = {
            'model': self.model_name,
            'messages': messages,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

        response = requests.post(url, json=data, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()

        return result['choices'][0]['message']['content']


class MiniMaxClient(BaseModelClient):
    """MiniMax 模型客户端"""

    def __init__(self, api_key: str, model_name: str = 'MiniMax-M2.5', **kwargs):
        super().__init__(api_key, model_name, **kwargs)
        self.api_base = 'https://api.minimax.chat/v1'

    def chat(self, messages: list, stream: bool = False) -> str | Generator:
        """发送聊天请求"""
        url = f"{self.api_base}/text/chatcompletion_v2"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        data = {
            'model': self.model_name,
            'messages': messages,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

        response = requests.post(url, json=data, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()

        return result['choices'][0]['message']['content']


# 提供商映射
PROVIDERS = {
    'openai': {'name': 'OpenAI', 'class': OpenAIClient, 'default_model': 'gpt-4'},
    'claude': {'name': 'Claude', 'class': ClaudeClient, 'default_model': 'claude-3-sonnet-20240229'},
    'baidu': {'name': '百度文心一言', 'class': BaiduClient, 'default_model': 'ernie-4.0-8k'},
    'alibaba': {'name': '阿里通义千问', 'class': AlibabaClient, 'default_model': 'qwen-turbo'},
    'tencent': {'name': '腾讯混元', 'class': TencentClient, 'default_model': 'hunyuan-pro'},
    'zhipu': {'name': '智谱AI', 'class': ZhipuClient, 'default_model': 'glm-4'},
    'moonshot': {'name': '月之暗面', 'class': MoonshotClient, 'default_model': 'moonshot-v1-8k'},
    'yi': {'name': '零一万物', 'class': YiClient, 'default_model': 'yi-medium'},
    'minimax': {'name': 'MiniMax', 'class': MiniMaxClient, 'default_model': 'MiniMax-M2.5'},
}


def get_model_client(provider: str, api_key: str, model_name: str, **kwargs) -> BaseModelClient:
    """
    获取模型客户端
    """
    provider_lower = provider.lower()
    if provider_lower in PROVIDERS:
        provider_info = PROVIDERS[provider_lower]
        return provider_info['class'](api_key, model_name, **kwargs)
    else:
        raise ValueError(f"不支持的模型提供商: {provider}")
