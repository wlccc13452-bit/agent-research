"""
Feishu Command and Menu Constants - 飞书命令和菜单常量

Contains command mappings and menu event mappings for the Feishu bot.

Note: Heartbeat constants are now imported from SDK layer for consistency.
"""

from feishu_sdk.config.constants import (
    HEARTBEAT_INTERVAL,
    HEARTBEAT_TIMEOUT,
    HEARTBEAT_MONITOR_INTERVAL,
)

# ==================== Command Mapping ====================
# Maps user input keywords to card sending methods
# Format: {keyword_pattern: (card_method_name, requires_param, description)}

COMMAND_MAPPING: dict[str, tuple[str, bool, str]] = {
    # Main menu & activation
    "hello": ("send_main_menu_card", False, "主菜单"),
    "hi": ("send_main_menu_card", False, "主菜单"),
    "菜单": ("send_main_menu_card", False, "主菜单"),
    "主菜单": ("send_main_menu_card", False, "主菜单"),
    
    # Stock query (requires param - show input card)
    "股票查询": ("send_stock_query_card", False, "股票查询"),
    "股票研究": ("send_stock_query_card", False, "股票查询"),
    "查询": ("send_stock_query_card", True, "股票查询"),  # 带参数时直接查询
    "分析": ("send_stock_query_card", True, "股票查询"),  # 带参数时直接查询
    
    # Holdings
    "查看持仓": ("send_holdings_display_card", False, "持仓列表"),
    "持仓": ("send_holdings_display_card", False, "持仓列表"),
    "自持分析": ("send_holdings_display_card", False, "持仓列表"),
    "持仓管理": ("send_holdings_menu_card", False, "持仓管理"),
    "添加持仓": ("send_add_stock_to_holdings_card", False, "添加持仓"),
    
    # Watchlist
    "查看关注": ("send_watchlist_display_card", False, "关注列表"),
    "关注": ("send_watchlist_display_card", False, "关注列表"),
    "关注管理": ("send_watchlist_menu_card", False, "关注管理"),
    "添加关注": ("send_add_to_watchlist_card", False, "添加关注"),
    
    # Price alerts
    "价格提醒": ("send_price_alert_menu_card", False, "价格提醒"),
    "价格监控": ("send_price_alert_menu_card", False, "价格提醒"),
    "市场监控": ("send_price_alert_menu_card", False, "价格提醒"),
    "价格查询": ("send_price_query_card", False, "价格查询"),
    
    # Monitor setup
    "监控设置": ("send_monitor_setup_card", False, "监控设置"),
    
    # Help
    "帮助": ("send_main_menu_card", False, "主菜单"),
    "help": ("send_main_menu_card", False, "主菜单"),
}

# ==================== Menu Event Mapping ====================
# Maps mobile menu event keys to card sending methods
# Used when user clicks floating menu on mobile Feishu

MENU_COMMANDS: dict[str, str] = {
    "STOCK_RESEARCH_START": "send_stock_research_start_card",
    "HOLDING_ANALYSIS": "send_holdings_display_card",
    "VIEW_HOLDINGS": "send_holdings_display_card",
    "VIEW_WATCHLIST": "send_watchlist_display_card",
    "MARKET_MONITOR": "send_monitor_setup_card",
    "PRICE_ALERT": "send_price_alert_menu_card",
    "HELP_MENU": "send_main_menu_card",
}

# Heartbeat configuration (imported from SDK for consistency)
# These constants are defined in feishu_sdk.config.constants
# Application layer imports from SDK to maintain dependency direction
