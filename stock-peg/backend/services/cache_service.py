"""
数据库缓存服务

功能：
1. 内存缓存常用查询结果
2. 减少 API 调用次数
3. 提高响应速度
4. 支持 TTL（Time To Live）
"""
import time
import logging
from typing import Any, Optional, Dict, Generic, TypeVar
from dataclasses import dataclass, field
from collections import OrderedDict
import hashlib
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheItem(Generic[T]):
    """缓存项"""
    value: T
    created_at: float = field(default_factory=time.time)
    ttl: Optional[float] = None  # Time to live in seconds
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl


class CacheService:
    """
    内存缓存服务
    
    使用 LRU (Least Recently Used) 策略管理缓存
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[float] = 300):
        """
        初始化缓存服务
        
        Args:
            max_size: 最大缓存项数
            default_ttl: 默认 TTL（秒），None 表示永不过期
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheItem] = OrderedDict()
        self._hits = 0
        self._misses = 0
    
    def _generate_key(self, *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键（MD5 哈希）
        """
        # 将参数序列化为字符串
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        
        # 生成 MD5 哈希
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        item = self._cache[key]
        
        # 检查是否过期
        if item.is_expired():
            del self._cache[key]
            self._misses += 1
            logger.debug(f"Cache expired: {key}")
            return None
        
        # 更新访问顺序（LRU）
        self._cache.move_to_end(key)
        self._hits += 1
        logger.debug(f"Cache hit: {key}")
        return item.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None
    ) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），None 表示使用默认 TTL
        """
        # 如果缓存已满，删除最旧的项
        if len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Cache evicted (LRU): {oldest_key}")
        
        # 使用提供的 TTL 或默认 TTL
        actual_ttl = ttl if ttl is not None else self.default_ttl
        
        # 添加到缓存
        self._cache[key] = CacheItem(
            value=value,
            ttl=actual_ttl
        )
        logger.debug(f"Cache set: {key}, TTL: {actual_ttl}s")
    
    def delete(self, key: str) -> bool:
        """
        删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")
            return True
        return False
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_items": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "total_requests": total_requests
        }
    
    def cleanup_expired(self) -> int:
        """
        清理过期的缓存项
        
        Returns:
            清理的项数
        """
        expired_keys = [
            key for key, item in self._cache.items()
            if item.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache items")
        
        return len(expired_keys)


# 装饰器：自动缓存函数结果
def cached(
    ttl: Optional[float] = 300,
    key_prefix: Optional[str] = None,
    cache_service: Optional[CacheService] = None
):
    """
    缓存装饰器
    
    自动缓存函数结果，下次调用时直接返回缓存值
    
    Args:
        ttl: TTL（秒）
        key_prefix: 缓存键前缀
        cache_service: 缓存服务实例（None 则使用全局实例）
    
    Example:
        @cached(ttl=60, key_prefix="stock_price")
        async def get_stock_price(stock_code: str) -> dict:
            # 从数据库或 API 获取数据
            return {...}
    """
    def decorator(func):
        _cache = cache_service or global_cache_service
        
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = _cache._generate_key(
                key_prefix or func.__name__,
                *args,
                **kwargs
            )
            
            # 尝试从缓存获取
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for function: {func.__name__}")
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            _cache.set(cache_key, result, ttl=ttl)
            logger.debug(f"Cached result for function: {func.__name__}")
            
            return result
        
        def sync_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = _cache._generate_key(
                key_prefix or func.__name__,
                *args,
                **kwargs
            )
            
            # 尝试从缓存获取
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for function: {func.__name__}")
                return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            _cache.set(cache_key, result, ttl=ttl)
            logger.debug(f"Cached result for function: {func.__name__}")
            
            return result
        
        # 根据函数类型返回不同的 wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 全局缓存服务实例
global_cache_service = CacheService(
    max_size=1000,
    default_ttl=300  # 5 分钟
)


# 便捷方法
def get_cache() -> CacheService:
    """获取全局缓存服务实例"""
    return global_cache_service


def cache_get(key: str) -> Optional[Any]:
    """从全局缓存获取值"""
    return global_cache_service.get(key)


def cache_set(key: str, value: Any, ttl: Optional[float] = None) -> None:
    """设置全局缓存值"""
    global_cache_service.set(key, value, ttl)


def cache_delete(key: str) -> bool:
    """删除全局缓存项"""
    return global_cache_service.delete(key)


def cache_clear() -> None:
    """清空全局缓存"""
    global_cache_service.clear()


def cache_stats() -> Dict[str, Any]:
    """获取全局缓存统计信息"""
    return global_cache_service.get_stats()
