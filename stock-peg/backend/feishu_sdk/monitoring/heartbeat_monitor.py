"""
Heartbeat Monitor - 心跳监控模块

负责长连接的心跳监控功能：
- 心跳更新和追踪
- 连接存活检测
- 数据库健康检查
"""

import asyncio
import logging
import threading
import time
from typing import Optional, Callable, Awaitable, Any

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_HEARTBEAT_INTERVAL = 30  # 心跳更新间隔（秒）
DEFAULT_HEARTBEAT_TIMEOUT = 60   # 心跳超时阈值（秒）


class HeartbeatMonitor:
    """
    心跳监控器
    
    负责监控长连接的存活状态，定期更新心跳时间戳。
    """
    
    def __init__(
        self,
        heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL,
        heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT
    ):
        """
        初始化心跳监控器
        
        Args:
            heartbeat_interval: 心跳更新间隔（秒）
            heartbeat_timeout: 心跳超时阈值（秒）
        """
        self._last_heartbeat: float = 0.0
        self._heartbeat_lock = threading.Lock()
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_timeout = heartbeat_timeout
        self._running = False
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._db_health_check_callback: Optional[Callable[[], Awaitable[dict]]] = None
    
    def set_db_health_check_callback(self, callback: Callable[[], Awaitable[dict]]) -> None:
        """
        设置数据库健康检查回调函数
        
        Args:
            callback: 异步健康检查函数
        """
        self._db_health_check_callback = callback
    
    def update_heartbeat(self) -> None:
        """更新心跳时间戳"""
        with self._heartbeat_lock:
            self._last_heartbeat = time.time()
            logger.debug(f"[HEART] 心跳已更新: {self._last_heartbeat}")
    
    def get_last_heartbeat(self) -> float:
        """
        获取最后心跳时间戳
        
        Returns:
            最后心跳时间戳（秒，从 epoch 开始）
        """
        with self._heartbeat_lock:
            return self._last_heartbeat
    
    def is_alive(self) -> bool:
        """
        检查连接是否存活
        
        Returns:
            True 如果连接存活（心跳在超时阈值内）
        """
        if not self._running:
            return False
        
        last_heartbeat = self.get_last_heartbeat()
        current_time = time.time()
        
        # 如果从未更新心跳，认为连接未存活
        if last_heartbeat == 0.0:
            return False
        
        # 检查心跳是否在超时阈值内
        is_alive = (current_time - last_heartbeat) < self._heartbeat_timeout
        return is_alive
    
    def get_heartbeat_age(self) -> float:
        """
        获取心跳年龄（距离上次更新的时间）
        
        Returns:
            心跳年龄（秒），如果从未更新则返回 0
        """
        last_heartbeat = self.get_last_heartbeat()
        if last_heartbeat == 0.0:
            return 0.0
        return time.time() - last_heartbeat
    
    def start(self) -> None:
        """启动心跳监控线程"""
        if self._running:
            logger.warning("心跳监控已在运行")
            return
        
        self._running = True
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="heartbeat-monitor"
        )
        self._heartbeat_thread.start()
        logger.info(f"[HEART] 心跳监控已启动 (间隔: {self._heartbeat_interval}s, 超时: {self._heartbeat_timeout}s)")
    
    def stop(self) -> None:
        """停止心跳监控"""
        self._running = False
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=3)
        logger.info("[HEART] 心跳监控已停止")
    
    def _heartbeat_loop(self) -> None:
        """心跳更新循环（在后台线程中运行）"""
        logger.info("[HEART] 心跳循环已启动")
        
        while self._running:
            try:
                self.update_heartbeat()
                
                # 定期数据库健康检查（每 5 分钟）
                if int(self._last_heartbeat) % 300 == 0:
                    self._check_database_health()
                
                time.sleep(self._heartbeat_interval)
            except Exception as e:
                logger.error(f"心跳更新失败: {e}")
                break
        
        logger.warning("[HEART] 心跳循环已停止")
    
    def _check_database_health(self) -> None:
        """检查数据库健康状态（在心跳线程中运行）"""
        if not self._db_health_check_callback:
            return
        
        try:
            # 创建新的事件循环执行健康检查
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(self._db_health_check_callback())
                
                if result.get("status") != "healthy":
                    logger.warning(f"[WARN]️ 数据库健康检查失败: {result}")
                else:
                    logger.debug(f"[OK] 数据库健康: pool_size={result.get('pool_size')}")
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")


class HeartbeatMonitorAsync:
    """
    异步心跳监控器
    
    使用 asyncio 实现心跳监控，适用于异步环境。
    """
    
    def __init__(
        self,
        heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL,
        heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT
    ):
        """
        初始化异步心跳监控器
        
        Args:
            heartbeat_interval: 心跳更新间隔（秒）
            heartbeat_timeout: 心跳超时阈值（秒）
        """
        self._last_heartbeat: float = 0.0
        self._heartbeat_lock = asyncio.Lock()
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_timeout = heartbeat_timeout
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._db_health_check_callback: Optional[Callable[[], Awaitable[dict]]] = None
    
    def set_db_health_check_callback(self, callback: Callable[[], Awaitable[dict]]) -> None:
        """
        设置数据库健康检查回调函数
        
        Args:
            callback: 异步健康检查函数
        """
        self._db_health_check_callback = callback
    
    async def update_heartbeat(self) -> None:
        """更新心跳时间戳"""
        async with self._heartbeat_lock:
            self._last_heartbeat = time.time()
            logger.debug(f"[HEART] 心跳已更新: {self._last_heartbeat}")
    
    async def get_last_heartbeat(self) -> float:
        """
        获取最后心跳时间戳
        
        Returns:
            最后心跳时间戳（秒，从 epoch 开始）
        """
        async with self._heartbeat_lock:
            return self._last_heartbeat
    
    async def is_alive(self) -> bool:
        """
        检查连接是否存活
        
        Returns:
            True 如果连接存活（心跳在超时阈值内）
        """
        if not self._running:
            return False
        
        last_heartbeat = await self.get_last_heartbeat()
        current_time = time.time()
        
        # 如果从未更新心跳，认为连接未存活
        if last_heartbeat == 0.0:
            return False
        
        # 检查心跳是否在超时阈值内
        is_alive = (current_time - last_heartbeat) < self._heartbeat_timeout
        return is_alive
    
    async def get_heartbeat_age(self) -> float:
        """
        获取心跳年龄（距离上次更新的时间）
        
        Returns:
            心跳年龄（秒），如果从未更新则返回 0
        """
        last_heartbeat = await self.get_last_heartbeat()
        if last_heartbeat == 0.0:
            return 0.0
        return time.time() - last_heartbeat
    
    async def start(self) -> None:
        """启动心跳监控任务"""
        if self._running:
            logger.warning("心跳监控已在运行")
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"[HEART] 异步心跳监控已启动 (间隔: {self._heartbeat_interval}s, 超时: {self._heartbeat_timeout}s)")
    
    async def stop(self) -> None:
        """停止心跳监控"""
        self._running = False
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("[HEART] 异步心跳监控已停止")
    
    async def _heartbeat_loop(self) -> None:
        """心跳更新循环（在异步任务中运行）"""
        logger.info("[HEART] 异步心跳循环已启动")
        
        while self._running:
            try:
                await self.update_heartbeat()
                
                # 定期数据库健康检查（每 5 分钟）
                last_heartbeat = await self.get_last_heartbeat()
                if int(last_heartbeat) % 300 == 0:
                    await self._check_database_health()
                
                await asyncio.sleep(self._heartbeat_interval)
            except asyncio.CancelledError:
                logger.info("[HEART] 异步心跳循环被取消")
                break
            except Exception as e:
                logger.error(f"心跳更新失败: {e}")
                break
        
        logger.warning("[HEART] 异步心跳循环已停止")
    
    async def _check_database_health(self) -> None:
        """检查数据库健康状态（异步版本）"""
        if not self._db_health_check_callback:
            return
        
        try:
            result = await self._db_health_check_callback()
            
            if result.get("status") != "healthy":
                logger.warning(f"[WARN]️ 数据库健康检查失败: {result}")
            else:
                logger.debug(f"[OK] 数据库健康: pool_size={result.get('pool_size')}")
                
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
