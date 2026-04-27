"""
Configuration Constants - Centralized configuration values

This module contains all hardcoded values, version numbers, and event mappings
to improve maintainability and reduce code duplication.
"""

# Bot Information
BOT_NAME = "PegBot"
BOT_VERSION = "2.1.0"
BOT_DESCRIPTION = "智能股票分析助手"

# Feishu API Constants
FEISHU_MESSAGE_ID_PREFIX = "om_"  # Feishu message ID format
FEISHU_MAX_CONTENT_LENGTH = 30000  # Max content length for Feishu messages

# Event Types and Actions
class EventType:
    """Feishu event types"""
    MESSAGE = "message"
    CARD_ACTION = "card_action"
    URL_VERIFICATION = "url_verification"


class CardAction:
    """Card action types"""
    # Query actions
    QUERY_STOCK = "query_stock"
    QUERY_STOCK_FROM_SELECT = "query_stock_from_select"
    QUERY_STOCK_FROM_STOCK = "query_stock_from_stock"
    QUERY_STOCK_PRICE = "query_stock_price"
    QUERY_STOCK_DETAIL = "query_stock_detail"
    TECHNICAL_ANALYSIS = "technical_analysis"
    FUNDAMENTAL_ANALYSIS = "fundamental_analysis"
    QUERY_PRICE = "query_price"
    
    # Menu actions
    MAIN_MENU = "main_menu"
    STOCK_QUERY_MENU = "stock_query_menu"
    PRICE_QUERY_MENU = "price_query_menu"
    HOLDINGS_MENU = "holdings_menu"
    WATCHLIST_MENU = "watchlist_menu"
    PRICE_ALERT_MENU = "price_alert_menu"
    
    # Holdings / watchlist management
    ADD_STOCK_TO_HOLDINGS = "add_stock_to_holdings"
    ADD_SECTOR_TO_HOLDINGS = "add_sector_to_holdings"
    ADD_TO_WATCHLIST = "add_to_watchlist"
    REMOVE_STOCK_FROM_HOLDINGS = "remove_stock_from_holdings"
    REMOVE_SECTOR_FROM_HOLDINGS = "remove_sector_from_holdings"
    REMOVE_FROM_WATCHLIST = "remove_from_watchlist"
    DELETE_STOCK_FROM_HOLDINGS = "delete_stock_from_holdings"
    DELETE_STOCK_FROM_WATCHLIST = "delete_stock_from_watchlist"
    SHOW_STOCK_ACTIONS = "show_stock_actions"
    SHOW_WATCHLIST_ACTIONS = "show_watchlist_actions"
    
    # Alert management
    CREATE_PRICE_ALERT = "create_price_alert"
    CREATE_PRICE_MONITOR = "create_price_monitor"
    STOP_ALERT_MONITORING = "stop_alert_monitoring"
    MODIFY_ALERT_THRESHOLD = "modify_alert_threshold"
    ADJUST_ALERT_THRESHOLD = "adjust_alert_threshold"
    CREATE_MONITOR = "create_monitor"
    SAVE_MONITOR_CONFIG = "save_monitor_config"
    
    # Form submissions
    CONFIRM_ADD_STOCK_HOLDINGS = "confirm_add_stock_holdings"
    CONFIRM_ADD_WATCHLIST = "confirm_add_watchlist"
    CONFIRM_CREATE_PRICE_ALERT = "confirm_create_price_alert"
    SAVE_MONITOR_TASK = "save_monitor_task"
    
    # Cancel / fallback actions
    CANCEL_QUERY = "cancel_query"
    CANCEL = "cancel"
    CANCEL_ADD = "cancel_add"
    
    # Quick view
    VIEW_HOLDINGS = "view_holdings"
    VIEW_WATCHLIST = "view_watchlist"
    VIEW_PRICE_ALERTS = "view_price_alerts"


CARD_QUERY_ACTIONS = {
    CardAction.QUERY_STOCK,
    CardAction.QUERY_STOCK_FROM_SELECT,
    CardAction.QUERY_STOCK_FROM_STOCK,
    CardAction.QUERY_STOCK_PRICE,
    CardAction.QUERY_STOCK_DETAIL,
    CardAction.TECHNICAL_ANALYSIS,
    CardAction.FUNDAMENTAL_ANALYSIS,
    CardAction.QUERY_PRICE,
}

CARD_FORM_ACTIONS = {
    CardAction.CONFIRM_ADD_STOCK_HOLDINGS,
    CardAction.CONFIRM_ADD_WATCHLIST,
    CardAction.CONFIRM_CREATE_PRICE_ALERT,
    CardAction.SAVE_MONITOR_TASK,
    CardAction.SAVE_MONITOR_CONFIG,
}

CARD_DELETE_ACTIONS = {
    CardAction.DELETE_STOCK_FROM_HOLDINGS,
    CardAction.DELETE_STOCK_FROM_WATCHLIST,
    CardAction.REMOVE_STOCK_FROM_HOLDINGS,
    CardAction.REMOVE_SECTOR_FROM_HOLDINGS,
    CardAction.REMOVE_FROM_WATCHLIST,
}

CARD_CANCEL_ACTIONS = {CardAction.CANCEL_QUERY, CardAction.CANCEL, CardAction.CANCEL_ADD}

CARD_MENU_ACTION_TO_METHOD: dict[str, str] = {
    CardAction.MAIN_MENU: "send_main_menu_card",
    CardAction.HOLDINGS_MENU: "send_holdings_menu_card",
    CardAction.WATCHLIST_MENU: "send_watchlist_menu_card",
    CardAction.PRICE_ALERT_MENU: "send_price_alert_menu_card",
    CardAction.PRICE_QUERY_MENU: "send_price_query_card",
    CardAction.STOCK_QUERY_MENU: "send_stock_query_card",
    CardAction.VIEW_HOLDINGS: "send_holdings_display_card",
    CardAction.VIEW_WATCHLIST: "send_watchlist_display_card",
    CardAction.ADD_STOCK_TO_HOLDINGS: "send_add_stock_to_holdings_card",
    CardAction.ADD_SECTOR_TO_HOLDINGS: "send_add_stock_to_holdings_card",
    CardAction.ADD_TO_WATCHLIST: "send_add_to_watchlist_card",
    CardAction.CREATE_PRICE_ALERT: "send_price_alert_card",
    CardAction.CREATE_MONITOR: "send_monitor_setup_card",
    CardAction.CREATE_PRICE_MONITOR: "send_monitor_config_card",
    CardAction.VIEW_PRICE_ALERTS: "send_price_alert_menu_card",
}

CARD_ACTION_RUNTIME_MAP: dict[str, str] = {
    CardAction.QUERY_STOCK_PRICE: CardAction.QUERY_STOCK,
    CardAction.QUERY_STOCK_DETAIL: CardAction.FUNDAMENTAL_ANALYSIS,
    CardAction.QUERY_STOCK_FROM_STOCK: CardAction.QUERY_STOCK_FROM_SELECT,
}

# 所有已知的 action（包括映射前和映射后的值）
CARD_ALL_KNOWN_ACTIONS = (
    CARD_QUERY_ACTIONS
    | CARD_FORM_ACTIONS
    | CARD_DELETE_ACTIONS
    | CARD_CANCEL_ACTIONS
    | set(CARD_MENU_ACTION_TO_METHOD.keys())
    | {CardAction.SHOW_STOCK_ACTIONS, CardAction.SHOW_WATCHLIST_ACTIONS}
    | {CardAction.SAVE_MONITOR_CONFIG, CardAction.ADD_SECTOR_TO_HOLDINGS}
    | set(CARD_ACTION_RUNTIME_MAP.keys())  # 添加映射前的原始 action（如 query_stock_price）
)


def _has_value(source: dict[str, object], key: str) -> bool:
    value = source.get(key)
    return value is not None and str(value).strip() != ""


def validate_card_action_payload(
    action_type: str,
    action_value: dict[str, object],
    form_data: dict[str, object]
) -> tuple[bool, str]:
    """Validate card action payload
    
    Args:
        action_type: The action type (can be original or runtime-mapped)
        action_value: The action value dict from button click
        form_data: The form data dict from input/select components
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    # Check if action is known (includes both original and mapped actions)
    if action_type not in CARD_ALL_KNOWN_ACTIONS:
        return False, f"未知动作: {action_type}"

    # Special handling for select dropdown actions
    # selected_stock can be in either action_value or form_data
    if action_type in {CardAction.QUERY_STOCK_FROM_SELECT, CardAction.QUERY_STOCK_FROM_STOCK}:
        has_selected_stock = (
            _has_value(form_data, "selected_stock") or
            _has_value(action_value, "selected_stock")
        )
        if not has_selected_stock:
            return False, "缺少选股字段 selected_stock"
        return True, ""

    # Query actions need stock_code from either source
    if action_type in {
        CardAction.QUERY_STOCK,
        CardAction.QUERY_PRICE,
        CardAction.QUERY_STOCK_PRICE,  # Add mapped action
        CardAction.TECHNICAL_ANALYSIS,
        CardAction.FUNDAMENTAL_ANALYSIS,
        CardAction.QUERY_STOCK_DETAIL,  # Add mapped action
    }:
        has_stock_code = (
            _has_value(form_data, "stock_code") or
            _has_value(action_value, "stock_code")
        )
        if has_stock_code:
            return True, ""
        return False, "缺少股票代码 stock_code"

    # Form submission validations
    if action_type == CardAction.CONFIRM_ADD_STOCK_HOLDINGS:
        has_stock = (
            _has_value(form_data, "stock_name") or
            _has_value(form_data, "selected_stock_from_watchlist") or
            _has_value(action_value, "stock_name") or
            _has_value(action_value, "selected_stock_from_watchlist")
        )
        has_sector = (
            _has_value(form_data, "sector_name") or
            _has_value(form_data, "new_sector_name") or
            _has_value(action_value, "sector_name") or
            _has_value(action_value, "new_sector_name")
        )
        if has_stock and has_sector:
            return True, ""
        return False, "添加持仓需提供股票和板块信息"

    if action_type == CardAction.CONFIRM_ADD_WATCHLIST:
        # 支持多种输入方式：
        # - stock_input: 手动输入股票名称或代码
        # - stock_select: 从持仓下拉选择
        # - stock_name: 旧字段（兼容）
        # - selected_stock_from_holdings: 旧字段（兼容）
        has_stock = (
            _has_value(form_data, "stock_input") or
            _has_value(form_data, "stock_select") or
            _has_value(form_data, "stock_name") or
            _has_value(form_data, "selected_stock_from_holdings") or
            _has_value(action_value, "stock_input") or
            _has_value(action_value, "stock_select") or
            _has_value(action_value, "stock_name") or
            _has_value(action_value, "selected_stock_from_holdings")
        )
        if has_stock:
            return True, ""
        return False, "添加关注需提供股票信息"

    if action_type == CardAction.CONFIRM_CREATE_PRICE_ALERT:
        has_stock_code = (
            _has_value(form_data, "stock_code") or
            _has_value(action_value, "stock_code")
        )
        has_threshold = (
            _has_value(form_data, "target_price") or
            _has_value(form_data, "change_up_pct") or
            _has_value(form_data, "change_down_pct") or
            _has_value(action_value, "target_price") or
            _has_value(action_value, "change_up_pct") or
            _has_value(action_value, "change_down_pct")
        )
        if has_stock_code and has_threshold:
            return True, ""
        return False, "价格提醒需提供股票代码和至少一个阈值"

    if action_type == CardAction.SAVE_MONITOR_TASK:
        has_stock = (
            _has_value(form_data, "stock_code") or
            _has_value(form_data, "stock_code_manual") or
            _has_value(action_value, "stock_code") or
            _has_value(action_value, "stock_code_manual")
        )
        has_threshold = (
            _has_value(form_data, "change_rate") or
            _has_value(form_data, "up_alert_pct") or
            _has_value(form_data, "down_alert_pct") or
            _has_value(action_value, "change_rate") or
            _has_value(action_value, "up_alert_pct") or
            _has_value(action_value, "down_alert_pct")
        )
        if has_stock and has_threshold:
            return True, ""
        return False, "监控任务需提供股票和预警阈值"

    # Delete actions need stock info OR sector info from action_value
    if action_type in CARD_DELETE_ACTIONS:
        has_stock_info = (
            _has_value(action_value, "stock_code") or
            _has_value(action_value, "stock_name")
        )
        has_sector_info = _has_value(action_value, "sector_name")
        
        if has_stock_info or has_sector_info:
            return True, ""
        return False, "删除动作缺少股票或板块信息"
    
    # Show actions need stock info
    if action_type in {CardAction.SHOW_STOCK_ACTIONS, CardAction.SHOW_WATCHLIST_ACTIONS}:
        has_stock_info = (
            _has_value(action_value, "stock_code") or
            _has_value(action_value, "stock_name")
        )
        if has_stock_info:
            return True, ""
        return False, "显示操作菜单需要股票信息"

    # All other actions are valid by default
    return True, ""


# Card Status Colors
class CardStatus:
    """Feishu card header template colors"""
    SUCCESS = "green"
    ERROR = "red"
    WARNING = "yellow"
    INFO = "blue"
    PROCESSING = "blue"
    NEUTRAL = "grey"
    IMPORTANT = "orange"
    SPECIAL = "purple"


# Card Templates
class CardTemplate:
    """Card template IDs and content"""
    # Loading card
    LOADING_TITLE = "⌛ 处理中"
    LOADING_CONTENT = "正在提交您的请求，请稍候..."
    
    # Success card
    SUCCESS_TITLE = "[OK] 操作成功"
    SUCCESS_CONTENT_DEFAULT = "操作已完成"
    
    # Error card
    ERROR_TITLE = "[ERROR] 操作失败"
    ERROR_CONTENT_DEFAULT = "操作失败，请重试"
    
    # Research start note
    RESEARCH_NOTE = "💡 提示: 分析通常需要 3-5 秒，结果将自动更新到此卡片"


# Retry Configuration
class RetryConfig:
    """Retry configuration for API calls"""
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    RETRY_BACKOFF_FACTOR = 2.0  # exponential backoff


# Rate Limiting
class RateLimit:
    """Rate limiting configuration"""
    FEISHU_API_MAX_REQUESTS_PER_SECOND = 10
    FEISHU_API_MAX_REQUESTS_PER_MINUTE = 500


# Database
class DatabaseConfig:
    """Database-related constants"""
    MESSAGE_ID_TRUNCATE_LENGTH = 16  # For logging purposes
    MAX_CONTENT_PREVIEW_LENGTH = 50  # For logging preview


# Logging
class LoggingConfig:
    """Logging configuration"""
    MAX_MESSAGE_ID_DISPLAY_LENGTH = 16
    MAX_CONTENT_PREVIEW_LENGTH = 50
    SENSITIVE_FIELD_NAMES = ["password", "token", "secret", "key", "credential"]


# Error Codes
class ErrorCode:
    """Feishu API error codes"""
    SUCCESS = 0
    INVALID_MESSAGE_ID = 10001
    PERMISSION_DENIED = 10002
    MESSAGE_NOT_FOUND = 10003
    RATE_LIMIT_EXCEEDED = 99991400  # Feishu rate limit error code
    HTTP_TOO_MANY_REQUESTS = 429  # HTTP 429 status code
    INTERNAL_ERROR = 500


# Card State Management
class CardStatePriority:
    """Card state priority for concurrent update protection
    
    Higher priority states cannot be overwritten by lower priority states.
    Terminal states (success/error) have highest priority.
    """
    TERMINAL_STATE_PRIORITY = 10  # success, error - cannot be overwritten
    WARNING_STATE_PRIORITY = 5     # warning, important states
    PROCESSING_STATE_PRIORITY = 1  # processing, intermediate states


# Content Size Limits
class ContentLimits:
    """Content size limits for Feishu messages"""
    MAX_CARD_SIZE_BYTES = 30 * 1024  # 30KB max for card JSON
    MAX_TRUNCATION_ATTEMPTS = 3      # Max attempts to truncate content
    TRUNCATION_NOTE = "...(内容过长已截断)"


# Concurrency Control Configuration
class ConcurrencyConfig:
    """Concurrency control configuration for card system
    
    These values control the locking and debouncing mechanisms
    to prevent concurrent conflicts and rapid-fire requests.
    """
    # Lock timeout
    LOCK_TIMEOUT = 10.0  # seconds - max time to wait for lock acquisition
    
    # Debounce settings
    DEBOUNCE_WINDOW = 2.0  # seconds - ignore rapid-fire requests within this window
    
    # Cleanup settings
    CLEANUP_INTERVAL = 300  # seconds - interval for cleaning up stale entries
    ENTRY_EXPIRY = 600  # seconds - entries older than this will be cleaned up
    MAX_ENTRIES = 10000  # maximum number of entries in memory
    
    # State management
    STATE_EXPIRY = 600  # seconds - card state entries older than this will be cleaned up
    USER_DEBOUNCE_EXPIRY = 10  # seconds - user debounce records older than this will be cleaned up


# Retry Configuration (Extended)
class RetryConfigExtended:
    """Extended retry configuration for external API calls"""
    # Retry attempts
    MAX_RETRIES = 3
    
    # Backoff settings
    BASE_BACKOFF = 1.0  # seconds - initial backoff time
    MAX_BACKOFF = 30.0  # seconds - maximum backoff time
    EXPONENTIAL_BASE = 2.0  # base for exponential calculation
    
    # Jitter
    ENABLE_JITTER = True  # add random jitter to avoid thundering herd
    
    # Timeout
    DEFAULT_TIMEOUT = 10.0  # seconds - default timeout for operations


# Circuit Breaker Configuration
class CircuitBreakerConfig:
    """Circuit breaker configuration for external service protection"""
    # Failure threshold
    FAILURE_THRESHOLD = 5  # number of failures before opening circuit
    
    # Recovery settings
    RECOVERY_TIMEOUT = 60.0  # seconds - time to wait before attempting recovery
    HALF_OPEN_MAX_CALLS = 3  # number of test calls in half-open state
