"""
Card Concurrency Manager - Global action lock and debounce system
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
        """Acquire user-level operation lock with debounce
        
        Args:
            user_id: User identifier
            
        Returns:
            True if lock acquired, False if already locked or debounced
        """
        # Check debounce
        current_time = time.time()
        last_action = self._user_last_action.get(user_id, 0)
        
        if current_time - last_action < self._debounce_window:
            logger.warning(
                f"[WARN]️ User {user_id} action debounced "
                f"(last action: {current_time - last_action:.2f}s ago)"
            )
            return False
        
        # Get or create lock
        if user_id not in self._user_locks:
            self._user_locks[user_id] = asyncio.Lock()
        
        lock = self._user_locks[user_id]
        
        # Try to acquire with timeout
        try:
            acquired = await asyncio.wait_for(
                lock.acquire(),
                timeout=self._lock_timeout
            )
            
            if acquired:
                self._user_last_action[user_id] = current_time
                logger.debug(f"🔒 User lock acquired: {user_id}")
                return True
            else:
                logger.warning(f"[WARN]️ User lock not acquired: {user_id}")
                return False
                
        except asyncio.TimeoutError:
            logger.warning(
                f"[WARN]️ User lock timeout: {user_id} "
                f"(lock held for > {self._lock_timeout}s)"
            )
            return False
    
    def release_user_lock(self, user_id: str) -> None:
        """Release user-level lock
        
        Args:
            user_id: User identifier
        """
        if user_id in self._user_locks:
            lock = self._user_locks[user_id]
            if lock.locked():
                lock.release()
                logger.debug(f"🔓 User lock released: {user_id}")
    
    async def acquire_chat_lock(self, chat_id: str) -> bool:
        """Acquire chat-level operation lock with debounce
        
        Args:
            chat_id: Chat identifier
            
        Returns:
            True if lock acquired, False if already locked or debounced
        """
        # Check debounce
        current_time = time.time()
        last_action = self._chat_last_action.get(chat_id, 0)
        
        if current_time - last_action < self._debounce_window:
            logger.warning(
                f"[WARN]️ Chat {chat_id} action debounced "
                f"(last action: {current_time - last_action:.2f}s ago)"
            )
            return False
        
        # Get or create lock
        if chat_id not in self._chat_locks:
            self._chat_locks[chat_id] = asyncio.Lock()
        
        lock = self._chat_locks[chat_id]
        
        # Try to acquire with timeout
        try:
            acquired = await asyncio.wait_for(
                lock.acquire(),
                timeout=self._lock_timeout
            )
            
            if acquired:
                self._chat_last_action[chat_id] = current_time
                logger.debug(f"🔒 Chat lock acquired: {chat_id}")
                return True
            else:
                logger.warning(f"[WARN]️ Chat lock not acquired: {chat_id}")
                return False
                
        except asyncio.TimeoutError:
            logger.warning(
                f"[WARN]️ Chat lock timeout: {chat_id} "
                f"(lock held for > {self._lock_timeout}s)"
            )
            return False
    
    def release_chat_lock(self, chat_id: str) -> None:
        """Release chat-level lock
        
        Args:
            chat_id: Chat identifier
        """
        if chat_id in self._chat_locks:
            lock = self._chat_locks[chat_id]
            if lock.locked():
                lock.release()
                logger.debug(f"🔓 Chat lock released: {chat_id}")
    
    async def acquire_both_locks(
        self, 
        user_id: str, 
        chat_id: str
    ) -> tuple[bool, bool]:
        """Acquire both user and chat locks atomically
        
        Args:
            user_id: User identifier
            chat_id: Chat identifier
            
        Returns:
            Tuple of (user_lock_acquired, chat_lock_acquired)
        """
        user_acquired = await self.acquire_user_lock(user_id)
        if not user_acquired:
            return (False, False)
        
        chat_acquired = await self.acquire_chat_lock(chat_id)
        if not chat_acquired:
            # Release user lock if chat lock failed
            self.release_user_lock(user_id)
            return (False, False)
        
        return (True, True)
    
    def release_both_locks(self, user_id: str, chat_id: str) -> None:
        """Release both user and chat locks
        
        Args:
            user_id: User identifier
            chat_id: Chat identifier
        """
        self.release_user_lock(user_id)
        self.release_chat_lock(chat_id)
    
    def is_user_locked(self, user_id: str) -> bool:
        """Check if user has an active lock
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user has active lock
        """
        if user_id in self._user_locks:
            return self._user_locks[user_id].locked()
        return False
    
    def is_chat_locked(self, chat_id: str) -> bool:
        """Check if chat has an active lock
        
        Args:
            chat_id: Chat identifier
            
        Returns:
            True if chat has active lock
        """
        if chat_id in self._chat_locks:
            return self._chat_locks[chat_id].locked()
        return False
    
    def get_stats(self) -> dict:
        """Get lock statistics
        
        Returns:
            Dictionary with lock statistics
        """
        return {
            "active_user_locks": sum(
                1 for lock in self._user_locks.values() if lock.locked()
            ),
            "active_chat_locks": sum(
                1 for lock in self._chat_locks.values() if lock.locked()
            ),
            "total_user_entries": len(self._user_last_action),
            "total_chat_entries": len(self._chat_last_action),
            "debounce_window": self._debounce_window,
            "lock_timeout": self._lock_timeout,
        }


# Global singleton instance
_global_action_lock: Optional[GlobalActionLock] = None


def get_global_action_lock() -> GlobalActionLock:
    """Get or create global action lock singleton
    
    Returns:
        GlobalActionLock instance
    """
    global _global_action_lock
    if _global_action_lock is None:
        _global_action_lock = GlobalActionLock()
    return _global_action_lock


# Context manager for automatic lock management
class UserActionLock:
    """Context manager for user action lock with automatic release"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.lock_manager = get_global_action_lock()
        self.acquired = False
    
    async def __aenter__(self) -> bool:
        self.acquired = await self.lock_manager.acquire_user_lock(self.user_id)
        return self.acquired
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            self.lock_manager.release_user_lock(self.user_id)
        return False  # Don't suppress exceptions


class ChatActionLock:
    """Context manager for chat action lock with automatic release"""
    
    def __init__(self, chat_id: str):
        self.chat_id = chat_id
        self.lock_manager = get_global_action_lock()
        self.acquired = False
    
    async def __aenter__(self) -> bool:
        self.acquired = await self.lock_manager.acquire_chat_lock(self.chat_id)
        return self.acquired
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            self.lock_manager.release_chat_lock(self.chat_id)
        return False  # Don't suppress exceptions
