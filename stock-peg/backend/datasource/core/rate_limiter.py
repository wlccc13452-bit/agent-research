"""统一速率限制器"""
import asyncio
import time
import logging
from typing import Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class UnifiedRateLimiter:
    """统一速率限制器 — 按数据源类型独立限速"""

    def __init__(self, default_interval=0.5, default_concurrent=3):
        self._default_interval = default_interval
        self._default_concurrent = default_concurrent
        self._intervals: Dict[str, float] = {}
        self._concurrents: Dict[str, int] = {}
        self._semaphores: Dict[str, asyncio.Semaphore] = {}
        self._last_request_time: Dict[str, float] = defaultdict(float)

    def configure(self, source_type: str, interval=None, concurrent=None):
        if interval is not None:
            self._intervals[source_type] = interval
        if concurrent is not None:
            self._concurrents[source_type] = concurrent
            self._semaphores[source_type] = asyncio.Semaphore(concurrent)

    def _get_interval(self, source_type: str) -> float:
        return self._intervals.get(source_type, self._default_interval)

    def _get_semaphore(self, source_type: str) -> asyncio.Semaphore:
        if source_type not in self._semaphores:
            c = self._concurrents.get(source_type, self._default_concurrent)
            self._semaphores[source_type] = asyncio.Semaphore(c)
        return self._semaphores[source_type]

    async def acquire(self, source_type: str):
        sem = self._get_semaphore(source_type)
        await sem.acquire()
        try:
            interval = self._get_interval(source_type)
            elapsed = time.time() - self._last_request_time[source_type]
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)
            self._last_request_time[source_type] = time.time()
        except Exception:
            sem.release()
            raise

    def release(self, source_type: str):
        sem = self._semaphores.get(source_type)
        if sem:
            sem.release()


# 全局单例
unified_rate_limiter = UnifiedRateLimiter(default_interval=0.5, default_concurrent=3)
unified_rate_limiter.configure("tushare", interval=0.5, concurrent=2)
unified_rate_limiter.configure("akshare", interval=1.0, concurrent=3)
unified_rate_limiter.configure("tencent", interval=0.3, concurrent=5)
unified_rate_limiter.configure("eastmoney", interval=0.3, concurrent=5)
