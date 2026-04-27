"""
Feishu Configuration Module - 配置模块

重新导出interfaces.py中的配置类，保持向后兼容。
所有配置类定义在interfaces.py中，避免重复定义。
"""

# 从interfaces.py导入配置类，避免重复定义
from feishu_sdk.config.interfaces import (
    FeishuConfig,
    FeishuConfigBuilder,
)

__all__ = ['FeishuConfig', 'FeishuConfigBuilder']
