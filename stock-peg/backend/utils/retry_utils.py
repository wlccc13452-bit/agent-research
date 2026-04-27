"""
Retry utilities for automatic retry with exponential backoff
"""
import asyncio
import functools
import logging
from typing import Callable, TypeVar, ParamSpec, Any, Optional
import random

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


def with_retry(
    max_retries: int = 3,
    base_backoff: float = 1.0,
    max_backoff: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,)
) -> Callable:
    """Retry decorator with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        base_backoff: Base backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        exponential_base: Base for exponential calculation
        jitter: Add random jitter to backoff
        retryable_exceptions: Tuple of exceptions to retry on
        
    Returns:
        Decorated function
    
    Example:
        @with_retry(max_retries=3, base_backoff=1.0)
        async def fetch_data():
            return await api_call()
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Final attempt failed, re-raise exception
                        logger.error(
                            f"[ERROR] {func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
                        raise
                    
                    # Calculate backoff time with exponential increase
                    backoff = min(
                        base_backoff * (exponential_base ** attempt),
                        max_backoff
                    )
                    
                    # Add jitter to avoid thundering herd
                    if jitter:
                        backoff = backoff * (0.5 + random.random())
                    
                    logger.warning(
                        f"[WARN]️ {func.__name__} attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {backoff:.2f}s..."
                    )
                    
                    await asyncio.sleep(backoff)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            else:
                raise RuntimeError(f"{func.__name__} failed without exception")
        
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Final attempt failed, re-raise exception
                        logger.error(
                            f"[ERROR] {func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
                        raise
                    
                    # Calculate backoff time
                    backoff = min(
                        base_backoff * (exponential_base ** attempt),
                        max_backoff
                    )
                    
                    # Add jitter
                    if jitter:
                        backoff = backoff * (0.5 + random.random())
                    
                    logger.warning(
                        f"[WARN]️ {func.__name__} attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {backoff:.2f}s..."
                    )
                    
                    import time
                    time.sleep(backoff)
            
            # Should never reach here
            if last_exception:
                raise last_exception
            else:
                raise RuntimeError(f"{func.__name__} failed without exception")
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def with_timeout(timeout: float) -> Callable:
    """Timeout decorator for async functions
    
    Args:
        timeout: Timeout in seconds
        
    Returns:
        Decorated function
    
    Example:
        @with_timeout(timeout=10.0)
        async def slow_operation():
            await asyncio.sleep(20)
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"⏱️ {func.__name__} timed out after {timeout}s")
                raise
        
        return wrapper
    
    return decorator


def with_fallback(fallback_value: Any = None, log_error: bool = True) -> Callable:
    """Fallback decorator that returns a default value on error
    
    Args:
        fallback_value: Value to return on error
        log_error: Whether to log the error
        
    Returns:
        Decorated function
    
    Example:
        @with_fallback(fallback_value={})
        async def get_data():
            return await risky_api_call()
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"[WARN]️ {func.__name__} failed, using fallback: {e}")
                return fallback_value
        
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"[WARN]️ {func.__name__} failed, using fallback: {e}")
                return fallback_value
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures
    
    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Failure threshold reached, requests blocked
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._state = "CLOSED"
        self._half_open_calls = 0
    
    def _should_allow_request(self) -> bool:
        """Check if request should be allowed"""
        import time
        current_time = time.time()
        
        if self._state == "CLOSED":
            return True
        
        elif self._state == "OPEN":
            # Check if recovery timeout has passed
            if current_time - self._last_failure_time >= self.recovery_timeout:
                self._state = "HALF_OPEN"
                self._half_open_calls = 0
                logger.info("🔄 Circuit breaker entering HALF_OPEN state")
                return True
            else:
                return False
        
        elif self._state == "HALF_OPEN":
            # Allow limited requests in half-open state
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            else:
                return False
        
        return False
    
    def _record_success(self) -> None:
        """Record successful request"""
        if self._state == "HALF_OPEN":
            # Service recovered, close circuit
            self._state = "CLOSED"
            self._failure_count = 0
            logger.info("[OK] Circuit breaker closed (service recovered)")
    
    def _record_failure(self) -> None:
        """Record failed request"""
        import time
        
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._state == "HALF_OPEN":
            # Service still failing, open circuit again
            self._state = "OPEN"
            logger.warning("[WARN]️ Circuit breaker opened again (service still failing)")
        
        elif self._state == "CLOSED":
            if self._failure_count >= self.failure_threshold:
                # Open circuit
                self._state = "OPEN"
                logger.warning(
                    f"🚨 Circuit breaker opened "
                    f"(failures: {self._failure_count}/{self.failure_threshold})"
                )
    
    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        """Decorate function with circuit breaker"""
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if not self._should_allow_request():
                raise Exception(
                    f"Circuit breaker is OPEN (service unavailable)"
                )
            
            try:
                result = await func(*args, **kwargs)
                self._record_success()
                return result
            except Exception as e:
                self._record_failure()
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if not self._should_allow_request():
                raise Exception(
                    f"Circuit breaker is OPEN (service unavailable)"
                )
            
            try:
                result = func(*args, **kwargs)
                self._record_success()
                return result
            except Exception as e:
                self._record_failure()
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    @property
    def state(self) -> str:
        """Get current circuit breaker state"""
        return self._state
    
    @property
    def stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            "state": self._state,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }


# Global circuit breakers for external services
_feishu_api_circuit_breaker: Optional[CircuitBreaker] = None
_database_circuit_breaker: Optional[CircuitBreaker] = None


def get_feishu_api_circuit_breaker() -> CircuitBreaker:
    """Get or create Feishu API circuit breaker"""
    global _feishu_api_circuit_breaker
    if _feishu_api_circuit_breaker is None:
        _feishu_api_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            half_open_max_calls=3
        )
    return _feishu_api_circuit_breaker


def get_database_circuit_breaker() -> CircuitBreaker:
    """Get or create database circuit breaker"""
    global _database_circuit_breaker
    if _database_circuit_breaker is None:
        _database_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30.0,
            half_open_max_calls=1
        )
    return _database_circuit_breaker
