"""腾讯API 数据源实现

统一腾讯股票API封装，消除 stock_service.py 中的重复实现。
"""
import logging
import re
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
    logger.warning("httpx 未安装，腾讯数据源不可用")


class TencentDataSource(BaseDataSource):
    """腾讯股票API数据源 - 免费，实时行情"""

    def __init__(self, base_url: str = "https://web.sqt.gtimg.cn"):
        self._base_url = base_url
        self._kline_base_url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        self._client = None
        if HTTPX_AVAILABLE:
            self._client = httpx.AsyncClient(timeout=10.0)
            logger.info(f"腾讯数据源初始化成功 (base_url: {base_url})")

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.TENCENT

    @property
    def priority(self) -> int:
        return 30

    async def is_available(self) -> bool:
        return self._client is not None

    def _to_tencent_symbol(self, stock_code: str) -> str:
        """转换股票代码为腾讯API格式"""
        symbol = (stock_code or "").strip()
        lower = symbol.lower()
        if lower.startswith(('sh', 'sz', 'hk', 'us', 'bk')):
            return lower
        suffix_match = re.match(r'^(\d{6})\.(sh|sz)$', lower)
        if suffix_match:
            code, market = suffix_match.groups()
            return f"{market}{code}"
        if code.startswith('6'):
            return f"sh{code}"
        elif code.startswith(('0', '3')):
            return f"sz{code}"
        return lower

    @provider(FunctionType.REALTIME_QUOTE)
    async def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """获取实时行情"""
        if not self._client:
            return None
        try:
            symbol = self._to_tencent_symbol(stock_code)
            url = f"{self._base_url}/q={symbol}"
            resp = await self._client.get(url)
            resp.raise_for_status()
            data = resp.text
            # 解析返回数据: v_sh600000="1~浦发银行~600000~10.50~10.30~10.55~..."
            if not data or '~' not in data:
                return None
            parts = data.split('~')
            if len(parts) < 45:
                return None
            return {
                'code': parts[2],
                'name': parts[1],
                'price': float(parts[3]) if parts[3] else 0,
                'prev_close': float(parts[4]) if parts[4] else 0,
                'open': float(parts[5]) if parts[5] else 0,
                'high': float(parts[33]) if parts[33] else 0,
                'low': float(parts[34]) if parts[34] else 0,
                'volume': int(float(parts[6])) if parts[6] else 0,
                'amount': float(parts[37]) if parts[37] else 0,
                'change_pct': float(parts[32]) if parts[32] else 0,
                'data_source': 'tencent',
            }
        except Exception as e:
            logger.debug(f"腾讯获取行情失败 {stock_code}: {e}")
            return None

    @provider(FunctionType.KLINE_MINUTE)
    async def get_minute_kline(self, stock_code: str, count: int = 240) -> Optional[List[Dict]]:
        """获取分钟K线数据"""
        if not self._client:
            return None
        try:
            symbol = self._to_tencent_symbol(stock_code)
            params = {
                '_var': 'kline_dayqfq',
                'param': f"{symbol},day,,,,,{count},",
            }
            resp = await self._client.get(self._kline_base_url, params=params)
            resp.raise_for_status()
            data = resp.json()
            qfq_data = data.get('data', {}).get(symbol, {}).get('day', [])
            if not qfq_data or not isinstance(qfq_data, list):
                return None
            return [{
                'code': stock_code, 'date': item[0],
                'open': float(item[1]), 'close': float(item[2]),
                'high': float(item[3]), 'low': float(item[4]),
                'volume': int(item[5]),
            } for item in qfq_data if len(item) >= 6]
        except Exception as e:
            logger.debug(f"腾讯获取分钟K线失败 {stock_code}: {e}")
            return None
