"""
AI引擎模块
"""
from .model_clients import OpenAIClient, ClaudeClient, get_model_client
from .prompt_templates import (
    SYSTEM_PROMPT,
    generate_question_prompt,
    generate_report_prompt,
    get_initial_question,
    DIMENSIONS
)

__all__ = [
    'OpenAIClient',
    'ClaudeClient',
    'get_model_client',
    'SYSTEM_PROMPT',
    'generate_question_prompt',
    'generate_report_prompt',
    'get_initial_question',
    'DIMENSIONS'
]
