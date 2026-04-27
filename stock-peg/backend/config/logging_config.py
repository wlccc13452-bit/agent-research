"""
Enhanced logging configuration with console output control
Controls what gets output to console vs log files
"""
import logging
import logging.config
import hashlib
import time
from pathlib import Path
from typing import Any, Optional
from collections import OrderedDict
from configparser import ConfigParser
from utils.line_limited_handler import LineLimitedFileHandler


class SizedCache(OrderedDict):
    """LRU Cache with max size"""
    def __init__(self, maxsize: int = 100):
        super().__init__()
        self.maxsize = maxsize
    
    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self.maxsize:
            self.popitem(last=False)


class OutputController:
    """Controls logging output format based on configuration"""
    
    def __init__(self, config_path: str = "config/console_output.ini"):
        self.config = ConfigParser()
        self.config.read(config_path, encoding='utf-8')
        
        # Load output control settings
        self.console_max_length = self.config.getint(
            'output_control', 'console_max_line_length', fallback=300
        )
        self.file_max_length = self.config.getint(
            'output_control', 'file_max_line_length', fallback=0
        )
        self.enable_sql_console = self.config.getboolean(
            'output_control', 'enable_sql_in_console', fallback=False
        )
        self.enable_sql_file = self.config.getboolean(
            'output_control', 'enable_sql_in_file', fallback=True
        )
        self.enable_traceback_console = self.config.getboolean(
            'output_control', 'enable_traceback_in_console', fallback=False
        )
        self.enable_traceback_file = self.config.getboolean(
            'output_control', 'enable_traceback_in_file', fallback=True
        )
        self.enable_error_dedup = self.config.getboolean(
            'output_control', 'enable_error_dedup', fallback=True
        )
        self.error_dedup_window = self.config.getint(
            'output_control', 'error_dedup_window', fallback=60
        )
        self.enable_list_console = self.config.getboolean(
            'output_control', 'enable_list_in_console', fallback=False
        )
        self.list_max_display = self.config.getint(
            'output_control', 'list_max_display', fallback=5
        )
        
        # Error deduplication cache
        self.error_cache: dict[str, tuple[float, int]] = {}
        
    def _hash_message(self, message: str) -> str:
        """Generate hash for message deduplication"""
        return hashlib.md5(message.encode('utf-8')).hexdigest()[:16]
    
    def is_duplicate_error(self, message: str) -> bool:
        """Check if error message is duplicate within time window"""
        if not self.enable_error_dedup:
            return False
        
        msg_hash = self._hash_message(message)
        current_time = time.time()
        
        # Clean old entries
        self.error_cache = {
            k: (t, c) for k, (t, c) in self.error_cache.items()
            if current_time - t < self.error_dedup_window
        }
        
        # Check if exists
        if msg_hash in self.error_cache:
            timestamp, count = self.error_cache[msg_hash]
            self.error_cache[msg_hash] = (timestamp, count + 1)
            return True
        
        # Add new entry
        self.error_cache[msg_hash] = (current_time, 1)
        return False
    
    def truncate_message(self, message: str, max_length: int) -> str:
        """Truncate message if exceeds max length"""
        if max_length <= 0 or len(message) <= max_length:
            return message
        
        return message[:max_length-3] + "..."
    
    def should_hide_sql(self, message: str, is_console: bool) -> tuple[bool, str]:
        """Check if SQL should be hidden in output
        
        Returns:
            (should_hide, replacement_message)
        """
        if '[SQL:' in message or 'SELECT ' in message or 'INSERT ' in message:
            if is_console and not self.enable_sql_console:
                # Extract SQL operation type for summary
                if 'SELECT' in message.upper():
                    return True, "[SQL: SELECT statement]"
                elif 'INSERT' in message.upper():
                    return True, "[SQL: INSERT statement]"
                elif 'UPDATE' in message.upper():
                    return True, "[SQL: UPDATE statement]"
                elif 'DELETE' in message.upper():
                    return True, "[SQL: DELETE statement]"
                else:
                    return True, "[SQL: statement]"
        
        return False, ""
    
    def should_hide_traceback(self, record: logging.LogRecord, is_console: bool) -> bool:
        """Check if traceback should be hidden"""
        if not is_console:
            return not self.enable_traceback_file
        return not self.enable_traceback_console
    
    def format_list_message(self, message: str, is_console: bool) -> str:
        """Format list/dict messages for display"""
        if not is_console or self.enable_list_console:
            return message
        
        # Detect list patterns like ['a', 'b', 'c', ...]
        import re
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
                        truncated_str = str(truncated[:-1] + [f"... ({remaining} more items)"])
                        message = message[:match.start()] + truncated_str + message[match.end():]
                except:
                    pass
        
        return message


class ConsoleFilter(logging.Filter):
    """Filter for console output with simplified messages"""
    
    def __init__(self, controller: OutputController):
        super().__init__()
        self.controller = controller
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and modify log record for console output"""
        
        # Check if it's an error/warning and deduplicate
        if record.levelno >= logging.ERROR:
            if self.controller.is_duplicate_error(record.getMessage()):
                return False  # Skip duplicate error
        
        # Get original message
        message = record.getMessage()
        
        # Check for SQL statements
        should_hide, replacement = self.controller.should_hide_sql(message, is_console=True)
        if should_hide:
            # Modify the message
            record.msg = replacement
            record.args = ()
            return True
        
        # Check for long lists
        message = self.controller.format_list_message(message, is_console=True)
        
        # Truncate long messages
        if self.controller.console_max_length > 0:
            message = self.controller.truncate_message(
                message, 
                self.controller.console_max_length
            )
        
        # Update record
        record.msg = message
        record.args = ()
        
        return True


class FileFilter(logging.Filter):
    """Filter for file output with full details"""
    
    def __init__(self, controller: OutputController):
        super().__init__()
        self.controller = controller
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log record for file output"""
        message = record.getMessage()
        
        # Check for SQL statements
        should_hide, replacement = self.controller.should_hide_sql(message, is_console=False)
        if should_hide:
            record.msg = replacement
            record.args = ()
        
        # Truncate if configured
        if self.controller.file_max_length > 0:
            message = record.getMessage()
            message = self.controller.truncate_message(
                message,
                self.controller.file_max_length
            )
            record.msg = message
            record.args = ()
        
        return True


def setup_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    config_path: str = "config/console_output.ini"
) -> None:
    """Setup enhanced logging with console output control
    
    Args:
        log_dir: Directory for log files
        log_level: Default log level
        config_path: Path to console_output.ini
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create server-debug directory
    server_debug_path = Path("logs/server-debug")
    server_debug_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize controller
    controller = OutputController(config_path)
    
    # Read server debug log configuration
    config_parser = ConfigParser()
    config_parser.read(config_path, encoding='utf-8')
    
    # Get log line limit configuration
    enable_line_limit = config_parser.getboolean(
        'log_line_limit', 'enable_line_limit', fallback=True
    )
    app_log_max_lines = config_parser.getint(
        'log_line_limit', 'app_log_max_lines', fallback=100
    )
    error_log_max_lines = config_parser.getint(
        'log_line_limit', 'error_log_max_lines', fallback=100
    )
    
    # Get server debug log settings
    enable_server_debug_log = config_parser.getboolean(
        'server_debug_log', 'enable_server_debug_log', fallback=True
    )
    delete_on_restart = config_parser.getboolean(
        'server_debug_log', 'delete_on_restart', fallback=True
    )
    debug_mode = config_parser.getboolean(
        'server_debug_log', 'debug_mode', fallback=True
    )
    backup_days = config_parser.getint(
        'server_debug_log', 'backup_days', fallback=30
    )
    rotation_strategy = config_parser.get(
        'server_debug_log', 'rotation_strategy', fallback='daily'
    )
    show_log_file_info = config_parser.getboolean(
        'server_debug_log', 'show_log_file_info', fallback=True
    )
    
    # Delete old logs in debug mode
    if debug_mode and delete_on_restart and enable_server_debug_log:
        server_log_file = Path("logs/server-debug/server.log")
        if server_log_file.exists():
            try:
                server_log_file.unlink()
                if show_log_file_info:
                    print(f"[DEBUG MODE] Deleted old server log: {server_log_file}")
            except Exception as e:
                print(f"[WARNING] Failed to delete old server log: {e}")
    
    # Determine backup count based on mode
    if debug_mode:
        backup_count = 1  # Keep only 1 day in debug mode
    else:
        backup_count = backup_days
    
    # Build handlers configuration
    # Use LineLimitedFileHandler if line limit is enabled
    if enable_line_limit:
        handlers = {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'console',
                'filters': ['console_filter'],
                'stream': 'ext://sys.stdout'
            },
            'file': {
                '()': LineLimitedFileHandler,
                'filename': f'{log_dir}/app.log',
                'max_lines': app_log_max_lines,
                'encoding': 'utf-8',
                'level': 'DEBUG',
                'formatter': 'file_detailed',
                'filters': ['file_filter']
            },
            'error_file': {
                '()': LineLimitedFileHandler,
                'filename': f'{log_dir}/error.log',
                'max_lines': error_log_max_lines,
                'encoding': 'utf-8',
                'level': 'ERROR',
                'formatter': 'file_detailed',
                'filters': ['file_filter']
            }
        }
    else:
        # Fallback to traditional RotatingFileHandler if line limit is disabled
        handlers = {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'console',
                'filters': ['console_filter'],
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'file_detailed',
                'filters': ['file_filter'],
                'filename': f'{log_dir}/app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'file_detailed',
                'filters': ['file_filter'],
                'filename': f'{log_dir}/error.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            }
        }
    
    # Add server debug handler if enabled
    if enable_server_debug_log:
        if rotation_strategy == 'daily':
            handlers['server_debug'] = {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'server_debug',
                'filename': 'logs/server-debug/server.log',
                'when': 'midnight',
                'interval': 1,
                'backupCount': backup_count,
                'encoding': 'utf-8'
            }
        else:  # size-based rotation
            handlers['server_debug'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'server_debug',
                'filename': 'logs/server-debug/server.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            }
    
    # Define logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'console': {
                'format': '%(asctime)s - %(levelname)s - %(message)s',
                'datefmt': '%H:%M:%S'
            },
            'file': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'file_detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'server_debug': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'filters': {
            'console_filter': {
                '()': lambda: ConsoleFilter(controller)
            },
            'file_filter': {
                '()': lambda: FileFilter(controller)
            }
        },
        'handlers': handlers,
        'root': {
            'level': log_level,
            'handlers': list(handlers.keys())
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Store controller reference for access from loggers
    logging._controller = controller
    
    # Log configuration info
    if enable_server_debug_log and show_log_file_info:
        logger = logging.getLogger(__name__)
        mode_str = "DEBUG MODE" if debug_mode else "PRODUCTION MODE"
        logger.info(f"[{mode_str}] Server debug logging enabled")
        logger.info(f"[{mode_str}] Log file: logs/server-debug/server.log")
        if debug_mode and delete_on_restart:
            logger.info(f"[{mode_str}] Old logs will be deleted on restart")
        else:
            logger.info(f"[{mode_str}] Logs will be kept for {backup_days} days")
    
    return controller


def get_controller() -> Optional[OutputController]:
    """Get the output controller instance"""
    return getattr(logging, '_controller', None)


# Convenience functions for common logging patterns

def log_sql(logger: logging.Logger, sql: str, params: tuple = None) -> None:
    """Log SQL statement with proper formatting
    
    Args:
        logger: Logger instance
        sql: SQL statement
        params: SQL parameters
    """
    if params:
        logger.debug(f"[SQL] {sql} | params: {params}")
    else:
        logger.debug(f"[SQL] {sql}")


def log_error_simple(logger: logging.Logger, error: Exception, context: str = "") -> None:
    """Log error with simple console message but full file details
    
    Args:
        logger: Logger instance
        error: Exception instance
        context: Additional context
    """
    error_msg = str(error)
    error_type = type(error).__name__
    
    # Console gets simple message
    if context:
        logger.error(f"{context}: {error_type}")
    else:
        logger.error(f"{error_type}: {error_msg[:100]}")
    
    # File gets full details (handled by file handler with traceback)


def log_list(logger: logging.Logger, level: int, prefix: str, items: list) -> None:
    """Log list with truncation for console
    
    Args:
        logger: Logger instance
        level: Log level
        prefix: Message prefix
        items: List of items
    """
    controller = get_controller()
    
    if controller and len(items) > controller.list_max_display:
        # Console gets truncated
        truncated = items[:controller.list_max_display]
        msg = f"{prefix}: {truncated}... ({len(items)} total)"
    else:
        msg = f"{prefix}: {items}"
    
    logger.log(level, msg)
