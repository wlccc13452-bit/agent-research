"""
Card State Manager - 卡片状态管理器

负责管理卡片的生命周期状态，包括：
- 卡片状态追踪（processing/success/error）
- 最后卡片消息追踪（防止双击）
- 用户防抖记录
- 聊天防抖记录
- 定期清理过期状态
"""

import asyncio
import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


class CardStateManager:
    """
    卡片状态管理器
    
    负责管理卡片的生命周期状态，提供线程安全的状态访问和更新。
    """
    
    # 状态过期阈值（秒）
    STATE_EXPIRY_THRESHOLD = 600  # 10分钟
    USER_DEBOUNCE_THRESHOLD = 10  # 10秒
    CHAT_DEBOUNCE_THRESHOLD = 10  # 10秒
    
    def __init__(self) -> None:
        """初始化状态管理器"""
        # Card state management: message_id -> (status, timestamp)
        self._card_states: dict[str, tuple[str, float]] = {}
        
        # Last card tracking: chat_id -> (message_id, timestamp)
        self._last_card_message_ids: dict[str, tuple[str, float]] = {}
        
        # User-level debounce: user_id -> last_action_timestamp
        self._user_last_action: dict[str, tuple[str, float]] = {}
        
        # Chat-level debounce: chat_id -> last_card_timestamp
        self._chat_last_card_time: dict[str, float] = {}
        
        # Lock for thread-safe state updates
        self._state_lock = threading.Lock()
        
        # Cleanup task flag
        self._cleanup_task_started = False
    
    # ==================== Card State Methods ====================
    
    def set_card_state(self, message_id: str, status: str, timestamp: Optional[float] = None) -> None:
        """设置卡片状态"""
        with self._state_lock:
            self._card_states[message_id] = (status, timestamp or time.time())
            logger.debug(f"[NOTE] Card state set: {message_id[:20]}... -> {status}")
    
    def get_card_state(self, message_id: str) -> Optional[tuple[str, float]]:
        """获取卡片状态"""
        with self._state_lock:
            return self._card_states.get(message_id)
    
    def delete_card_state(self, message_id: str) -> None:
        """删除卡片状态"""
        with self._state_lock:
            if message_id in self._card_states:
                del self._card_states[message_id]
                logger.debug(f"🗑️ Card state deleted: {message_id[:20]}...")
    
    # ==================== Last Card Tracking Methods ====================
    
    def set_last_card_message(self, chat_id: str, message_id: str, timestamp: Optional[float] = None) -> None:
        """设置聊天的最后卡片消息"""
        with self._state_lock:
            self._last_card_message_ids[chat_id] = (message_id, timestamp or time.time())
    
    def get_last_card_message(self, chat_id: str) -> Optional[tuple[str, float]]:
        """获取聊天的最后卡片消息"""
        with self._state_lock:
            return self._last_card_message_ids.get(chat_id)
    
    # ==================== User Debounce Methods ====================
    
    def set_user_action(self, user_id: str, action: str, timestamp: Optional[float] = None) -> None:
        """记录用户操作时间"""
        with self._state_lock:
            self._user_last_action[user_id] = (action, timestamp or time.time())
    
    def get_user_action(self, user_id: str) -> Optional[tuple[str, float]]:
        """获取用户最后操作"""
        with self._state_lock:
            return self._user_last_action.get(user_id)
    
    # ==================== Chat Debounce Methods ====================
    
    def set_chat_last_card_time(self, chat_id: str, timestamp: Optional[float] = None) -> None:
        """设置聊天最后卡片发送时间"""
        with self._state_lock:
            self._chat_last_card_time[chat_id] = timestamp or time.time()
    
    def get_chat_last_card_time(self, chat_id: str) -> Optional[float]:
        """获取聊天最后卡片发送时间"""
        with self._state_lock:
            return self._chat_last_card_time.get(chat_id)
    
    # ==================== Cleanup Methods ====================
    
    def cleanup_expired(self) -> None:
        """清理过期的状态记录"""
        current_time = time.time()
        
        # 清理卡片状态
        with self._state_lock:
            if self._card_states:
                expired_keys = [
                    msg_id for msg_id, (status, timestamp) in self._card_states.items()
                    if current_time - timestamp > self.STATE_EXPIRY_THRESHOLD
                ]
                
                for msg_id in expired_keys:
                    del self._card_states[msg_id]
                
                if expired_keys:
                    logger.info(f"🗑️ Cleaned up {len(expired_keys)} expired card states")
        
        # 清理最后卡片追踪
        with self._state_lock:
            if self._last_card_message_ids:
                expired_chat_ids = [
                    chat_id for chat_id, (msg_id, timestamp) in self._last_card_message_ids.items()
                    if current_time - timestamp > self.STATE_EXPIRY_THRESHOLD
                ]
                
                for chat_id in expired_chat_ids:
                    del self._last_card_message_ids[chat_id]
                
                if expired_chat_ids:
                    logger.info(f"🗑️ Cleaned up {len(expired_chat_ids)} expired last card IDs")
        
        # 清理用户防抖记录
        with self._state_lock:
            if self._user_last_action:
                expired_user_actions = [
                    key for key, (action, timestamp) in self._user_last_action.items()
                    if current_time - timestamp > self.USER_DEBOUNCE_THRESHOLD
                ]
                
                for key in expired_user_actions:
                    del self._user_last_action[key]
                
                if expired_user_actions:
                    logger.debug(f"🗑️ Cleaned up {len(expired_user_actions)} expired user debounce records")
        
        # 清理聊天防抖记录
        with self._state_lock:
            if self._chat_last_card_time:
                expired_chat_cards = [
                    chat_id for chat_id, timestamp in self._chat_last_card_time.items()
                    if current_time - timestamp > self.CHAT_DEBOUNCE_THRESHOLD
                ]
                
                for chat_id in expired_chat_cards:
                    del self._chat_last_card_time[chat_id]
                
                if expired_chat_cards:
                    logger.debug(f"🗑️ Cleaned up {len(expired_chat_cards)} expired chat debounce records")
    
    def start_cleanup_task(self) -> None:
        """启动清理任务"""
        if self._cleanup_task_started:
            return
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._cleanup_loop_async())
                self._cleanup_task_started = True
                logger.info("🗑️ Card state cleanup task started (asyncio mode)")
            else:
                logger.debug("Event loop not running, cleanup task will start later")
        except RuntimeError:
            logger.warning("No event loop available, using thread for cleanup (fallback)")
            self._start_cleanup_thread_fallback()
    
    async def _cleanup_loop_async(self) -> None:
        """异步清理循环"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时清理一次
                self.cleanup_expired()
            except Exception as e:
                logger.error(f"Card state cleanup error: {e}")
    
    def _start_cleanup_thread_fallback(self) -> None:
        """线程清理降级方案"""
        def cleanup_loop():
            while True:
                try:
                    time.sleep(3600)
                    self.cleanup_expired()
                except Exception as e:
                    logger.error(f"Card state cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True, name="card-state-cleanup")
        cleanup_thread.start()
        self._cleanup_task_started = True
        logger.info("🗑️ Card state cleanup thread started (thread fallback mode)")
