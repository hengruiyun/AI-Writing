# -*- coding: utf-8 -*-
"""
LLM分析模型包
"""

# 导入分析模型
try:
    from .analysis_models import *
except ImportError:
    pass

# 从父目录的models.py导入核心模型类和函数
try:
    import sys
    import os
    
    # 添加父目录到路径
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # 导入核心模型
    from models import (
        ModelProvider,
        LLMModel, 
        get_model_info,
        list_all_models,
        get_models_by_provider,
        load_models_from_json
    )
    
except ImportError as e:
    # 如果无法导入，则定义基本的枚举和类
    from enum import Enum
    from typing import Optional, List
    
    class ModelProvider(str, Enum):
        OPENAI = "OpenAI"
        ANTHROPIC = "Anthropic"
        GROQ = "Groq"
        DEEPSEEK = "DeepSeek"
        GEMINI = "Gemini"
        OLLAMA = "Ollama"
        LMSTUDIO = "LMStudio"
    
    class LLMModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def get_model_info(model_name: str, provider: Optional[str] = None) -> Optional[LLMModel]:
        return None
    
    def list_all_models() -> List[LLMModel]:
        return []
    
    def get_models_by_provider(provider: ModelProvider) -> List[LLMModel]:
        return []
    
    def load_models_from_json(json_path: str) -> List[LLMModel]:
        return []

__all__ = [
    'RiskLevel',
    'TrendDirection', 
    'InvestmentAction',
    'MarketSentiment',
    'MarketAnalysis',
    'SectorAnalysis',
    'StockRecommendation',
    'RiskManagement',
    'TimeframeOutlook',
    'StructuredAnalysisResult',
    'MultiPerspectiveAnalysis',
    'QuickAnalysisResult',
    'ModelProvider',
    'LLMModel',
    'get_model_info',
    'list_all_models',
    'get_models_by_provider',
    'load_models_from_json'
]