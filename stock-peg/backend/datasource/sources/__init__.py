"""数据源实现模块"""
from datasource.sources.tushare_source import TushareDataSource
from datasource.sources.akshare_source import AkshareDataSource
from datasource.sources.tencent_source import TencentDataSource
from datasource.sources.eastmoney_source import EastmoneyDataSource
from datasource.sources.us_market_source import USMarketDataSource
from datasource.sources.adapters import (
    NewsServiceAdapter,
    FundamentalAnalyzerAdapter,
)

__all__ = [
    # 原生数据源实现
    'TushareDataSource',
    'AkshareDataSource',
    'TencentDataSource',
    'EastmoneyDataSource',
    'USMarketDataSource',
    # 服务适配器（包装现有services）
    'NewsServiceAdapter',
    'FundamentalAnalyzerAdapter',
]
