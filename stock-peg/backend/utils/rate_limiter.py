"""
Rate limiter for API calls with concurrency control
"""
import asyncio
import time
import logging
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter with both request rate and concurrency control
    
    Features:
    - Minimum interval between requests
    - Maximum concurrent requests
    - Request queue with timeout
    - Adaptive backoff on failures
    """
    
    def __init__(
        self,
        min_interval: float = 0.5,
        max_concurrent: int = 3,
        timeout: float = 30.0
    ):
        """Initialize rate limiter
        
        Args:
            min_interval: Minimum seconds between requests
            max_concurrent: Maximum concurrent requests
            timeout: Maximum wait time in queue
        """
        self.min_interval = min_interval
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._last_request_time = 0.0
        self._lock = asyncio.Lock()
        self._failure_count = 0
        self._adaptive_interval = min_interval
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire rate limiter slot with automatic release"""
        start_time = time.time()
        
        # Wait for semaphore (concurrency control)
        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            logger.warning(
                f"⏱️ Rate limiter queue timeout after {self.timeout}s"
            )
            raise
        
        try:
            # Enforce minimum interval between requests
            async with self._lock:
                elapsed = time.time() - self._last_request_time
                wait_time = max(0, self._adaptive_interval - elapsed)
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                
                self._last_request_time = time.time()
            
            yield
            
        finally:
            self._semaphore.release()
    
    def record_success(self):
        """Record successful request - reduce adaptive interval"""
        self._failure_count = max(0, self._failure_count - 1)
        
        # Gradually reduce adaptive interval on success
        if self._adaptive_interval > self.min_interval:
            self._adaptive_interval = max(
                self.min_interval,
                self._adaptive_interval * 0.9
            )
            logger.debug(
                f"[OK] Rate limiter success, interval reduced to "
                f"{self._adaptive_interval:.2f}s"
            )
    
    def record_failure(self):
        """Record failed request - increase adaptive interval"""
        self._failure_count += 1
        
        # Increase adaptive interval on failure (max 5x original)
        self._adaptive_interval = min(
            self.min_interval * 5,
            self._adaptive_interval * 1.5
        )
        
        logger.warning(
            f"[WARN]️ Rate limiter failure #{self._failure_count}, "
            f"interval increased to {self._adaptive_interval:.2f}s"
        )
    
    @property
    def stats(self) -> dict:
        """Get rate limiter statistics"""
        return {
            "min_interval": self.min_interval,
            "adaptive_interval": self._adaptive_interval,
            "max_concurrent": self.max_concurrent,
            "failure_count": self._failure_count,
            "available_slots": self._semaphore._value,
        }


# Global rate limiters for different services
_akshare_rate_limiter: Optional[RateLimiter] = None
_tushare_rate_limiter: Optional[RateLimiter] = None


def get_akshare_rate_limiter() -> RateLimiter:
    """Get or create Akshare rate limiter
    
    Configuration (from config/console_output.ini):
    - Min interval: min_request_interval
    - Max concurrent: max_concurrent_requests
    - Timeout: request_queue_timeout
    """
    global _akshare_rate_limiter
    if _akshare_rate_limiter is None:
        # 从配置文件读取参数
        try:
            from configparser import ConfigParser
            from pathlib import Path
            
            config_file = Path(__file__).parent.parent / "config" / "console_output.ini"
            config = ConfigParser()
            config.read(config_file, encoding='utf-8')
            
            min_interval = config.getfloat(
                'akshare_rate_limit',
                'min_request_interval',
                fallback=1.0
            )
            max_concurrent = config.getint(
                'akshare_rate_limit',
                'max_concurrent_requests',
                fallback=2
            )
            timeout = config.getfloat(
                'akshare_rate_limit',
                'request_queue_timeout',
                fallback=30.0
            )
        except Exception as e:
            logger.warning(f"Failed to read rate limiter config: {e}, using defaults")
            min_interval = 1.0
            max_concurrent = 2
            timeout = 30.0
        
        _akshare_rate_limiter = RateLimiter(
            min_interval=min_interval,
            max_concurrent=max_concurrent,
            timeout=timeout
        )
        logger.info(
            f"🔒 Akshare rate limiter initialized "
            f"(interval={min_interval}s, concurrent={max_concurrent})"
        )
    return _akshare_rate_limiter


def get_tushare_rate_limiter() -> RateLimiter:
    """Get or create Tushare rate limiter
    
    Configuration:
    - Min interval: 0.2s (5 requests per second max)
    - Max concurrent: 5 requests
    - Timeout: 30s
    """
    global _tushare_rate_limiter
    if _tushare_rate_limiter is None:
        _tushare_rate_limiter = RateLimiter(
            min_interval=0.2,
            max_concurrent=5,
            timeout=30.0
        )
        logger.info(
            "🔒 Tushare rate limiter initialized "
            f"(interval=0.2s, concurrent=5)"
        )
    return _tushare_rate_limiter
