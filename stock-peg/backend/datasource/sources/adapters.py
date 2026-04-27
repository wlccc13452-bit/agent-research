"""服务适配器 - 将现有services包装为datasource兼容的数据源

策略：不复制代码，而是用适配器模式将现有的 AkshareService / USMarketDataService / NewsAggregator
包装为 BaseDataSource 子类，注册到 DataSourceManager 中。

这样所有 ak.* / httpx.* / yf.* 调用都通过统一 datasource 接口暴露。
"""
import logging
from typing import Optional, Dict, List, Any

from datasource.core.base import BaseDataSource
from datasource.core.constants import FunctionType, DataSourceType
from datasource.core.decorators import provider

logger = logging.getLogger(__name__)


class NewsServiceAdapter(BaseDataSource):
    """适配器：将 NewsAggregator 包装为 BaseDataSource"""
    
    def __init__(self):
        self._service = None
    
    def _get_service(self):
        if self._service is None:
            from services.news_aggregator import news_aggregator
            self._service = news_aggregator
        return self._service
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.SINAFINANCE
    
    @property
    def priority(self) -> int:
        return 60
    
    async def is_available(self) -> bool:
        return True
    
    @provider(FunctionType.NEWS)
    async def get_stock_news(self, stock_code: str, stock_name: str = "", count: int = 20) -> List[Dict]:
        name = stock_name or stock_code
        return await self._get_service().get_stock_news(stock_code, name, count)
    
    @provider(FunctionType.NEWS)
    async def get_hot_news(self, count: int = 20) -> List[Dict]:
        return await self._get_service().get_hot_news(count)
    
    @provider(FunctionType.NEWS)
    async def get_sector_news(self, sector_name: str, count: int = 20) -> List[Dict]:
        return await self._get_service().get_sector_news(sector_name, count)


class FundamentalAnalyzerAdapter(BaseDataSource):
    """适配器：将 FundamentalAnalyzer 中的 Tushare 调用包装为 BaseDataSource

    fundamental_analyzer.py 中有 10 个直接 Tushare API 调用
    (daily_basic/income/fina_indicator/balancesheet/cashflow)，
    通过此适配器暴露给 datasource 层。
    """
    
    def __init__(self):
        self._service = None
    
    def _get_service(self):
        if self._service is None:
            from services.fundamental_analyzer import fundamental_analyzer
            self._service = fundamental_analyzer
        return self._service
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.TUSHARE
    
    @property
    def priority(self) -> int:
        return 15  # 低于原生 TushareDataSource (10)，作为补充
    
    async def is_available(self) -> bool:
        try:
            svc = self._get_service()
            return svc.ts_pro is not None
        except Exception:
            return False
    
    @provider(FunctionType.FINANCIAL_INDICATOR)
    async def get_financial_indicator_tushare(self, stock_code: str) -> Optional[Dict]:
        svc = self._get_service()
        try:
            return await svc._get_valuation_metrics(stock_code)
        except Exception:
            return None
    
    @provider(FunctionType.INCOME_STATEMENT)
    async def get_income_tushare(self, stock_code: str) -> Optional[Dict]:
        svc = self._get_service()
        try:
            return await svc._get_income_statement(stock_code)
        except Exception:
            return None
    
    @provider(FunctionType.BALANCE_SHEET)
    async def get_balance_sheet_tushare(self, stock_code: str) -> Optional[Dict]:
        svc = self._get_service()
        try:
            return await svc._get_balance_sheet(stock_code)
        except Exception:
            return None
    
    @provider(FunctionType.CASH_FLOW)
    async def get_cashflow_tushare(self, stock_code: str) -> Optional[Dict]:
        svc = self._get_service()
        try:
            return await svc._get_cashflow_statement(stock_code)
        except Exception:
            return None
    
    @provider(FunctionType.STOCK_INFO)
    async def get_stock_info_em(self, stock_code: str) -> Optional[Dict]:
        svc = self._get_service()
        try:
            return await svc._get_stock_info(stock_code)
        except Exception:
            return None
