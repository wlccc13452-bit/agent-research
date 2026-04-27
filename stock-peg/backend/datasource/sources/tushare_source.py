"""Tushare 数据源实现

统一的 Tushare API 封装，消除项目中3处重复的 _call_tushare() 实现。
"""
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta, date

from datasource.core.base import BaseDataSource
from datasource.core.constants import FunctionType, DataSourceType
from datasource.core.decorators import provider

logger = logging.getLogger(__name__)

try:
    import tushare as ts
    import pandas as pd
    TUSHARE_AVAILABLE = True
except ImportError:
    TUSHARE_AVAILABLE = False
    logger.warning("Tushare 未安装，该数据源不可用")


class TushareDataSource(BaseDataSource):
    """Tushare 数据源 - 付费数据源，数据最全面"""

    def __init__(self, token: str = None):
        self._token = token
        self._ts_pro = None
        self._unauthorized_apis: set = set()

        if TUSHARE_AVAILABLE and token:
            try:
                self._ts_pro = ts.pro_api(token)
                logger.info("Tushare 数据源初始化成功")
            except Exception as e:
                logger.error(f"Tushare 初始化失败: {str(e)}")

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.TUSHARE

    @property
    def priority(self) -> int:
        return 10

    async def is_available(self) -> bool:
        return self._ts_pro is not None

    def call_tushare_api(self, api_name: str, **kwargs) -> pd.DataFrame:
        """调用 Tushare API（公共方法，供外部模块使用）

        替代所有旧的 _call_tushare() 私有实现（stock_service, fundamental_analyzer 等）。
        """
        if not self._ts_pro:
            return pd.DataFrame()

        if api_name in self._unauthorized_apis:
            raise PermissionError(f"Tushare 接口 [{api_name}] 无权限")

        try:
            api_func = getattr(self._ts_pro, api_name)
            return api_func(**kwargs)
        except Exception as e:
            error_msg = str(e)
            if "没有接口访问权限" in error_msg or "unauthorized" in error_msg.lower():
                self._unauthorized_apis.add(api_name)
                raise PermissionError(f"Tushare 接口 [{api_name}] 无权限")
            raise

    # 保持向后兼容的别名
    _call_tushare_api = call_tushare_api

    # ==================== 行情数据 ====================

    @provider(FunctionType.REALTIME_QUOTE)
    async def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        if not self._ts_pro:
            return None
        try:
            df = self.call_tushare_api(
                'daily', ts_code=stock_code,
                start_date=(datetime.now() - timedelta(days=7)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d'),
            )
            if df.empty:
                return None
            latest = df.iloc[0]
            return {
                'code': stock_code, 'price': float(latest['close']),
                'open': float(latest['open']), 'high': float(latest['high']),
                'low': float(latest['low']), 'volume': int(latest['vol']),
                'amount': float(latest['amount']), 'date': latest['trade_date'],
            }
        except PermissionError:
            return None
        except Exception as e:
            logger.error(f"Tushare 获取实时行情失败 {stock_code}: {e}")
            raise

    @provider(FunctionType.KLINE_DAILY, FunctionType.KLINE_WEEKLY, FunctionType.KLINE_MONTHLY)
    async def get_kline(self, stock_code: str, period: str = "day",
                        start_date: str = None, end_date: str = None,
                        count: int = 100) -> Optional[List[Dict]]:
        if not self._ts_pro:
            return None
        try:
            period_map = {'day': 'daily', 'week': 'weekly', 'month': 'monthly'}
            api_name = period_map.get(period, 'daily')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                days = count * 2 if period == 'day' else count * 10
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            df = self.call_tushare_api(api_name, ts_code=stock_code,
                                       start_date=start_date, end_date=end_date)
            if df.empty:
                return None
            df = df.head(count)
            return [{
                'code': stock_code, 'date': str(row['trade_date']),
                'open': float(row['open']), 'close': float(row['close']),
                'high': float(row['high']), 'low': float(row['low']),
                'volume': int(row['vol']), 'amount': float(row['amount']),
            } for _, row in df.iterrows()][::-1]
        except PermissionError:
            return None
        except Exception as e:
            logger.error(f"Tushare 获取K线失败 {stock_code}: {e}")
            raise

    # ==================== 财务数据 ====================

    @provider(FunctionType.FINANCIAL_INDICATOR)
    async def get_financial_indicator(self, stock_code: str) -> Optional[Dict]:
        if not self._ts_pro:
            return None
        try:
            df = self.call_tushare_api(
                'fina_indicator', ts_code=stock_code,
                start_date=(datetime.now() - timedelta(days=365)).strftime('%Y%m%d'),
            )
            if df.empty:
                return None
            latest = df.iloc[0]
            return {
                'pe_ttm': float(latest['pe_ttm']) if pd.notna(latest.get('pe_ttm')) else None,
                'pb': float(latest['pb']) if pd.notna(latest.get('pb')) else None,
                'roe': float(latest['roe']) / 100 if pd.notna(latest.get('roe')) else None,
            }
        except (PermissionError, Exception):
            return None

    @provider(FunctionType.BALANCE_SHEET)
    async def get_balance_sheet(self, stock_code: str) -> Optional[Dict]:
        if not self._ts_pro:
            return None
        try:
            df = self.call_tushare_api(
                'balancesheet', ts_code=stock_code,
                start_date=(datetime.now() - timedelta(days=365)).strftime('%Y%m%d'),
            )
            if df.empty:
                return None
            latest = df.iloc[0]
            ta = float(latest['total_assets']) if pd.notna(latest.get('total_assets')) else None
            tl = float(latest['total_liab']) if pd.notna(latest.get('total_liab')) else None
            return {
                'total_assets': ta, 'total_liab': tl,
                'total_equity': float(latest['total_hldr_eqy_exc_min_int']) if pd.notna(latest.get('total_hldr_eqy_exc_min_int')) else None,
                'debt_ratio': (tl / ta) if ta and tl else None,
            }
        except (PermissionError, Exception):
            return None

    @provider(FunctionType.MONEY_FLOW)
    async def get_money_flow(self, stock_code: str, days: int = 5) -> Optional[List[Dict]]:
        if not self._ts_pro:
            return None
        try:
            df = self.call_tushare_api('moneyflow', ts_code=stock_code, limit=days)
            if df.empty:
                return None
            return [{'date': row['trade_date'], 'net_mf_amount': float(row['net_mf_amount'])}
                    for _, row in df.iterrows()]
        except (PermissionError, Exception):
            return None

    @provider(FunctionType.STOCK_LIST)
    async def get_stock_list(self) -> Optional[List[Dict]]:
        if not self._ts_pro:
            return None
        try:
            df = self.call_tushare_api('stock_basic', list_status='L')
            if df.empty:
                return None
            return [{'code': row['ts_code'], 'name': row['name'], 'industry': row.get('industry')}
                    for _, row in df.iterrows()]
        except (PermissionError, Exception):
            return None

    # ==================== 市场情绪 ====================

    @provider(FunctionType.MARKET_SENTIMENT)
    async def get_market_sentiment(self) -> Optional[Dict]:
        """获取最近交易日市场情绪（涨跌统计）"""
        if not self._ts_pro:
            return None
        try:
            for days_back in range(8):
                trade_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y%m%d')
                df = self.call_tushare_api('daily', trade_date=trade_date,
                                             start_date=trade_date, end_date=trade_date)
                if df.empty:
                    continue
                total_count = len(df)
                df['change_pct'] = ((df['close'] - df['pre_close']) / df['pre_close'] * 100).round(2)
                up_count = int((df['change_pct'] > 0).sum())
                down_count = int((df['change_pct'] < 0).sum())
                flat_count = int((df['change_pct'] == 0).sum())
                return {
                    'total_count': total_count,
                    'up_count': up_count, 'down_count': down_count, 'flat_count': flat_count,
                    'limit_up': int((df['change_pct'] >= 9.9).sum()),
                    'limit_down': int((df['change_pct'] <= -9.9).sum()),
                    'market_breadth': round(up_count / total_count * 100, 2) if total_count else 0,
                    'avg_change_pct': round(float(df['change_pct'].mean()), 2) if not df.empty else None,
                    'trade_date': trade_date,
                    'data_quality': 'full' if total_count >= 5000 else 'partial',
                    'data_source': 'tushare',
                }
            return None
        except (PermissionError, Exception) as e:
            logger.error(f"Tushare 获取市场情绪失败: {e}")
            return None

    async def get_historical_sentiment(self, trade_date: date) -> Optional[Dict]:
        """获取指定日期的市场情绪（公开方法，供回填逻辑使用）

        替代 background_updater 中对 _call_tushare_api 私有方法的直接调用。
        """
        if not self._ts_pro:
            return None
        try:
            trade_date_str = trade_date.strftime('%Y%m%d')
            df = self.call_tushare_api('daily', trade_date=trade_date_str,
                                         start_date=trade_date_str, end_date=trade_date_str)
            if df.empty:
                return None
            total_count = len(df)
            df['change_pct'] = ((df['close'] - df['pre_close']) / df['pre_close'] * 100).round(2)
            up_count = int((df['change_pct'] > 0).sum())
            down_count = int((df['change_pct'] < 0).sum())
            flat_count = int((df['change_pct'] == 0).sum())
            avg_change_pct = df['change_pct'].mean()
            return {
                'total_count': total_count,
                'up_count': up_count, 'down_count': down_count, 'flat_count': flat_count,
                'limit_up': int((df['change_pct'] >= 9.9).sum()),
                'limit_down': int((df['change_pct'] <= -9.9).sum()),
                'market_breadth': round(up_count / total_count * 100, 2),
                'avg_change_pct': round(float(avg_change_pct), 2) if pd.notna(avg_change_pct) else None,
                'trade_date': trade_date_str,
                'data_quality': 'full' if total_count >= 5000 else 'partial',
                'data_source': 'tushare',
            }
        except Exception as e:
            logger.error(f"Tushare 获取 {trade_date} 市场情绪失败: {e}")
            return None
