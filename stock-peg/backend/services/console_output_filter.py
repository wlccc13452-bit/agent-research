"""
控制台输出过滤器

根据console_output.ini配置动态过滤控制台输出
支持：消息截断、SQL隐藏、错误去重、列表简化
"""
import logging
import hashlib
import time
import re
from config.settings import settings
from typing import Dict, Set
from configparser import ConfigParser


class OutputController:
    """输出控制器 - 管理消息格式和长度"""
    
    def __init__(self):
        # Load output control settings from config
        self.config = ConfigParser()
        self.config.read('config/console_output.ini', encoding='utf-8')
        
        # Output length control
        self.console_max_length = self._getint('console_max_line_length', 300)
        self.file_max_length = self._getint('file_max_line_length', 0)
        
        # SQL output control
        self.enable_sql_console = self._getboolean('enable_sql_in_console', False)
        self.enable_sql_file = self._getboolean('enable_sql_in_file', True)
        
        # Traceback control
        self.enable_traceback_console = self._getboolean('enable_traceback_in_console', False)
        self.enable_traceback_file = self._getboolean('enable_traceback_in_file', True)
        
        # Error deduplication
        self.enable_error_dedup = self._getboolean('enable_error_dedup', True)
        self.error_dedup_window = self._getint('error_dedup_window', 60)
        self.show_error_summary = self._getboolean('show_error_summary', True)
        
        # List output control
        self.enable_list_console = self._getboolean('enable_list_in_console', False)
        self.list_max_display = self._getint('list_max_display', 5)
        
        # Error cache for deduplication
        # Format: {pattern_hash: (timestamp, count, last_message)}
        self.error_cache: Dict[str, tuple] = {}
    
    def _getint(self, key: str, fallback: int) -> int:
        try:
            return self.config.getint('output_control', key, fallback=fallback)
        except:
            return fallback
    
    def _getboolean(self, key: str, fallback: bool) -> bool:
        try:
            return self.config.getboolean('output_control', key, fallback=fallback)
        except:
            return fallback
    
    def _extract_error_pattern(self, message: str) -> str:
        """Extract error pattern for deduplication
        
        Identifies dynamic parts (stock codes, timestamps, IDs, etc.) and replaces them
        with placeholders to group similar errors together.
        
        Examples:
            "获取板块名称失败 BK0896: Connection error" -> "获取板块名称失败 {CODE}: Connection error"
            "未找到板块 BK1135 的名称" -> "未找到板块 {CODE} 的名称"
        """
        # Common patterns to replace
        patterns = [
            # 板块代码 BK开头
            (r'BK\d{4}', '{BOARD_CODE}'),
            # 股票代码 6位数字
            (r'\b\d{6}\b', '{STOCK_CODE}'),
            # 时间戳
            (r'\d{14,}', '{TIMESTAMP}'),
            (r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', '{DATETIME}'),
            # UUID
            (r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '{UUID}'),
            # IP地址
            (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '{IP}'),
            # 端口号
            (r':\d{4,5}\b', ':{PORT}'),
        ]
        
        pattern_msg = message
        for pattern, replacement in patterns:
            pattern_msg = re.sub(pattern, replacement, pattern_msg)
        
        return pattern_msg
    
    def _hash_message(self, message: str) -> str:
        """Generate hash for message deduplication"""
        return hashlib.md5(message.encode('utf-8')).hexdigest()[:16]
    
    def is_duplicate_error(self, message: str) -> bool:
        """Check if error message is duplicate within time window
        
        Uses error pattern (with dynamic parts replaced) for deduplication.
        Returns True if this error type has been seen recently.
        """
        if not self.enable_error_dedup:
            return False
        
        # Extract error pattern (replace dynamic parts)
        error_pattern = self._extract_error_pattern(message)
        pattern_hash = self._hash_message(error_pattern)
        current_time = time.time()
        
        # Clean old entries
        self.error_cache = {
            k: (t, c, m) for k, (t, c, m) in self.error_cache.items()
            if current_time - t < self.error_dedup_window
        }
        
        # Check if exists
        if pattern_hash in self.error_cache:
            timestamp, count, _ = self.error_cache[pattern_hash]
            self.error_cache[pattern_hash] = (timestamp, count + 1, message)
            return True
        
        # Add new entry
        self.error_cache[pattern_hash] = (current_time, 1, message)
        return False
    
    def get_error_summary(self, message: str) -> str:
        """Get error summary message if this is a duplicate
        
        Returns:
            Summary message like "该类型错误已出现 5 次"， or empty string if not duplicate
        """
        if not self.enable_error_dedup or not self.show_error_summary:
            return ""
        
        error_pattern = self._extract_error_pattern(message)
        pattern_hash = self._hash_message(error_pattern)
        
        if pattern_hash in self.error_cache:
            _, count, _ = self.error_cache[pattern_hash]
            # 只在特定次数时输出汇总：第2次、第10次、第50次、第100次
            summary_thresholds = [2, 10, 50, 100]
            if count in summary_thresholds:
                return f"[重复{count}次] {error_pattern}"
        
        return ""
    
    def truncate_message(self, message: str, max_length: int) -> str:
        """Truncate message if exceeds max length"""
        if max_length <= 0 or len(message) <= max_length:
            return message
        
        return message[:max_length-3] + "..."
    
    def hide_sql(self, message: str) -> str:
        """Hide SQL statement and return summary"""
        if '[SQL:' not in message:
            return message
        
        # Extract SQL type for summary
        if 'SELECT' in message.upper():
            return "[SQL: SELECT statement]"
        elif 'INSERT' in message.upper():
            return "[SQL: INSERT statement]"
        elif 'UPDATE' in message.upper():
            return "[SQL: UPDATE statement]"
        elif 'DELETE' in message.upper():
            return "[SQL: DELETE statement]"
        else:
            return "[SQL: statement]"
    
    def simplify_list(self, message: str) -> str:
        """Simplify list/dict display in console"""
        if self.enable_list_console:
            return message
        
        # Detect list patterns
        list_pattern = r"\[.*?\]"
        matches = list(re.finditer(list_pattern, message))
        
        if matches:
            for match in reversed(matches):  # Reverse to preserve indices
                list_str = match.group()
                try:
                    items = eval(list_str)
                    if isinstance(items, (list, tuple)) and len(items) > self.list_max_display:
                        # Truncate list
                        truncated = list(items[:self.list_max_display])
                        remaining = len(items) - self.list_max_display
                        truncated_str = str(truncated[:-1] + [f"... ({remaining} more)"])
                        message = message[:match.start()] + truncated_str + message[match.end():]
                except:
                    pass
        
        return message
    
    def format_for_console(self, record: logging.LogRecord) -> str:
        """Format message for console output (simplified)"""
        message = record.getMessage()
        
        # Hide SQL statements
        if '[SQL:' in message:
            message = self.hide_sql(message)
        
        # Simplify lists
        message = self.simplify_list(message)
        
        # Truncate long messages
        message = self.truncate_message(message, self.console_max_length)
        
        return message


# Global controller instance
_controller = None


def get_controller() -> OutputController:
    """Get or create output controller instance"""
    global _controller
    if _controller is None:
        _controller = OutputController()
    return _controller


class ConsoleOutputFilter(logging.Filter):
    """控制台输出过滤器，基于模块名和配置动态过滤日志"""
    
    # 模块名到配置项的映射
    MODULE_CONFIG_MAP: Dict[str, str] = {
        # 数据类
        'stock_data': 'enable_stock_data',
        'stock_service': 'enable_stock_data',
        'stock_data_service': 'enable_stock_data',
        'kline': 'enable_kline_data',
        'kline_cache': 'enable_kline_data',
        'financial': 'enable_financial_data',
        'fundamental': 'enable_financial_data',
        'market_index': 'enable_market_index',
        'market_data': 'enable_market_index',
        'us_market': 'enable_us_market',
        
        # 功能类
        'update_progress': 'enable_update_progress',
        'data_update': 'enable_update_progress',
        'background_updater': 'enable_background_task',
        'preload': 'enable_preload_progress',
        'cache': 'enable_cache',
        'websocket': 'enable_websocket',
        'realtime_pusher': 'enable_websocket',
        
        # 飞书机器人
        'feishu_bot': 'enable_feishu_bot',
        'feishu_long_connection': 'enable_feishu_connection',
        'feishu_chat': 'enable_feishu_chat',
        
        # 其他
        'scheduler': 'enable_scheduler',
        'database': 'enable_database',
        'api_request': 'enable_api_request',
        'httpx': 'enable_api_request',
        'httpcore': 'enable_api_request',
    }
    
    # 特定关键词到配置项的映射
    KEYWORD_CONFIG_MAP: Dict[str, str] = {
        'K线': 'enable_kline_data',
        '股票': 'enable_stock_data',
        '指数': 'enable_market_index',
        '美股': 'enable_us_market',
        '财务': 'enable_financial_data',
        '更新': 'enable_update_progress',
        '预加载': 'enable_preload_progress',
        '缓存': 'enable_cache',
        'WebSocket': 'enable_websocket',
        '飞书': 'enable_feishu_bot',
        '定时任务': 'enable_scheduler',
        '后台任务': 'enable_background_task',
        '数据库': 'enable_database',
    }
    
    def __init__(self):
        super().__init__()
        self.controller = get_controller()
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录
        
        Args:
            record: 日志记录
            
        Returns:
            bool: True表示允许输出，False表示过滤掉
        """
        # 如果总开关关闭，只允许错误日志
        if not settings.enable_console_output:
            return record.levelno >= logging.ERROR
        
        # 根据日志级别过滤
        if record.levelno >= logging.ERROR:
            # 检查错误去重
            message = record.getMessage()
            is_dup = self.controller.is_duplicate_error(message)
            
            if is_dup:
                # 如果是重复错误，检查是否需要输出汇总
                if self.controller.show_error_summary:
                    summary = self.controller.get_error_summary(message)
                    if summary:
                        # 修改记录的消息为汇总消息
                        record.msg = summary
                        record.args = ()
                        return settings.enable_errors
                return False
            
            return settings.enable_errors
        elif record.levelno >= logging.WARNING:
            # 警告也进行去重处理
            message = record.getMessage()
            if self.controller.is_duplicate_error(message):
                if self.controller.show_error_summary:
                    summary = self.controller.get_error_summary(message)
                    if summary:
                        record.msg = summary
                        record.args = ()
                        return settings.enable_warnings
                return False
            return settings.enable_warnings
        elif record.levelno >= logging.DEBUG and record.levelno < logging.INFO:
            return settings.enable_debug
        
        # 获取日志消息和模块名
        message = record.getMessage()
        module_name = record.name
        
        # 检查是否是启动相关日志
        if any(keyword in message for keyword in ['启动', '初始化', '就绪', '关闭']):
            return settings.enable_startup_info
        
        # 检查是否是系统状态日志
        if any(keyword in message for keyword in ['状态', '健康检查', '完成', '[OK]', '[ERROR]']):
            if '[OK]' in message or '[ERROR]' in message or '状态' in message:
                return settings.enable_system_status
        
        # 按模块名匹配配置
        for module_key, config_key in self.MODULE_CONFIG_MAP.items():
            if module_key in module_name:
                return getattr(settings, config_key, True)
        
        # 按关键词匹配配置
        for keyword, config_key in self.KEYWORD_CONFIG_MAP.items():
            if keyword in message:
                return getattr(settings, config_key, True)
        
        # 默认允许输出
        return True
    
    def format_message(self, record: logging.LogRecord) -> str:
        """Format message for console output"""
        return self.controller.format_for_console(record)
        
        # 按模块名匹配配置
        for module_key, config_key in self.MODULE_CONFIG_MAP.items():
            if module_key in module_name:
                return getattr(settings, config_key, True)
        
        # 按关键词匹配配置
        for keyword, config_key in self.KEYWORD_CONFIG_MAP.items():
            if keyword in message:
                return getattr(settings, config_key, True)
        
        # 默认允许输出
        return True




class ConsoleFormatter(logging.Formatter):
    """Custom formatter for console output with message simplification"""
    
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self.controller = get_controller()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with message simplification"""
        # Apply message simplification
        record.msg = self.controller.format_for_console(record)
        record.args = ()  # Clear args to prevent re-formatting
        
        # Call parent formatter
        return super().format(record)


def setup_console_filter():
    """设置控制台输出过滤器"""
    # 获取根logger
    root_logger = logging.getLogger()
    
    # 创建过滤器实例
    filter_instance = ConsoleOutputFilter()
    
    # 创建格式化器实例（简化格式）
    console_formatter = ConsoleFormatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 为所有控制台handler添加过滤器和格式化器
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.addFilter(filter_instance)
            # Apply simplified formatter
            handler.setFormatter(console_formatter)
    
    # 为常用模块添加过滤器
    common_loggers = [
        'services.stock_data_service',
        'services.stock_service',
        'services.kline_cache',
        'services.websocket_manager',
        'services.realtime_pusher',
        'services.background_updater',
        'services.data_update_manager',
        'services.feishu_bot',
        'services.feishu_long_connection_service',
        'services.scheduler',
        'routers.stock',
        'routers.us_market',
        'routers.holding',
        'database',
        'services.fundamental_analyzer',
        'services.fundamental_data_service',
    ]
    
    for logger_name in common_loggers:
        logger = logging.getLogger(logger_name)
        logger.addFilter(filter_instance)
        # Apply formatter to console handlers
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.addFilter(filter_instance)
                handler.setFormatter(console_formatter)
        # 如果logger没有handler，传播到root logger，过滤器会应用在root logger上
        logger.propagate = True


def should_show_progress() -> bool:
    """判断是否应该显示进度条"""
    return settings.show_progress_bar and settings.enable_preload_progress


# Convenience functions for logging specific content types

def log_sql(logger: logging.Logger, sql: str, params: tuple = None) -> None:
    """Log SQL statement with proper formatting
    
    Args:
        logger: Logger instance
        sql: SQL statement
        params: SQL parameters
    """
    controller = get_controller()
    
    # Always log to file with full details
    if controller.enable_sql_file:
        if params:
            logger.debug(f"[SQL] {sql} | params: {params}")
        else:
            logger.debug(f"[SQL] {sql}")
    elif controller.enable_sql_console:
        # Only log to console if enabled
        logger.debug(f"[SQL: statement]")


def log_error_simple(logger: logging.Logger, error: Exception, context: str = "") -> None:
    """Log error with simple console message but full file details
    
    Args:
        logger: Logger instance
        error: Exception instance
        context: Additional context
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Console gets simple message (handled by filter)
    if context:
        logger.error(f"{context}: {error_type} - {error_msg[:100]}")
    else:
        logger.error(f"{error_type}: {error_msg[:100]}")


def log_list(logger: logging.Logger, level: int, prefix: str, items: list) -> None:
    """Log list with truncation for console
    
    Args:
        logger: Logger instance
        level: Log level
        prefix: Message prefix
        items: List of items
    """
    controller = get_controller()
    
    if len(items) > controller.list_max_display:
        # Console gets truncated (handled by filter)
        msg = f"{prefix}: {items}"
    else:
        msg = f"{prefix}: {items}"
    
    logger.log(level, msg)
