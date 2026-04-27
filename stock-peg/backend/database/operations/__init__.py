"""Database Operations - 数据访问层

提供数据访问操作，将数据库操作从服务层分离：
- chat_message_ops: 聊天消息数据操作
- price_alert_ops: 价格预警数据操作
- watchlist_ops: 关注列表数据操作
- quote_ops: 行情数据操作
- stock_kline_ops: K线数据操作
- fundamental_ops: 基本面数据操作
- data_update_ops: 数据更新日志操作
- db_health: 数据库健康检查
"""

from database.operations.chat_message_ops import (
    save_chat_message,
    get_chat_history,
    get_recent_messages,
    get_latest_chat_id,
    get_messages_in_time_range,
    clear_all_chat_messages,
    check_message_exists,
    count_chat_messages,
)
from database.operations.price_alert_ops import (
    create_price_alert,
    stop_alert_monitoring,
    get_alert_by_id,
    adjust_alert_threshold,
    get_alerts,
    get_active_alerts,
    update_alert_price,
    trigger_alert,
    increment_trigger_count,
    deactivate_alert,
    delete_alert,
    reset_alert_trigger,
)
from database.operations.watchlist_ops import (
    add_to_watchlist,
    remove_from_watchlist,
    check_watchlist_exists,
    get_watchlist_by_date,
    get_all_dates,
    get_recent_watchlist_stocks,
    get_watchlist_by_stock,
    get_stock_by_id,
    update_watchlist_stock,
    archive_watchlist_stocks,
    unarchive_watchlist_stocks,
    upsert_watchlist_stock,
)
from database.operations.quote_ops import (
    get_quote,
    save_quote,
    check_update_necessity,
    get_all_quotes,
)
from database.operations.stock_kline_ops import (
    get_latest_date,
    get_kline_data,
    save_kline_data,
    clean_duplicates,
    get_kline_count,
    get_kline_data_by_date_range,
)
from database.operations.fundamental_ops import (
    get_fundamental_metrics,
    save_fundamental_metrics,
    get_financial_history,
    get_latest_financial_report,
    save_financial_history,
)
from database.operations.data_update_ops import (
    record_update_start,
    record_update_complete,
    get_latest_update_log,
    check_kline_data_integrity,
    check_financial_data_integrity,
    check_us_index_data_integrity,
    get_update_logs,
    get_latest_successful_update,
    migrate_stock_code,
)

from database.operations.force_index_ops import (
    get_force_index_cache,
    save_force_index_cache,
)
from database.operations.report_ops import (
    get_daily_report,
    get_daily_reports,
    update_prediction_verification,
    save_daily_report,
    get_reports_for_training,
)
from database.operations.us_stock_ops import (
    get_us_daily_data,
    save_us_daily_data,
    get_latest_us_data_date,
)
from database.operations.market_sentiment_ops import (
    get_latest_sentiment,
    get_sentiment_history,
    get_sentiment_by_date,
    save_sentiment,
    is_cache_valid,
    get_stored_trade_dates,
)
from database.operations.db_health import check_database_health
from database.operations.data_source_ops import (
    track_data_read,
    get_latest_tracks,
    get_current_data_status,
    build_metadata_response,
)

__all__ = [
    # Chat Message Operations
    'save_chat_message',
    'get_chat_history',
    'get_recent_messages',
    'get_latest_chat_id',
    'get_messages_in_time_range',
    'clear_all_chat_messages',
    'check_message_exists',
    'count_chat_messages',
    'get_latest_chat_id',
    'get_messages_in_time_range',
    'clear_all_chat_messages',
    'check_message_exists',
    'count_chat_messages',
    # Price Alert Operations
    'create_price_alert',
    'stop_alert_monitoring',
    'get_alert_by_id',
    'adjust_alert_threshold',
    'get_alerts',
    'get_active_alerts',
    'update_alert_price',
    'trigger_alert',
    'increment_trigger_count',
    'deactivate_alert',
    'delete_alert',
    'reset_alert_trigger',
    # Watchlist Operations
    'add_to_watchlist',
    'remove_from_watchlist',
    'check_watchlist_exists',
    'get_watchlist_by_date',
    'get_all_dates',
    'get_recent_watchlist_stocks',
    'get_watchlist_by_stock',
    'get_stock_by_id',
    'update_watchlist_stock',
    'archive_watchlist_stocks',
    'unarchive_watchlist_stocks',
    'upsert_watchlist_stock',
    # Quote Operations
    'get_quote',
    'save_quote',
    'check_update_necessity',
    'get_all_quotes',
    # Stock KLine Operations
    'get_latest_date',
    'get_kline_data',
    'save_kline_data',
    'clean_duplicates',
    'get_kline_count',
    'get_kline_data_by_date_range',
    # Fundamental Operations
    'get_fundamental_metrics',
    'save_fundamental_metrics',
    'get_financial_history',
    'get_latest_financial_report',
    'save_financial_history',
    # Data Update Operations
    'record_update_start',
    'record_update_complete',
    'get_latest_update_log',
    'check_kline_data_integrity',
    'check_financial_data_integrity',
    'check_us_index_data_integrity',
    'get_update_logs',
    'get_latest_successful_update',
    'migrate_stock_code',
    # Force Index Operations
    'get_force_index_cache',
    'save_force_index_cache',
    # Report Operations
    'get_daily_report',
    'get_daily_reports',
    'update_prediction_verification',
    'save_daily_report',
    'get_reports_for_training',
    # US Stock Operations
    'get_us_daily_data',
    'save_us_daily_data',
    'get_latest_us_data_date',
    # Market Sentiment Operations
    'get_latest_sentiment',
    'get_sentiment_history',
    'get_sentiment_by_date',
    'save_sentiment',
    'is_cache_valid',
    'get_stored_trade_dates',
    # Database Health
    'check_database_health',
    # Data Source Operations
    'track_data_read',
    'get_latest_tracks',
    'get_current_data_status',
    'build_metadata_response',
]
