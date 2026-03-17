"""
配置文件
"""
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # 数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///restaurant_ai.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 默认AI模型配置
    DEFAULT_MODEL_PROVIDER = 'openai'
    DEFAULT_MODEL_NAME = 'gpt-4'

    # OpenAI配置
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

    # Claude配置
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')

    # 会话配置
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7天


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
