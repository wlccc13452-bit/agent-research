"""
扩展数据内存缓存服务
用于PMR、财务数据、指数数据
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import logging
import asyncio

logger = logging.getLogger(__name__)


class GenericMemoryCache:
    """
    通用内存缓存类
    可用于各种数据类型
    """
    
    def __init__(self, name: str, ttl_seconds: int = 300, max_size: int = 100):
        """
        初始化缓存
        
        Args:
            name: 缓存名称（用于日志）
            ttl_seconds: 缓存过期时间（秒）
            max_size: 最大缓存条目数
        """
        self.name = name
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._lock = asyncio.Lock()
        
        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
        
        logger.info(f"[OK] {name}缓存初始化: TTL={ttl_seconds}s, MaxSize={max_size}")
    
    def _make_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        return ":".join(key_parts)
    
    async def get(self, *args, **kwargs) -> Optional[Any]:
        """获取缓存数据"""
        key = self._make_key(*args, **kwargs)
        
        async with self._lock:
            self.stats['total_requests'] += 1
            
            if key not in self.cache:
                self.stats['misses'] += 1
                logger.debug(f"{self.name}缓存未命中: {key}")
                return None
            
            entry = self.cache[key]
            
            # 检查是否过期
            if datetime.now() > entry['expires_at']:
                del self.cache[key]
                self.stats['misses'] += 1
                self.stats['evictions'] += 1
                logger.debug(f"{self.name}缓存已过期: {key}")
                return None
            
            # 缓存命中
            self.stats['hits'] += 1
            entry['last_access'] = datetime.now()
            hit_rate = self.stats['hits'] / self.stats['total_requests'] * 100
            
            logger.info(f"[TARGET] {self.name}缓存命中: {key}, 命中率: {hit_rate:.1f}%")
            
            return entry['data']
    
    async def set(self, data: Any, *args, **kwargs):
        """设置缓存数据"""
        key = self._make_key(*args, **kwargs)
        
        async with self._lock:
            # 检查缓存大小，如果超过限制则清理最旧的条目
            if len(self.cache) >= self.max_size:
                await self._evict_oldest()
            
            self.cache[key] = {
                'data': data,
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(seconds=self.ttl),
                'last_access': datetime.now()
            }
            
            logger.info(f"💾 {self.name}缓存已设置: {key}, 缓存大小: {len(self.cache)}/{self.max_size}")
    
    async def delete(self, *args, **kwargs):
        """删除缓存数据"""
        key = self._make_key(*args, **kwargs)
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                logger.info(f"🗑️ {self.name}缓存已删除: {key}")
                return True
            return False
    
    async def clear(self):
        """清空所有缓存数据"""
        async with self._lock:
            self.cache.clear()
            logger.info(f"🧹 {self.name}缓存已清空")
            return True
    
    async def _evict_oldest(self):
        """淘汰最旧的缓存条目"""
        if not self.cache:
            return
        
        oldest_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k]['last_access']
        )
        
        del self.cache[oldest_key]
        self.stats['evictions'] += 1
        logger.debug(f"{self.name}缓存已淘汰: {oldest_key}")
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        total = self.stats['total_requests']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'name': self.name,
            'total_requests': total,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'hit_rate': hit_rate,
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'ttl_seconds': self.ttl
        }


# ==================== 各类数据缓存实例 ====================

# PMR数据缓存（24小时过期，因为PMR计算稳定且基于历史数据）
pmr_cache = GenericMemoryCache("PMR数据", ttl_seconds=86400, max_size=500)

# 财务指标缓存（1天过期，财务数据更新频率低）
financial_metrics_cache = GenericMemoryCache("财务指标", ttl_seconds=86400, max_size=100)

# 财务分析缓存（1天过期）
financial_analysis_cache = GenericMemoryCache("财务分析", ttl_seconds=86400, max_size=100)

# 指数列表缓存（10分钟过期）
index_list_cache = GenericMemoryCache("指数列表", ttl_seconds=600, max_size=10)

# 技术指标缓存（1小时过期，技术指标变化相对稳定）
technical_cache = GenericMemoryCache("技术指标", ttl_seconds=3600, max_size=200)

# 实时行情缓存（1分钟过期，平衡实时性和性能）
quote_cache = GenericMemoryCache("实时行情", ttl_seconds=60, max_size=500)


# ==================== 缓存装饰器 ====================

def cached(cache_instance: GenericMemoryCache):
    """
    缓存装饰器
    
    用法:
    @cached(pmr_cache)
    async def get_pmr(stock_code: str, days: int = 120):
        ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 尝试从缓存获取
            cached_data = await cache_instance.get(*args, **kwargs)
            if cached_data is not None:
                return cached_data
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            if result is not None:
                await cache_instance.set(result, *args, **kwargs)
            
            return result
        
        return wrapper
    return decorator
