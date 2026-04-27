"""美股/全球市场数据源

整合 yfinance, Alpha Vantage, Finnhub, 东方财富全球指数 等多个数据源。
替代 us_market_analyzer.py 中的直接 HTTP 调用。
"""
import logging
from typing import Optional, Dict, List

import httpx

from datasource.core.base import BaseDataSource
from datasource.core.constants import FunctionType, DataSourceType
from datasource.core.decorators import provider

logger = logging.getLogger(__name__)


class USMarketDataSource(BaseDataSource):
    """美股/全球市场数据源（多源级联）"""

    def __init__(self):
        self._alpha_vantage_key = None
        self._finnhub_key = None
        self._available = True
        self._try_load_keys()

    def _try_load_keys(self):
        try:
            from config.settings import settings
            self._alpha_vantage_key = getattr(settings, 'alpha_vantage_key', None)
            self._finnhub_key = getattr(settings, 'finnhub_key', None)
        except Exception:
            pass

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.YFINANCE

    @property
    def priority(self) -> int:
        return 50

    async def is_available(self) -> bool:
        return self._available

    @provider(FunctionType.US_QUOTE)
    async def get_us_quote(self, symbol: str) -> Optional[Dict]:
        """获取美股实时报价（级联: Finnhub -> Alpha Vantage -> Eastmoney -> yfinance）"""
        if self._finnhub_key:
            result = await self._fetch_finnhub_quote(symbol)
            if result:
                return result
        if self._alpha_vantage_key:
            result = await self._fetch_alpha_vantage_quote(symbol)
            if result:
                return result
        result = await self._fetch_eastmoney_us_quote(symbol)
        if result:
            return result
        return await self._fetch_yfinance_quote(symbol)

    @provider(FunctionType.INDEX_KLINE)
    async def get_index_kline(self, symbol: str, period: str = "day",
                              count: int = 100) -> Optional[List[Dict]]:
        """获取美股指数K线"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            period_map = {"day": "1mo", "week": "3mo", "month": "1y"}
            yf_period = period_map.get(period, "1mo")
            df = ticker.history(period=yf_period)
            if df.empty:
                return None
            history = df.tail(count)
            return [{
                'date': date_val.strftime('%Y-%m-%d'),
                'open': float(row['Open']), 'high': float(row['High']),
                'low': float(row['Low']), 'close': float(row['Close']),
                'volume': int(row['Volume']),
            } for date_val, row in history.iterrows()]
        except ImportError:
            logger.warning("yfinance 未安装")
            return None
        except Exception as e:
            logger.error(f"获取美股指数K线失败: {e}")
            return None

    # === 内部方法 ===

    async def _fetch_finnhub_quote(self, symbol: str) -> Optional[Dict]:
        if not self._finnhub_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                resp = await c.get("https://finnhub.io/api/v1/quote",
                                  params={"symbol": symbol, "token": self._finnhub_key})
                resp.raise_for_status()
                data = resp.json()
                if data.get("c", 0) > 0:
                    return {
                        "symbol": symbol, "current": data["c"],
                        "high": data["h"], "low": data["l"],
                        "open": data["o"], "prev_close": data["pc"],
                        "change": data["c"] - data["pc"],
                        "change_pct": round((data["c"] - data["pc"]) / data["pc"] * 100, 2) if data["pc"] else 0,
                        "source": "finnhub",
                    }
        except Exception:
            pass
        return None

    async def _fetch_alpha_vantage_quote(self, symbol: str) -> Optional[Dict]:
        if not self._alpha_vantage_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                resp = await c.get("https://www.alphavantage.co/query", params={
                    "function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": self._alpha_vantage_key,
                })
                resp.raise_for_status()
                data = resp.json()
                quote = data.get("Global Quote", {})
                if quote:
                    price = float(quote.get("05. price", 0))
                    prev = float(quote.get("08. previous close", 0))
                    return {
                        "symbol": symbol, "current": price, "prev_close": prev,
                        "change": round(float(quote.get("09. change", 0)), 2),
                        "change_pct": round(float(quote.get("10. change percent", "0%").rstrip("%")), 2),
                        "source": "alpha_vantage",
                    }
        except Exception:
            pass
        return None

    async def _fetch_eastmoney_us_quote(self, symbol: str) -> Optional[Dict]:
        # 东方财富国际指数 secid 映射
        symbol_map = {
            "^DJI": "100.DJI", "^GSPC": "100.SPX",
            "^IXIC": "100.NDX", "^VIX": "100.VIX",
            "^N225": "100.N225", "^KS11": "100.KS11",
        }
        em_symbol = symbol_map.get(symbol, symbol)
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                resp = await c.get("https://push2.eastmoney.com/api/qt/ulist.np/get", params={
                    "fltt": "2", "secids": em_symbol,
                    "fields": "f1,f2,f3,f4,f5,f6,f12,f14",
                })
                resp.raise_for_status()
                data = resp.json()
                items = data.get("data", {}).get("diff", [])
                if items:
                    item = items[0]
                    return {
                        "symbol": symbol, "name": item.get("f14", ""),
                        "current": item.get("f2"), "change": item.get("f4"),
                        "change_pct": item.get("f3"), "source": "eastmoney",
                    }
        except Exception:
            pass
        return None

    async def _fetch_yfinance_quote(self, symbol: str) -> Optional[Dict]:
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if hist.empty or len(hist) < 1:
                return None
            current = float(hist['Close'].iloc[-1])
            prev_close = float(hist['Close'].iloc[0]) if len(hist) >= 2 else current
            info = ticker.info
            return {
                "symbol": symbol, "name": info.get("shortName", ""),
                "current": current, "prev_close": prev_close,
                "change": round(current - prev_close, 2),
                "change_pct": round((current - prev_close) / prev_close * 100, 2) if prev_close else 0,
                "market_cap": info.get("marketCap"), "source": "yfinance",
            }
        except ImportError:
            return None
        except Exception:
            return None
