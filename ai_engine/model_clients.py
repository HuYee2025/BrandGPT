"""
AI模型客户端 - 支持多种大模型
"""
import json
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


def get_model_client(provider: str, api_key: str, model_name: str, **kwargs) -> BaseModelClient:
    """
    获取模型客户端
    provider: 'openai' 或 'claude'
    """
    if provider.lower() == 'openai':
        return OpenAIClient(api_key, model_name, **kwargs)
    elif provider.lower() == 'claude':
        return ClaudeClient(api_key, model_name, **kwargs)
    else:
        raise ValueError(f"不支持的模型提供商: {provider}")
