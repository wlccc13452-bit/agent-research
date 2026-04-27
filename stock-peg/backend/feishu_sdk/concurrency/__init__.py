"""
Concurrency Management - SDK Layer

Provides concurrency control utilities for SDK services.
"""

from feishu_sdk.concurrency.action_lock import GlobalActionLock, get_global_action_lock

__all__ = [
    'GlobalActionLock',
    'get_global_action_lock',
]
