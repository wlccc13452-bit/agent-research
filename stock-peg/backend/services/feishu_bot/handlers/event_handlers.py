"""
Feishu Event Handlers Module - 事件处理器模块

重新导出interfaces.py中的事件处理器接口，保持向后兼容。
所有接口定义在interfaces.py中，避免重复定义。
"""

# 从interfaces.py导入事件处理器接口，避免重复定义
from feishu_sdk.config.interfaces import (
    FeishuEventHandler,
    MessageContext,
    CardActionContext,
)

__all__ = [
    'FeishuEventHandler',
    'MessageContext', 
    'CardActionContext'
]
