"""
快速LLM客户端
精简流程，2秒级响应，高性能优化
"""
import requests
import json
import time
import sys
import os
import threading
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 确保正确的导入路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 尝试多种导入方式
ModelProvider = None
LLMModel = None

# 方法1：直接从当前目录的models.py导入
try:
    sys.path.insert(0, current_dir)
    
    # 临时移除可能冲突的模块
    if 'models' in sys.modules:
        del sys.modules['models']
    
    # 直接导入models.py文件
    import importlib.util
    models_path = os.path.join(current_dir, 'models.py')
    
    if os.path.exists(models_path):
        spec = importlib.util.spec_from_file_location("models", models_path)
        models_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models_module)
        
        ModelProvider = models_module.ModelProvider
        LLMModel = models_module.LLMModel
        print(f"Successfully imported ModelProvider and LLMModel from {models_path}")
    else:
        raise ImportError(f"models.py not found at {models_path}")
        
except Exception as e:
    print(f"Method 1 failed: {e}")
    
    # 方法2：尝试从models包导入
    try:
        from models import ModelProvider, LLMModel
        print("Successfully imported from models package")
    except ImportError as e2:
        print(f"Method 2 failed: {e2}")
        
        # 降级方案：手动定义必要的类
        from enum import Enum
        from pydantic import BaseModel
        
        class ModelProvider(str, Enum):
            OPENAI = "OpenAI"
            OLLAMA = "Ollama"
            ANTHROPIC = "Anthropic"
            GOOGLE = "Google"
            LMSTUDIO = "LMStudio"
        
        class LLMModel(BaseModel):
            display_name: str
            model_name: str
            provider: ModelProvider
        
        print("Using fallback model definitions")

class FastLLMClient:
    """快速LLM客户端 - 高性能优化版本"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries
        self._session_cache = {}  # 为不同base_url缓存session
        self._lock = threading.Lock()
        
        # 创建默认session
        self._default_session = self._create_optimized_session()
    
    def _create_optimized_session(self) -> requests.Session:
        """创建优化的requests session"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        
        # 配置连接池适配器 - 增加连接池大小
        adapter = HTTPAdapter(
            pool_connections=20,
            pool_maxsize=50,
            max_retries=retry_strategy,
            pool_block=False
        )
        
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        # 设置默认headers
        session.headers.update({
            'User-Agent': 'FastLLMClient/1.0',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate'
        })
        
        return session
    
    def _get_session(self, base_url: str) -> requests.Session:
        """获取或创建针对特定base_url的session"""
        with self._lock:
            if base_url not in self._session_cache:
                self._session_cache[base_url] = self._create_optimized_session()
            return self._session_cache[base_url]
    
    def _build_context_prompt(self, prompt: str, grade: str = None, subject: str = None, 
                            topic: str = None, requirement: str = None) -> str:
        """构建包含上下文信息的提示词"""
        context_parts = []
        
        # 根据学科选择语言
        is_english = subject and "英语" in subject
        
        if grade:
            if is_english:
                context_parts.append(f"Grade: {grade}")
            else:
                context_parts.append(f"年级：{grade}")
        if subject:
            if is_english:
                context_parts.append(f"Subject: {subject}")
            else:
                context_parts.append(f"学科：{subject}")
        if topic:
            if is_english:
                context_parts.append(f"Essay Topic: {topic}")
            else:
                context_parts.append(f"作文题目：{topic}")
        if requirement:
            if is_english:
                context_parts.append(f"Requirements: {requirement}")
            else:
                context_parts.append(f"具体要求：{requirement}")
        
        if context_parts:
            if is_english:
                context = "[Context Information]\n" + "\n".join(context_parts) + "\n\n"
            else:
                context = "【上下文信息】\n" + "\n".join(context_parts) + "\n\n"
            return context + prompt
        
        return prompt
    
    def _call_openai_api(self, prompt: str, model: LLMModel, max_tokens: int = 1000, 
                        **kwargs) -> str:
        """调用OpenAI API - 优化版本"""
        base_url = getattr(model, 'base_url', None) or 'https://api.openai.com/v1'
        session = self._get_session(base_url)
        
        headers = {
            'Authorization': f'Bearer {getattr(model, "api_key", "")}',
            'Content-Type': 'application/json'
        }
        
        # 构建消息
        messages = [{'role': 'user', 'content': prompt}]
        
        # 如果有系统消息，添加到开头
        if kwargs.get('system_message'):
            messages.insert(0, {'role': 'system', 'content': kwargs['system_message']})
        
        data = {
            'model': model.model_name,
            'messages': messages,
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': max_tokens,
            'stream': False  # 禁用流式以提高速度
        }
        
        # 如果模型支持JSON模式且需要
        if kwargs.get('json_mode') and hasattr(model, 'has_json_mode') and model.has_json_mode():
            data['response_format'] = {'type': 'json_object'}
        
        url = urljoin(base_url.rstrip('/') + '/', 'chat/completions')
        response = session.post(url, json=data, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _call_ollama_api(self, prompt: str, model: LLMModel, max_tokens: int = 1000, 
                        **kwargs) -> str:
        """调用Ollama API - 优化版本"""
        base_url = getattr(model, 'base_url', None) or 'http://localhost:11434'
        session = self._get_session(base_url)
        
        # 构建完整提示词
        full_prompt = prompt
        if kwargs.get('system_message'):
            full_prompt = f"System: {kwargs['system_message']}\n\nUser: {prompt}"
        
        data = {
            'model': model.model_name,
            'prompt': full_prompt,
            'stream': False,
            'options': {
                'num_predict': max_tokens,
                'temperature': kwargs.get('temperature', 0.7),
                'top_p': kwargs.get('top_p', 0.9),
                'repeat_penalty': 1.1,
                'num_ctx': kwargs.get('context_window', 2048)
            }
        }
        
        # 如果模型支持JSON模式
        if kwargs.get('json_mode') and hasattr(model, 'has_json_mode') and model.has_json_mode():
            data['format'] = 'json'
        
        url = urljoin(base_url.rstrip('/') + '/', 'api/generate')
        response = session.post(url, json=data, timeout=self.timeout)
        response.raise_for_status()
        
        result = response.json()
        return result['response']
    
    def _call_anthropic_api(self, prompt: str, model: LLMModel, max_tokens: int = 1000, 
                          **kwargs) -> str:
        """调用Anthropic API - 优化版本"""
        base_url = getattr(model, 'base_url', None) or 'https://api.anthropic.com/v1'
        session = self._get_session(base_url)
        
        headers = {
            'x-api-key': getattr(model, 'api_key', ''),
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        # 构建消息
        messages = [{'role': 'user', 'content': prompt}]
        
        data = {
            'model': model.model_name,
            'max_tokens': max_tokens,
            'messages': messages,
            'temperature': kwargs.get('temperature', 0.7)
        }
        
        # 如果有系统消息
        if kwargs.get('system_message'):
            data['system'] = kwargs['system_message']
        
        url = urljoin(base_url.rstrip('/') + '/', 'messages')
        response = session.post(url, json=data, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        result = response.json()
        return result['content'][0]['text']
    
    def _call_google_api(self, prompt: str, model: LLMModel, max_tokens: int = 1000, 
                        **kwargs) -> str:
        """调用Google API - 优化版本"""
        base_url = getattr(model, 'base_url', None) or 'https://generativelanguage.googleapis.com/v1beta'
        session = self._get_session(base_url)
        
        # 构建完整提示词
        full_prompt = prompt
        if kwargs.get('system_message'):
            full_prompt = f"{kwargs['system_message']}\n\n{prompt}"
        
        data = {
            'contents': [{'parts': [{'text': full_prompt}]}],
            'generationConfig': {
                'temperature': kwargs.get('temperature', 0.7),
                'maxOutputTokens': max_tokens,
                'topP': kwargs.get('top_p', 0.9)
            }
        }
        
        api_key = getattr(model, 'api_key', '')
        url = f"{base_url.rstrip('/')}/models/{model.model_name}:generateContent?key={api_key}"
        
        response = session.post(url, json=data, timeout=self.timeout)
        response.raise_for_status()
        
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    
    def generate_response(self, prompt: str, model: LLMModel, max_tokens: int = 1000,
                         grade: str = None, subject: str = None, topic: str = None,
                         requirement: str = None, **kwargs) -> str:
        """生成响应 - 统一接口"""
        start_time = time.time()
        
        # 构建包含上下文的提示词
        context_prompt = self._build_context_prompt(prompt, grade, subject, topic, requirement)
        
        try:
            if model.provider == ModelProvider.OPENAI:
                response = self._call_openai_api(context_prompt, model, max_tokens, **kwargs)
            elif model.provider == ModelProvider.OLLAMA:
                response = self._call_ollama_api(context_prompt, model, max_tokens, **kwargs)
            elif model.provider == ModelProvider.ANTHROPIC:
                response = self._call_anthropic_api(context_prompt, model, max_tokens, **kwargs)
            elif model.provider == ModelProvider.GOOGLE:
                response = self._call_google_api(context_prompt, model, max_tokens, **kwargs)
            elif model.provider == ModelProvider.LMSTUDIO:
                # LMStudio使用OpenAI兼容API
                response = self._call_openai_api(context_prompt, model, max_tokens, **kwargs)
            else:
                raise ValueError(f"不支持的模型供应商: {model.provider}")
            
            elapsed_time = time.time() - start_time
            print(f"API调用耗时: {elapsed_time:.2f}秒")
            
            return response.strip()
            
        except requests.exceptions.Timeout:
            raise Exception("API调用超时")
        except requests.exceptions.ConnectionError:
            raise Exception("无法连接到API服务")
        except requests.exceptions.HTTPError as e:
            error_msg = f"API调用失败: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {e.response.text}"
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(f"生成响应失败: {str(e)}")
    
    def test_connection(self, model: LLMModel) -> bool:
        """测试连接"""
        try:
            response = self.generate_response("Hello", model, max_tokens=10)
            return len(response) > 0
        except:
            return False
    
    def batch_generate(self, prompts: List[str], model: LLMModel, max_tokens: int = 1000,
                      **kwargs) -> List[str]:
        """批量生成响应 - 并发处理"""
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self.generate_response, prompt, model, max_tokens, **kwargs)
                for prompt in prompts
            ]
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(f"错误: {str(e)}")
            
            return results
    
    def __del__(self):
        """清理资源"""
        # 清理所有session
        if hasattr(self, '_session_cache'):
            for session in self._session_cache.values():
                session.close()
        if hasattr(self, '_default_session'):
            self._default_session.close()

# 全局快速客户端实例
fast_client = FastLLMClient(timeout=30)

def quick_generate(prompt: str, model: LLMModel, max_tokens: int = 1000,
                  grade: str = None, subject: str = None, topic: str = None,
                  requirement: str = None, **kwargs) -> str:
    """快速生成响应 - 统一接口"""
    return fast_client.generate_response(
        prompt, model, max_tokens, grade, subject, topic, requirement, **kwargs
    )

def quick_test(model: LLMModel) -> bool:
    """快速测试连接"""
    return fast_client.test_connection(model)

def quick_batch_generate(prompts: List[str], model: LLMModel, max_tokens: int = 1000,
                        **kwargs) -> List[str]:
    """快速批量生成"""
    return fast_client.batch_generate(prompts, model, max_tokens, **kwargs)