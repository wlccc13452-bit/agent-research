"""
统一日志管理器

提供基于配置的日志输出控制，简化日志使用
"""
import logging
from config.settings import settings
from typing import Optional


class ManagedLogger:
    """受管理的日志器，根据配置自动控制输出"""
    
    def __init__(self, name: str, config_key: Optional[str] = None):
        """
        初始化受管理的日志器
        
        Args:
            name: 日志器名称
            config_key: 配置项键名（可选，自动推断）
        """
        self.logger = logging.getLogger(name)
        self.name = name
        self.config_key = config_key
    
    def _should_log(self, level: int) -> bool:
        """判断是否应该输出日志"""
        # 检查总开关
        if not settings.enable_console_output:
            return level >= logging.ERROR and settings.enable_errors
        
        # 检查日志级别配置
        if level >= logging.ERROR:
            return settings.enable_errors
        elif level >= logging.WARNING:
            return settings.enable_warnings
        elif level >= logging.DEBUG:
            return settings.enable_debug
        
        # 如果有指定配置键，使用该配置
        if self.config_key:
            return getattr(settings, self.config_key, True)
        
        return True
    
    def _log(self, level: int, msg: str, *args, **kwargs):
        """内部日志方法，先检查配置再输出"""
        if self._should_log(level):
            self.logger.log(level, msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        """调试日志"""
        self._log(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """信息日志"""
        self._log(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """警告日志"""
        self._log(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """错误日志"""
        self._log(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """严重错误日志"""
        self._log(logging.CRITICAL, msg, *args, **kwargs)


# 预定义的专用日志器
class StockDataLogger(ManagedLogger):
    """股票数据日志器"""
    def __init__(self, name: str = 'stock_data'):
        super().__init__(name, 'enable_stock_data')


class MarketIndexLogger(ManagedLogger):
    """市场指数日志器"""
    def __init__(self, name: str = 'market_index'):
        super().__init__(name, 'enable_market_index')


class FeishuBotLogger(ManagedLogger):
    """飞书机器人日志器"""
    def __init__(self, name: str = 'feishu_bot'):
        super().__init__(name, 'enable_feishu_bot')


class UpdateProgressLogger(ManagedLogger):
    """更新进度日志器"""
    def __init__(self, name: str = 'update_progress'):
        super().__init__(name, 'enable_update_progress')


class StartupLogger(ManagedLogger):
    """启动信息日志器"""
    def __init__(self, name: str = 'startup'):
        super().__init__(name, 'enable_startup_info')


class WebSocketLogger(ManagedLogger):
    """WebSocket连接日志器"""
    def __init__(self, name: str = 'websocket'):
        super().__init__(name, 'enable_websocket')


# 便捷工厂函数
def get_stock_logger(name: str = 'stock') -> StockDataLogger:
    """获取股票数据日志器"""
    return StockDataLogger(name)


def get_market_logger(name: str = 'market') -> MarketIndexLogger:
    """获取市场指数日志器"""
    return MarketIndexLogger(name)


def get_feishu_logger(name: str = 'feishu') -> FeishuBotLogger:
    """获取飞书机器人日志器"""
    return FeishuBotLogger(name)


def get_update_logger(name: str = 'update') -> UpdateProgressLogger:
    """获取更新进度日志器"""
    return UpdateProgressLogger(name)


def get_startup_logger(name: str = 'startup') -> StartupLogger:
    """获取启动信息日志器"""
    return StartupLogger(name)


def get_websocket_logger(name: str = 'websocket') -> WebSocketLogger:
    """获取WebSocket日志器"""
    return WebSocketLogger(name)
