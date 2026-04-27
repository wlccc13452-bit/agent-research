"""
K线数据内存缓存服务
立即生效的性能优化方案
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import asyncio

logger = logging.getLogger(__name__)


class KLineMemoryCache:
    """
    K线数据内存缓存
    
    特性:
    - TTL过期机制（默认5分钟）
    - 线程安全
    - 自动清理过期数据
    """
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        """
        初始化缓存
        
        Args:
            ttl_seconds: 缓存过期时间（秒），默认300秒（5分钟）
            max_size: 最大缓存条目数，默认100只股票
        """
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
        
        logger.info(f"[OK] K线内存缓存初始化: TTL={ttl_seconds}s, MaxSize={max_size}")
    
    def _make_key(self, stock_code: str, period: str = "day", count: int = 100) -> str:
        """生成缓存键"""
        return f"{stock_code}:{period}:{count}"
    
    async def get(self, stock_code: str, period: str = "day", count: int = 100) -> Optional[List[Dict]]:
        """
        获取缓存数据
        
        Args:
            stock_code: 股票代码
            period: K线周期
            count: 数据条数
            
        Returns:
            缓存的K线数据列表，如果不存在或已过期则返回None
        """
        key = self._make_key(stock_code, period, count)
        
        async with self._lock:
            self.stats['total_requests'] += 1
            
            if key not in self.cache:
                self.stats['misses'] += 1
                logger.debug(f"缓存未命中: {key}")
                return None
            
            entry = self.cache[key]
            
            # 检查是否过期
            if datetime.now() > entry['expires_at']:
                # 已过期，删除
                del self.cache[key]
                self.stats['misses'] += 1
                self.stats['evictions'] += 1
                logger.debug(f"缓存已过期: {key}")
                return None
            
            # 缓存命中
            self.stats['hits'] += 1
            entry['last_access'] = datetime.now()
            hit_rate = self.stats['hits'] / self.stats['total_requests'] * 100
            
            logger.info(f"[TARGET] 缓存命中: {key}, 命中率: {hit_rate:.1f}%, 当前缓存大小: {len(self.cache)}")
            
            return entry['data']
    
    async def set(self, stock_code: str, data: List[Dict], period: str = "day", count: int = 100):
        """
        设置缓存数据
        
        Args:
            stock_code: 股票代码
            data: K线数据列表
            period: K线周期
            count: 数据条数
        """
        key = self._make_key(stock_code, period, count)
        
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
            
            logger.info(f"💾 缓存已设置: {key}, 数据条数: {len(data)}, 缓存大小: {len(self.cache)}/{self.max_size}")
    
    async def _evict_oldest(self):
        """淘汰最旧的缓存条目"""
        if not self.cache:
            return
        
        # 找到最旧的条目（按最后访问时间）
        oldest_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k]['last_access']
        )
        
        del self.cache[oldest_key]
        self.stats['evictions'] += 1
        logger.debug(f"缓存已淘汰: {oldest_key}")
    
    async def clear_expired(self):
        """清理所有过期缓存"""
        async with self._lock:
            expired_keys = [
                k for k, v in self.cache.items()
                if datetime.now() > v['expires_at']
            ]
            
            for key in expired_keys:
                del self.cache[key]
                self.stats['evictions'] += 1
            
            if expired_keys:
                logger.info(f"🧹 清理过期缓存: {len(expired_keys)} 条")
    
    async def clear_all(self):
        """清空所有缓存"""
        async with self._lock:
            count = len(self.cache)
            self.cache.clear()
            logger.info(f"🗑️  清空所有缓存: {count} 条")
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        total = self.stats['total_requests']
        if total == 0:
            hit_rate = 0
        else:
            hit_rate = self.stats['hits'] / total * 100
        
        return {
            'total_requests': total,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'hit_rate': hit_rate,
            'cache_size': len(self.cache),
            'max_size': self.max_size
        }
    
    def print_stats(self):
        """打印缓存统计信息"""
        stats = self.get_stats()
        print("\n" + "="*60)
        print("[CHART] 缓存统计信息")
        print("="*60)
        print(f"总请求数: {stats['total_requests']}")
        print(f"缓存命中: {stats['hits']}")
        print(f"缓存未命中: {stats['misses']}")
        print(f"缓存淘汰: {stats['evictions']}")
        print(f"命中率: {stats['hit_rate']:.1f}%")
        print(f"缓存大小: {stats['cache_size']}/{stats['max_size']}")
        print("="*60)


# 全局单例实例
kline_cache = KLineMemoryCache(ttl_seconds=300, max_size=100)
