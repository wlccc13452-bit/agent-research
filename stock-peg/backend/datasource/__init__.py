"""
统一数据源入口模块

所有需要外部数据的模块都应通过此模块获取数据，而不是直接调用 akshare/tushare/httpx。

使用方式:
    from datasource import get_datasource

    # 获取实时行情
    quote = await get_datasource().get_realtime_quote("000001")

    # 获取K线
    kline = await get_datasource().get_kline("000001", period="day", count=120)

    # 获取市场情绪
    sentiment = await get_datasource().get_market_sentiment()

    # 按功能类型调用（自动选择最优数据源）
    from datasource import FunctionType
    kline = await get_datasource().call(FunctionType.KLINE_DAILY, "000001", count=120)
"""

from datasource.core.base import BaseDataSource
from datasource.core.constants import FunctionType, DataSourceType
from datasource.core.decorators import provider
from datasource.core.manager import DataSourceManager, data_source_manager
from datasource.core.smart_router import SmartRouter
from datasource.core.call_recorder import CallRecorder
from datasource.core.rate_limiter import UnifiedRateLimiter, unified_rate_limiter

__all__ = [
    # 核心类
    'DataSourceManager',
    'data_source_manager',
    'get_datasource',
    'get_source_manager',
    'init_datasources',
    # 基类与装饰器
    'BaseDataSource',
    'provider',
    # 枚举
    'FunctionType',
    'DataSourceType',
    # 基础设施
    'SmartRouter',
    'CallRecorder',
    'UnifiedRateLimiter',
    'unified_rate_limiter',
]

# 初始化标志
_initialized = False


def init_datasources() -> DataSourceManager:
    """
    初始化所有数据源并注册到管理器。

    应在应用启动时调用一次。每个数据源的 is_available() 检查
    会在实际调用时才触发（懒加载），此处只做注册。

    Returns:
        DataSourceManager 全局实例
    """
    global _initialized
    if _initialized:
        return data_source_manager

    from config.settings import settings
    from datasource.sources.tushare_source import TushareDataSource
    from datasource.sources.akshare_source import AkshareDataSource
    from datasource.sources.tencent_source import TencentDataSource
    from datasource.sources.eastmoney_source import EastmoneyDataSource
    from datasource.sources.us_market_source import USMarketDataSource
    from datasource.sources.adapters import (
        NewsServiceAdapter,
        FundamentalAnalyzerAdapter,
    )

    # 实例化并注册（按优先级排序）
    sources = [
        TushareDataSource(token=settings.tushare_token),  # priority=10, 付费API最稳定
        FundamentalAnalyzerAdapter(),                       # priority=15, Tushare财务数据补充
        TencentDataSource(),                                # priority=20, 实时行情首选
        AkshareDataSource(),                                # priority=20, AKShare完整实现
        EastmoneyDataSource(),                              # priority=40, 资金流等
        USMarketDataSource(),                               # priority=50, 美股数据
        NewsServiceAdapter(),                               # priority=60, 新闻数据
    ]

    for source in sources:
        try:
            data_source_manager.register_source(source)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"注册数据源 {source.__class__.__name__} 失败: {e}")

    _initialized = True
    return data_source_manager


def get_datasource() -> DataSourceManager:
    """获取全局数据源管理器实例（自动初始化）"""
    if not _initialized:
        init_datasources()
    return data_source_manager


def get_source_manager() -> DataSourceManager:
    """获取全局数据源管理器实例（别名）"""
    return get_datasource()
