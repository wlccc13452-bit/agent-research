"""
Card Concurrency Manager - Global action lock and debounce system

Provides global operation locks to prevent concurrent conflicts.
This is a SDK-level utility with NO business logic dependencies.
"""
import asyncio
import logging
import time
from typing import Optional, Dict
from collections import defaultdict

logger = logging.getLogger(__name__)


class GlobalActionLock:
    """Global operation lock to prevent concurrent conflicts
    
    Features:
    - User-level locking: Prevent same user from concurrent operations
    - Chat-level locking: Prevent conflicts in same chat
    - Timeout protection: Auto-release locks after timeout
    - Debounce: Prevent rapid-fire requests
    """
    
    def __init__(self):
        self._user_locks: Dict[str, asyncio.Lock] = {}
        self._chat_locks: Dict[str, asyncio.Lock] = {}
        self._user_last_action: Dict[str, float] = {}
        self._chat_last_action: Dict[str, float] = {}
        
        # Configuration
        self._lock_timeout = 10.0  # seconds
        self._debounce_window = 2.0  # seconds
        self._cleanup_interval = 300  # seconds
        
        # Start cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start_cleanup(self) -> None:
        """Start background cleanup task"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("🔒 GlobalActionLock cleanup task started")
    
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of stale locks"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                self._cleanup_stale_entries()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def _cleanup_stale_entries(self) -> None:
        """Remove stale entries older than 1 hour"""
        current_time = time.time()
        stale_threshold = 3600  # 1 hour
        
        # Cleanup user entries
        stale_users = [
            user_id for user_id, last_time in self._user_last_action.items()
            if current_time - last_time > stale_threshold
        ]
        for user_id in stale_users:
            self._user_last_action.pop(user_id, None)
            self._user_locks.pop(user_id, None)
        
        # Cleanup chat entries
        stale_chats = [
            chat_id for chat_id, last_time in self._chat_last_action.items()
            if current_time - last_time > stale_threshold
        ]
        for chat_id in stale_chats:
            self._chat_last_action.pop(chat_id, None)
            self._chat_locks.pop(chat_id, None)
        
        if stale_users or stale_chats:
            logger.info(
                f"🧹 Cleaned up {len(stale_users)} stale users, "
                f"{len(stale_chats)} stale chats"
            )
    
    async def acquire_user_lock(self, user_id: str) -> bool:
        """Acquire lock for user
        
        Args:
            user_id: User ID
            
        Returns:
            True if lock acquired, False if already locked
        """
        if user_id not in self._user_locks:
            self._user_locks[user_id] = asyncio.Lock()
        
        lock = self._user_locks[user_id]
        
        # Check debounce
        current_time = time.time()
        if user_id in self._user_last_action:
            time_since_last = current_time - self._user_last_action[user_id]
            if time_since_last < self._debounce_window:
                logger.warning(f"User {user_id} debounced (time since last: {time_since_last:.2f}s)")
                return False
        
        # Try to acquire lock with timeout
        try:
            acquired = await asyncio.wait_for(
                lock.acquire(),
                timeout=self._lock_timeout
            )
            if acquired:
                self._user_last_action[user_id] = current_time
                return True
            return False
        except asyncio.TimeoutError:
            logger.warning(f"User {user_id} lock acquisition timeout")
            return False
    
    def release_user_lock(self, user_id: str) -> None:
        """Release lock for user"""
        if user_id in self._user_locks:
            lock = self._user_locks[user_id]
            if lock.locked():
                lock.release()
                logger.debug(f"Released user lock for {user_id}")
    
    async def acquire_chat_lock(self, chat_id: str) -> bool:
        """Acquire lock for chat
        
        Args:
            chat_id: Chat ID
            
        Returns:
            True if lock acquired, False if already locked
        """
        if chat_id not in self._chat_locks:
            self._chat_locks[chat_id] = asyncio.Lock()
        
        lock = self._chat_locks[chat_id]
        
        # Check debounce
        current_time = time.time()
        if chat_id in self._chat_last_action:
            time_since_last = current_time - self._chat_last_action[chat_id]
            if time_since_last < self._debounce_window:
                logger.warning(f"Chat {chat_id} debounced (time since last: {time_since_last:.2f}s)")
                return False
        
        # Try to acquire lock with timeout
        try:
            acquired = await asyncio.wait_for(
                lock.acquire(),
                timeout=self._lock_timeout
            )
            if acquired:
                self._chat_last_action[chat_id] = current_time
                return True
            return False
        except asyncio.TimeoutError:
            logger.warning(f"Chat {chat_id} lock acquisition timeout")
            return False
    
    def release_chat_lock(self, chat_id: str) -> None:
        """Release lock for chat"""
        if chat_id in self._chat_locks:
            lock = self._chat_locks[chat_id]
            if lock.locked():
                lock.release()
                logger.debug(f"Released chat lock for {chat_id}")


# Global singleton instance
_global_action_lock: Optional[GlobalActionLock] = None


def get_global_action_lock() -> GlobalActionLock:
    """Get or create global action lock instance"""
    global _global_action_lock
    if _global_action_lock is None:
        _global_action_lock = GlobalActionLock()
        logger.info("🔒 GlobalActionLock instance created")
    return _global_action_lock


__all__ = [
    'GlobalActionLock',
    'get_global_action_lock',
]
