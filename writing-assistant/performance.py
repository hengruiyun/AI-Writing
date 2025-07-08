"""
性能监控和优化模块
"""
import time
import functools
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.request_times = deque(maxlen=1000)  # 保留最近1000次请求
        self.api_calls = defaultdict(int)
        self.error_count = defaultdict(int)
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }
        self._lock = threading.Lock()
    
    def record_request(self, endpoint: str, duration: float, status_code: int):
        """记录请求性能"""
        with self._lock:
            self.metrics[endpoint].append({
                'duration': duration,
                'timestamp': datetime.utcnow(),
                'status_code': status_code
            })
            self.request_times.append(duration)
            self.api_calls[endpoint] += 1
            
            if status_code >= 400:
                self.error_count[endpoint] += 1
    
    def record_cache_hit(self):
        """记录缓存命中"""
        with self._lock:
            self.cache_stats['hits'] += 1
            self.cache_stats['total_requests'] += 1
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        with self._lock:
            self.cache_stats['misses'] += 1
            self.cache_stats['total_requests'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        with self._lock:
            total_requests = len(self.request_times)
            avg_response_time = sum(self.request_times) / total_requests if total_requests > 0 else 0
            
            # 计算缓存命中率
            cache_hit_rate = 0
            if self.cache_stats['total_requests'] > 0:
                cache_hit_rate = self.cache_stats['hits'] / self.cache_stats['total_requests'] * 100
            
            # 计算错误率
            total_api_calls = sum(self.api_calls.values())
            total_errors = sum(self.error_count.values())
            error_rate = (total_errors / total_api_calls * 100) if total_api_calls > 0 else 0
            
            return {
                'total_requests': total_requests,
                'average_response_time': round(avg_response_time, 3),
                'cache_hit_rate': round(cache_hit_rate, 2),
                'error_rate': round(error_rate, 2),
                'api_calls': dict(self.api_calls),
                'error_count': dict(self.error_count),
                'cache_stats': self.cache_stats.copy()
            }
    
    def get_slow_endpoints(self, threshold: float = 1.0) -> Dict[str, float]:
        """获取慢接口"""
        slow_endpoints = {}
        
        with self._lock:
            for endpoint, records in self.metrics.items():
                if records:
                    avg_time = sum(r['duration'] for r in records) / len(records)
                    if avg_time > threshold:
                        slow_endpoints[endpoint] = round(avg_time, 3)
        
        return dict(sorted(slow_endpoints.items(), key=lambda x: x[1], reverse=True))

# 全局性能监控实例
performance_monitor = PerformanceMonitor()

def monitor_performance(func: Callable) -> Callable:
    """性能监控装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            status_code = getattr(result, 'status_code', 200)
        except Exception as e:
            status_code = 500
            logger.error(f"Function {func.__name__} failed: {e}")
            raise
        finally:
            duration = time.time() - start_time
            performance_monitor.record_request(func.__name__, duration, status_code)
        
        return result
    
    return wrapper

class SimpleCache:
    """简单的内存缓存"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl  # 生存时间（秒）
        self.cache = {}
        self.access_times = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self.cache:
                # 检查是否过期
                if time.time() - self.access_times[key] < self.ttl:
                    self.access_times[key] = time.time()  # 更新访问时间
                    performance_monitor.record_cache_hit()
                    return self.cache[key]
                else:
                    # 过期，删除
                    del self.cache[key]
                    del self.access_times[key]
            
            performance_monitor.record_cache_miss()
            return None
    
    def set(self, key: str, value: Any):
        """设置缓存值"""
        with self._lock:
            # 如果缓存满了，删除最老的条目
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[key] = value
            self.access_times[key] = time.time()
    
    def delete(self, key: str):
        """删除缓存值"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                del self.access_times[key]
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self.cache.clear()
            self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_rate': performance_monitor.cache_stats['hits'] / max(performance_monitor.cache_stats['total_requests'], 1) * 100
            }

# 全局缓存实例
cache = SimpleCache()

def cached(ttl: int = 3600, key_func: Optional[Callable] = None):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator

class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self):
        self.query_stats = defaultdict(list)
        self._lock = threading.Lock()
    
    def record_query(self, query: str, duration: float):
        """记录查询性能"""
        with self._lock:
            self.query_stats[query].append({
                'duration': duration,
                'timestamp': datetime.utcnow()
            })
    
    def get_slow_queries(self, threshold: float = 0.5) -> Dict[str, float]:
        """获取慢查询"""
        slow_queries = {}
        
        with self._lock:
            for query, records in self.query_stats.items():
                if records:
                    avg_time = sum(r['duration'] for r in records) / len(records)
                    if avg_time > threshold:
                        slow_queries[query] = round(avg_time, 3)
        
        return dict(sorted(slow_queries.items(), key=lambda x: x[1], reverse=True))
    
    def optimize_suggestions(self) -> list:
        """获取优化建议"""
        suggestions = []
        slow_queries = self.get_slow_queries()
        
        if slow_queries:
            suggestions.append("发现慢查询，建议添加索引或优化查询语句")
        
        cache_hit_rate = performance_monitor.cache_stats['hits'] / max(performance_monitor.cache_stats['total_requests'], 1) * 100
        if cache_hit_rate < 80:
            suggestions.append("缓存命中率较低，建议优化缓存策略")
        
        error_rate = sum(performance_monitor.error_count.values()) / max(sum(performance_monitor.api_calls.values()), 1) * 100
        if error_rate > 5:
            suggestions.append("错误率较高，建议检查错误处理逻辑")
        
        return suggestions

# 全局数据库优化器
db_optimizer = DatabaseOptimizer()

def optimize_query(func: Callable) -> Callable:
    """查询优化装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
        finally:
            duration = time.time() - start_time
            db_optimizer.record_query(func.__name__, duration)
        
        return result
    
    return wrapper

class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self):
        self.memory_usage = deque(maxlen=100)
        self.cpu_usage = deque(maxlen=100)
        self._lock = threading.Lock()
    
    def record_memory_usage(self, usage: float):
        """记录内存使用率"""
        with self._lock:
            self.memory_usage.append({
                'usage': usage,
                'timestamp': datetime.utcnow()
            })
    
    def record_cpu_usage(self, usage: float):
        """记录CPU使用率"""
        with self._lock:
            self.cpu_usage.append({
                'usage': usage,
                'timestamp': datetime.utcnow()
            })
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """获取资源统计"""
        with self._lock:
            memory_avg = sum(r['usage'] for r in self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
            cpu_avg = sum(r['usage'] for r in self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
            
            return {
                'memory_usage_avg': round(memory_avg, 2),
                'cpu_usage_avg': round(cpu_avg, 2),
                'memory_samples': len(self.memory_usage),
                'cpu_samples': len(self.cpu_usage)
            }

# 全局资源监控器
resource_monitor = ResourceMonitor()

def get_system_performance() -> Dict[str, Any]:
    """获取系统性能概览"""
    return {
        'performance': performance_monitor.get_stats(),
        'cache': cache.get_stats(),
        'database': {
            'slow_queries': db_optimizer.get_slow_queries(),
            'optimization_suggestions': db_optimizer.optimize_suggestions()
        },
        'resources': resource_monitor.get_resource_stats(),
        'timestamp': datetime.utcnow().isoformat()
    }

def optimize_application():
    """应用优化建议"""
    stats = get_system_performance()
    suggestions = []
    
    # 性能建议
    if stats['performance']['average_response_time'] > 1.0:
        suggestions.append("平均响应时间较长，建议优化接口性能")
    
    if stats['performance']['error_rate'] > 5:
        suggestions.append("错误率较高，建议检查错误处理")
    
    # 缓存建议
    if stats['cache']['hit_rate'] < 80:
        suggestions.append("缓存命中率较低，建议优化缓存策略")
    
    # 数据库建议
    suggestions.extend(stats['database']['optimization_suggestions'])
    
    return suggestions

# 性能监控中间件
class PerformanceMiddleware:
    """Flask性能监控中间件"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # 添加性能统计路由
        @app.route('/api/performance')
        def performance_stats():
            return get_system_performance()
    
    def before_request(self):
        """请求前处理"""
        from flask import g
        g.start_time = time.time()
    
    def after_request(self, response):
        """请求后处理"""
        from flask import g, request
        
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            performance_monitor.record_request(
                request.endpoint or 'unknown',
                duration,
                response.status_code
            )
        
        return response 