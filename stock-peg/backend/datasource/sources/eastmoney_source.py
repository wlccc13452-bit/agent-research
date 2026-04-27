"""东方财富数据源实现

从 services/data_sources/eastmoney_source.py 迁移。
"""
import logging
import json
from typing import Optional, Dict, List

from datasource.core.base import BaseDataSource
from datasource.core.constants import FunctionType, DataSourceType
from datasource.core.decorators import provider

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx 未安装，东方财富数据源不可用")


class EastmoneyDataSource(BaseDataSource):
    """东方财富数据源 - 免费，行情和财务数据"""

    def __init__(self):
        self._client = None
        if HTTPX_AVAILABLE:
            self._client = httpx.AsyncClient(timeout=10.0, verify=False)
            logger.info("东方财富数据源初始化成功")

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.EASTMONEY

    @property
    def priority(self) -> int:
        return 40

    async def is_available(self) -> bool:
        return self._client is not None

    def _to_em_symbol(self, stock_code: str) -> str:
        """转换股票代码为东财格式 (0.000001, 1.600000)"""
        code = stock_code.split('.')[0]
        return f"1.{code}" if code.startswith('6') else f"0.{code}"

    @provider(FunctionType.REALTIME_QUOTE)
    async def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        if not self._client:
            return None
        try:
            symbol = self._to_em_symbol(stock_code)
            url = f"https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': symbol,
                'fields': 'f43,f44,f45,f46,f47,f48,f57,f58,f60,f169,f170',
            }
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            d = data.get('data')
            if not d:
                return None
            return {
                'code': stock_code,
                'price': d.get('f43', 0) / 100 if d.get('f43') else 0,
                'prev_close': d.get('f60', 0) / 100 if d.get('f60') else 0,
                'open': d.get('f46', 0) / 100 if d.get('f46') else 0,
                'high': d.get('f44', 0) / 100 if d.get('f44') else 0,
                'low': d.get('f45', 0) / 100 if d.get('f45') else 0,
                'volume': d.get('f47', 0),
                'amount': d.get('f48', 0),
                'change_pct': d.get('f170', 0) / 100 if d.get('f170') else 0,
                'data_source': 'eastmoney',
            }
        except Exception as e:
            logger.debug(f"东方财富获取行情失败 {stock_code}: {e}")
            return None

    @provider(FunctionType.FINANCIAL_REPORT)
    async def get_financial_report(self, stock_code: str) -> Optional[Dict]:
        """获取财务报表摘要"""
        if not self._client:
            return None
        try:
            symbol = self._to_em_symbol(stock_code)
            url = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
            params = {
                'reportName': 'RPT_F10_FINANCE_MAINFINADATA',
                'columns': 'SECURITY_CODE,REPORT_DATE,BASIC_EPS,WEIGHTAVG_ROE,MGJZC,YSTZ',
                'filter': f'(SECURITY_CODE="{stock_code.split(".")[0]}")',
                'pageNumber': 1, 'pageSize': 1, 'sortTypes': -1,
                'sortColumns': 'REPORT_DATE',
            }
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            result = data.get('result', {}).get('data', [])
            if not result:
                return None
            row = result[0]
            return {
                'code': row.get('SECURITY_CODE', ''),
                'report_date': row.get('REPORT_DATE', ''),
                'eps': row.get('BASIC_EPS'),
                'roe': row.get('WEIGHTAVG_ROE'),
                'bps': row.get('MGJZC'),
                'dividend_yield': row.get('YSTZ'),
            }
        except Exception as e:
            logger.debug(f"东方财富获取财务报表失败 {stock_code}: {e}")
            return None
