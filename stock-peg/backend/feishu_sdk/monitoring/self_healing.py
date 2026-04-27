"""
Self Healing - 自愈机制模块

负责长连接的自愈功能：
- 连接重启管理
- 指数退避重试
- 重启计数和限制
"""

import asyncio
import logging
import threading
import time
from typing import Optional, Callable, Any, Awaitable

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_MAX_RESTART_ATTEMPTS = 5
DEFAULT_RESTART_BACKOFF_BASE = 2.0  # 秒


class SelfHealingManager:
    """
    自愈管理器
    
    负责监控连接状态并自动重启失败的连接。
    使用指数退避策略避免频繁重启。
    """
    
    def __init__(
        self,
        max_restart_attempts: int = DEFAULT_MAX_RESTART_ATTEMPTS,
        restart_backoff_base: float = DEFAULT_RESTART_BACKOFF_BASE
    ):
        """
        初始化自愈管理器
        
        Args:
            max_restart_attempts: 最大重启尝试次数
            restart_backoff_base: 指数退避基数（秒）
        """
        self._restart_count: int = 0
        self._last_restart_time: float = 0.0
        self._max_restart_attempts = max_restart_attempts
        self._restart_backoff_base = restart_backoff_base
        self._restart_lock = threading.Lock()
        self._running = False
        
        # 回调函数
        self._restart_callback: Optional[Callable[[], None]] = None
        self._is_alive_callback: Optional[Callable[[], bool]] = None
    
    def set_restart_callback(self, callback: Callable[[], None]) -> None:
        """
        设置重启回调函数
        
        Args:
            callback: 重启连接的函数
        """
        self._restart_callback = callback
    
    def set_is_alive_callback(self, callback: Callable[[], bool]) -> None:
        """
        设置连接存活检查回调函数
        
        Args:
            callback: 检查连接是否存活的函数
        """
        self._is_alive_callback = callback
    
    def can_restart(self) -> bool:
        """
        检查是否可以重启
        
        Returns:
            True 如果可以重启
        """
        with self._restart_lock:
            # 检查是否超过最大重启次数
            if self._restart_count >= self._max_restart_attempts:
                logger.error(
                    f"[ERROR] 已达到最大重启次数 ({self._max_restart_attempts})，停止自动重启"
                )
                return False
            
            # 检查是否在退避时间内
            current_time = time.time()
            delay = self._restart_backoff_base ** self._restart_count
            
            if current_time - self._last_restart_time < delay:
                logger.info(
                    f"⏳ 等待退避时间: {delay:.1f}s "
                    f"(重启次数: {self._restart_count}/{self._max_restart_attempts})"
                )
                return False
            
            return True
    
    def get_restart_delay(self) -> float:
        """
        获取当前重启延迟（指数退避）
        
        Returns:
            重启延迟（秒）
        """
        with self._restart_lock:
            return self._restart_backoff_base ** self._restart_count
    
    def record_restart(self) -> None:
        """记录重启事件"""
        with self._restart_lock:
            self._restart_count += 1
            self._last_restart_time = time.time()
            logger.info(f"🔄 记录重启事件 (累计重启: {self._restart_count} 次)")
    
    def reset_restart_count(self) -> None:
        """重置重启计数器"""
        with self._restart_lock:
            if self._restart_count > 0:
                logger.info(f"[OK] 连接稳定，重置重启计数器 (原计数: {self._restart_count})")
            self._restart_count = 0
    
    def attempt_restart(self) -> bool:
        """
        尝试重启连接（同步版本）
        
        Returns:
            True 如果重启成功
        """
        if not self.can_restart():
            return False
        
        if not self._restart_callback:
            logger.error("未设置重启回调函数")
            return False
        
        try:
            delay = self.get_restart_delay()
            logger.info(
                f"🔄 尝试重启连接 "
                f"(第 {self._restart_count + 1}/{self._max_restart_attempts} 次, "
                f"退避延迟: {delay:.1f}s)"
            )
            
            # 等待退避延迟
            logger.info(f"⏳ 等待 {delay:.1f}s 后重启...")
            time.sleep(delay)
            
            # 执行重启
            self._restart_callback()
            self.record_restart()
            
            logger.info(f"[OK] 连接重启成功 (累计重启: {self._restart_count} 次)")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] 重启失败: {e}", exc_info=True)
            return False
    
    def check_and_restart_if_needed(self) -> bool:
        """
        检查连接状态并在需要时重启
        
        Returns:
            True 如果执行了重启
        """
        if not self._is_alive_callback:
            logger.debug("未设置存活检查回调函数")
            return False
        
        if self._is_alive_callback():
            logger.debug("连接存活，无需重启")
            return False
        
        logger.error("[ERROR] 检测到连接失效，准备重启")
        return self.attempt_restart()
    
    def start_stability_check(self, check_interval: float = 300) -> None:
        """
        启动稳定性检查线程（5分钟后重置计数器）
        
        Args:
            check_interval: 检查间隔（秒），默认300秒（5分钟）
        """
        def stability_check_loop():
            while self._running:
                try:
                    time.sleep(check_interval)
                    
                    # 检查连接是否稳定
                    if self._is_alive_callback and self._is_alive_callback():
                        self.reset_restart_count()
                        
                except Exception as e:
                    logger.error(f"稳定性检查失败: {e}")
        
        self._running = True
        check_thread = threading.Thread(
            target=stability_check_loop,
            daemon=True,
            name="stability-check"
        )
        check_thread.start()
        logger.info(f"🏥 稳定性检查已启动 (间隔: {check_interval}s)")
    
    def stop(self) -> None:
        """停止自愈管理器"""
        self._running = False


class SelfHealingManagerAsync:
    """
    异步自愈管理器
    
    使用 asyncio 实现自愈功能，适用于异步环境。
    """
    
    def __init__(
        self,
        max_restart_attempts: int = DEFAULT_MAX_RESTART_ATTEMPTS,
        restart_backoff_base: float = DEFAULT_RESTART_BACKOFF_BASE
    ):
        """
        初始化异步自愈管理器
        
        Args:
            max_restart_attempts: 最大重启尝试次数
            restart_backoff_base: 指数退避基数（秒）
        """
        self._restart_count: int = 0
        self._last_restart_time: float = 0.0
        self._max_restart_attempts = max_restart_attempts
        self._restart_backoff_base = restart_backoff_base
        self._restart_lock = asyncio.Lock()
        self._running = False
        self._stability_task: Optional[asyncio.Task] = None
        
        # 回调函数
        self._restart_callback: Optional[Callable[[], Awaitable[None]]] = None
        self._is_alive_callback: Optional[Callable[[], Awaitable[bool]]] = None
    
    def set_restart_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        """
        设置重启回调函数
        
        Args:
            callback: 重启连接的异步函数
        """
        self._restart_callback = callback
    
    def set_is_alive_callback(self, callback: Callable[[], Awaitable[bool]]) -> None:
        """
        设置连接存活检查回调函数
        
        Args:
            callback: 检查连接是否存活的异步函数
        """
        self._is_alive_callback = callback
    
    async def can_restart(self) -> bool:
        """
        检查是否可以重启
        
        Returns:
            True 如果可以重启
        """
        async with self._restart_lock:
            # 检查是否超过最大重启次数
            if self._restart_count >= self._max_restart_attempts:
                logger.error(
                    f"[ERROR] 已达到最大重启次数 ({self._max_restart_attempts})，停止自动重启"
                )
                return False
            
            # 检查是否在退避时间内
            current_time = time.time()
            delay = self._restart_backoff_base ** self._restart_count
            
            if current_time - self._last_restart_time < delay:
                logger.info(
                    f"⏳ 等待退避时间: {delay:.1f}s "
                    f"(重启次数: {self._restart_count}/{self._max_restart_attempts})"
                )
                return False
            
            return True
    
    async def get_restart_delay(self) -> float:
        """
        获取当前重启延迟（指数退避）
        
        Returns:
            重启延迟（秒）
        """
        async with self._restart_lock:
            return self._restart_backoff_base ** self._restart_count
    
    async def record_restart(self) -> None:
        """记录重启事件"""
        async with self._restart_lock:
            self._restart_count += 1
            self._last_restart_time = time.time()
            logger.info(f"🔄 记录重启事件 (累计重启: {self._restart_count} 次)")
    
    async def reset_restart_count(self) -> None:
        """重置重启计数器"""
        async with self._restart_lock:
            if self._restart_count > 0:
                logger.info(f"[OK] 连接稳定，重置重启计数器 (原计数: {self._restart_count})")
            self._restart_count = 0
    
    async def attempt_restart(self) -> bool:
        """
        尝试重启连接（异步版本）
        
        Returns:
            True 如果重启成功
        """
        if not await self.can_restart():
            return False
        
        if not self._restart_callback:
            logger.error("未设置重启回调函数")
            return False
        
        try:
            delay = await self.get_restart_delay()
            logger.info(
                f"🔄 尝试重启连接 "
                f"(第 {self._restart_count + 1}/{self._max_restart_attempts} 次, "
                f"退避延迟: {delay:.1f}s)"
            )
            
            # 等待退避延迟
            logger.info(f"⏳ 等待 {delay:.1f}s 后重启...")
            await asyncio.sleep(delay)
            
            # 执行重启
            await self._restart_callback()
            await self.record_restart()
            
            logger.info(f"[OK] 连接重启成功 (累计重启: {self._restart_count} 次)")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] 重启失败: {e}", exc_info=True)
            return False
    
    async def check_and_restart_if_needed(self) -> bool:
        """
        检查连接状态并在需要时重启
        
        Returns:
            True 如果执行了重启
        """
        if not self._is_alive_callback:
            logger.debug("未设置存活检查回调函数")
            return False
        
        if await self._is_alive_callback():
            logger.debug("连接存活，无需重启")
            return False
        
        logger.error("[ERROR] 检测到连接失效，准备重启")
        return await self.attempt_restart()
    
    async def start_stability_check(self, check_interval: float = 300) -> None:
        """
        启动稳定性检查任务（5分钟后重置计数器）
        
        Args:
            check_interval: 检查间隔（秒），默认300秒（5分钟）
        """
        if self._stability_task and not self._stability_task.done():
            logger.warning("稳定性检查任务已在运行")
            return
        
        self._running = True
        self._stability_task = asyncio.create_task(
            self._stability_check_loop(check_interval)
        )
        logger.info(f"🏥 异步稳定性检查已启动 (间隔: {check_interval}s)")
    
    async def _stability_check_loop(self, check_interval: float) -> None:
        """稳定性检查循环"""
        while self._running:
            try:
                await asyncio.sleep(check_interval)
                
                # 检查连接是否稳定
                if self._is_alive_callback and await self._is_alive_callback():
                    await self.reset_restart_count()
                    
            except asyncio.CancelledError:
                logger.info("🏥 稳定性检查任务被取消")
                break
            except Exception as e:
                logger.error(f"稳定性检查失败: {e}")
    
    async def stop(self) -> None:
        """停止自愈管理器"""
        self._running = False
        if self._stability_task and not self._stability_task.done():
            self._stability_task.cancel()
            try:
                await self._stability_task
            except asyncio.CancelledError:
                pass
        logger.info("🏥 异步自愈管理器已停止")
