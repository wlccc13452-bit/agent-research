"""
User selection cache for storing dropdown selections

由于飞书 Schema 2.0 的下拉选择和按钮点击是两次独立的回调，
需要缓存用户的下拉选择，以便在按钮点击时使用。
"""

import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class UserSelectionCache:
    """用户选择缓存（内存缓存，用于跨回调传递数据）"""
    
    def __init__(self, expiry_seconds: int = 300):
        """
        Initialize cache
        
        Args:
            expiry_seconds: Cache expiry time in seconds (default: 5 minutes)
        """
        self._cache: dict[str, dict[str, any]] = {}
        self._expiry = expiry_seconds
    
    def set_selection(self, user_id: str, field_name: str, value: str) -> None:
        """
        Store user's selection
        
        Args:
            user_id: User's open_id
            field_name: Field name (e.g., "selected_stock")
            value: Selected value
        """
        key = f"{user_id}:{field_name}"
        self._cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
        logger.info(f"[CACHE] Stored selection: {key} = {value}")
    
    def get_selection(self, user_id: str, field_name: str) -> Optional[str]:
        """
        Get user's selection
        
        Args:
            user_id: User's open_id
            field_name: Field name (e.g., "selected_stock")
            
        Returns:
            Selected value or None if not found/expired
        """
        key = f"{user_id}:{field_name}"
        entry = self._cache.get(key)
        
        if not entry:
            logger.warning(f"[CACHE] No selection found for: {key}")
            return None
        
        # Check expiry
        if time.time() - entry["timestamp"] > self._expiry:
            logger.warning(f"[CACHE] Selection expired for: {key}")
            del self._cache[key]
            return None
        
        value = entry["value"]
        logger.info(f"[CACHE] Retrieved selection: {key} = {value}")
        return value
    
    def clear_selection(self, user_id: str, field_name: str) -> None:
        """
        Clear user's selection
        
        Args:
            user_id: User's open_id
            field_name: Field name
        """
        key = f"{user_id}:{field_name}"
        if key in self._cache:
            del self._cache[key]
            logger.info(f"[CACHE] Cleared selection: {key}")
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired entries
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry["timestamp"] > self._expiry
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"[CACHE] Cleaned up {len(expired_keys)} expired entries")
        
        return len(expired_keys)


# Global singleton instance
_user_selection_cache: Optional[UserSelectionCache] = None


def get_user_selection_cache() -> UserSelectionCache:
    """Get global user selection cache instance"""
    global _user_selection_cache
    if _user_selection_cache is None:
        _user_selection_cache = UserSelectionCache()
    return _user_selection_cache
