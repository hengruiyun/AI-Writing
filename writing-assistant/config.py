"""
配置管理模块
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('config.env')

class Config:
    """应用配置类"""
    
    # LLM API配置
    LLM_API_URL = os.getenv('LLM_API_URL', 'http://localhost:8000')
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gpt-3.5-turbo')
    LLM_TIMEOUT = int(os.getenv('LLM_TIMEOUT', '30'))
    
    # 服务器配置
    SERVER_HOST = os.getenv('SERVER_HOST', '127.0.0.1')
    SERVER_PORT = int(os.getenv('SERVER_PORT', '8080'))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # 数据库配置
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///writing_assistant.db')
    
    # 应用配置
    AUTO_SAVE_INTERVAL = int(os.getenv('AUTO_SAVE_INTERVAL', '30'))
    MAX_WORD_COUNT = int(os.getenv('MAX_WORD_COUNT', '2000'))
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

def get_config():
    """获取配置实例"""
    return Config 