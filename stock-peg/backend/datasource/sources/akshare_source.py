"""AKShare 数据源实现 - 整合自 services/akshare_service.py

功能：
1. 所有 ak.* API 调用的统一入口
2. 代理禁用处理
3. 失败缓存机制
4. 板块代码映射缓存
5. 本地股票名称映射
"""
import os
import logging
import asyncio
import json
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from pathlib import Path

# ============================================
# CRITICAL: Disable proxy BEFORE importing akshare
# ============================================
_proxy_env_vars = (
    'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
    'ALL_PROXY', 'all_proxy'
)
for _var in _proxy_env_vars:
    os.environ.pop(_var, None)

os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

try:
    import requests
    requests.sessions.Session.trust_env = False
except Exception:
    pass

logger = logging.getLogger(__name__)

# 延迟导入 akshare
try:
    import akshare as ak
    import pandas as pd
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    logger.warning("Akshare 未安装，该数据源不可用")

from datasource.core.base import BaseDataSource
from datasource.core.constants import FunctionType, DataSourceType
from datasource.core.decorators import provider


class AkshareDataSource(BaseDataSource):
    """AKShare 数据源 - 免费开源数据源
    
    整合自 services/akshare_service.py，提供完整的 akshare API 封装。
    包含失败缓存、板块映射缓存、本地名称映射等增强功能。
    """

    def __init__(self):
        self._available = AKSHARE_AVAILABLE
        
        if self._available:
            logger.info("Akshare 数据源初始化成功（代理已禁用）")
        
        # 失败缓存：记录调用失败的股票代码，避免重复尝试
        self._failure_cache: Dict[str, Dict] = {}
        self._failure_cache_ttl = 3600  # 1小时
        
        # 股票列表缓存
        self._stock_list_cache = None
        self._stock_list_cache_time = None
        self._stock_list_cache_ttl = 3600 * 24  # 24小时
        
        # 板块代码映射缓存
        self._board_code_cache: Dict[str, Optional[str]] = {}
        self._board_code_cache_time = None
        self._board_code_cache_ttl = 3600 * 24
        self._board_code_cache_lock = asyncio.Lock()
        
        # 本地股票名称映射
        self._local_name_mapping: Dict[str, str] = {}
        self._local_mapping_file = None
        self._local_mapping_mtime = None
        self._load_local_name_mapping()

    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.AKSHARE

    @property
    def priority(self) -> int:
        return 20

    async def is_available(self) -> bool:
        return self._available

    # ==================== 内部方法 ====================

    async def _call_akshare(self, func, *args, **kwargs):
        """在线程中调用 akshare 同步函数，避免阻塞事件循环"""
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except Exception as e:
            logger.warning(f"Akshare {func.__name__} 失败: {e}")
            raise

    def _get_ak_module(self):
        """Get the akshare module object"""
        return ak

    def _load_local_name_mapping(self):
        """加载本地股票名称映射文件"""
        try:
            mapping_file = Path(__file__).parent.parent.parent / "data" / "stock_name_mapping.json"
            self._local_mapping_file = mapping_file
            
            if mapping_file.exists():
                file_mtime = os.path.getmtime(mapping_file)
                
                if self._local_mapping_mtime is not None and self._local_mapping_mtime == file_mtime:
                    return
                
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    self._local_name_mapping = json.load(f)
                
                self._local_mapping_mtime = file_mtime
                logger.info(f"Loaded {len(self._local_name_mapping)} stock name mappings from local file")
        except Exception as e:
            logger.error(f"Failed to load local stock name mapping: {str(e)}")
            self._local_name_mapping = {}

    def _check_and_reload_mapping(self):
        """检查文件是否更新，如果更新则重新加载"""
        try:
            if self._local_mapping_file and self._local_mapping_file.exists():
                file_mtime = os.path.getmtime(self._local_mapping_file)
                if self._local_mapping_mtime is None or self._local_mapping_mtime != file_mtime:
                    logger.info("Detected stock name mapping file update, reloading...")
                    self._load_local_name_mapping()
        except Exception as e:
            logger.error(f"Failed to check mapping file update: {str(e)}")

    def _save_local_name_mapping(self):
        """保存股票名称映射到本地文件"""
        try:
            mapping_file = Path(__file__).parent.parent.parent / "data" / "stock_name_mapping.json"
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self._local_name_mapping, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self._local_name_mapping)} stock name mappings to local file")
        except Exception as e:
            logger.error(f"Failed to save local stock name mapping: {str(e)}")

    def _is_in_failure_cache(self, stock_code: str, function_name: str) -> bool:
        """检查股票代码是否在失败缓存中"""
        cache_key = f"{stock_code}:{function_name}"
        if cache_key not in self._failure_cache:
            return False
        
        cache_entry = self._failure_cache[cache_key]
        elapsed = (datetime.now() - cache_entry['timestamp']).total_seconds()
        
        if elapsed > self._failure_cache_ttl:
            del self._failure_cache[cache_key]
            return False
        
        return True

    def _add_to_failure_cache(self, stock_code: str, function_name: str):
        """将股票代码添加到失败缓存"""
        cache_key = f"{stock_code}:{function_name}"
        self._failure_cache[cache_key] = {
            'timestamp': datetime.now(),
            'function': function_name
        }
        logger.debug(f"已将 {stock_code} 添加到失败缓存（函数: {function_name}）")

    # ==================== 行情数据 ====================

    @provider(FunctionType.REALTIME_QUOTE)
    async def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """获取实时行情"""
        if not self._available:
            return None
        
        try:
            if stock_code.startswith(('sh', 'sz', 'hk', 'us')):
                symbol = stock_code
                pure_code = stock_code[2:] if stock_code.startswith(('sh', 'sz')) else stock_code
            else:
                market = "sh" if stock_code.startswith("6") else "sz"
                symbol = f"{market}{stock_code}"
                pure_code = stock_code
            
            df = await self._call_akshare(ak.stock_zh_a_spot_em)
            
            stock_data = df[df['代码'] == pure_code]
            
            if stock_data.empty:
                logger.warning(f"Akshare 未找到股票 {stock_code}")
                return None
            
            row = stock_data.iloc[0]
            
            return {
                'code': stock_code,
                'name': row['名称'],
                'price': float(row['最新价']),
                'change': float(row['涨跌额']),
                'change_pct': float(row['涨跌幅']),
                'open': float(row['今开']),
                'high': float(row['最高']),
                'low': float(row['最低']),
                'volume': int(row['成交量']),
                'amount': float(row['成交额']),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Akshare 获取实时行情失败 {stock_code}: {str(e)}")
            return None

    @provider(FunctionType.KLINE_DAILY, FunctionType.KLINE_WEEKLY, FunctionType.KLINE_MONTHLY)
    async def get_kline(self, stock_code: str, period: str = "day", 
                       count: int = 100) -> Optional[List[Dict]]:
        """获取 K 线数据"""
        if not self._available:
            return None
        
        try:
            period_map = {
                'day': 'daily',
                'week': 'weekly',
                'month': 'monthly'
            }
            
            ak_period = period_map.get(period, 'daily')
            
            # 特殊处理：板块代码（BK开头）
            lower_code = stock_code.lower()
            if lower_code.startswith('bk'):
                return await self._get_board_kline(stock_code, period, count)
            
            # 使用代码格式转换工具
            from utils.index_code_converter import normalize_index_code
            
            normalized = normalize_index_code(stock_code)
            symbol = normalized['akshare_code']
            pure_code = normalized['pure_code']
            
            # 获取 K 线数据
            df = await self._call_akshare(ak.stock_zh_a_hist, symbol=symbol, period=ak_period, adjust="qfq")
            
            if df.empty:
                return None
            
            # 取最近 count 条数据
            df = df.tail(count)
            
            # 转换格式
            klines = []
            for _, row in df.iterrows():
                klines.append({
                    'code': pure_code,
                    'date': str(row['日期']),
                    'open': float(row['开盘']),
                    'close': float(row['收盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'volume': int(row['成交量']),
                    'amount': float(row['成交额'])
                })
            
            return klines
            
        except Exception as e:
            logger.error(f"Akshare 获取 K 线失败 {stock_code}: {str(e)}")
            return None

    async def _get_board_kline(self, board_code: str, period: str = "day", count: int = 100) -> Optional[List[Dict]]:
        """获取板块K线数据"""
        try:
            board_name = await self._get_board_name(board_code)
            if not board_name:
                logger.warning(f"未找到板块 {board_code} 的名称")
                return None
            
            df = await self._call_akshare(ak.stock_board_industry_hist_em, symbol=board_name)
            
            if df.empty:
                return None
            
            df = df.tail(count)
            
            klines = []
            for _, row in df.iterrows():
                klines.append({
                    'code': board_code,
                    'date': str(row['日期']),
                    'open': float(row['开盘']),
                    'close': float(row['收盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'volume': int(row['成交量']),
                    'amount': float(row['成交额'])
                })
            
            logger.info(f"Akshare 获取板块K线成功: {board_code} ({board_name}), {len(klines)}条")
            return klines
            
        except Exception as e:
            logger.error(f"Akshare 获取板块K线失败 {board_code}: {str(e)}")
            return None

    async def _get_board_name(self, board_code: str) -> Optional[str]:
        """根据板块代码获取板块名称（带缓存和并发锁）"""
        cache_key = board_code.lower()
        
        if cache_key in self._board_code_cache:
            return self._board_code_cache[cache_key]
        
        async with self._board_code_cache_lock:
            if cache_key in self._board_code_cache:
                return self._board_code_cache[cache_key]
            
            if self._board_code_cache_time:
                elapsed = (datetime.now() - self._board_code_cache_time).total_seconds()
                if elapsed > self._board_code_cache_ttl:
                    self._board_code_cache.clear()
                    self._board_code_cache_time = None
            
            if self._board_code_cache_time and self._board_code_cache:
                return self._board_code_cache.get(cache_key)
            
            try:
                df = await self._call_akshare(ak.stock_board_industry_name_em)
                
                if df.empty:
                    self._board_code_cache[cache_key] = None
                    self._board_code_cache_time = datetime.now()
                    return None
                
                for _, row in df.iterrows():
                    code = str(row['板块代码']).lower()
                    name = row['板块名称']
                    self._board_code_cache[code] = name
                self._board_code_cache_time = datetime.now()
                logger.info(f"已缓存 {len(self._board_code_cache)} 个板块代码映射")
                
                matched_name = self._board_code_cache.get(cache_key)
                
                if not matched_name:
                    cache_key_failure = f"board_not_found:{cache_key}"
                    if cache_key_failure not in self._failure_cache:
                        logger.warning(f"板块代码 {board_code} 不在 akshare 行业板块列表中")
                        self._failure_cache[cache_key_failure] = {
                            'timestamp': datetime.now(),
                            'function': '_get_board_name'
                        }
                
                return matched_name
                
            except Exception as e:
                logger.error(f"获取板块名称失败 {board_code}: {str(e)}")
                self._board_code_cache[cache_key] = None
                self._board_code_cache_time = datetime.now()
                return None

    @provider(FunctionType.KLINE_MINUTE)
    async def get_intraday_data(self, stock_code: str) -> Optional[Dict]:
        """获取分时数据"""
        if not self._available:
            return None
        
        try:
            market = "sh" if stock_code.startswith("6") else "sz"
            symbol = f"{market}{stock_code}"
            
            df = await self._call_akshare(ak.stock_zh_a_hist_min_em, symbol=symbol, period="1", adjust="")
            
            if df.empty:
                return None
            
            intraday_data = []
            for _, row in df.iterrows():
                intraday_data.append({
                    'time': str(row['时间']),
                    'price': float(row['收盘']),
                    'volume': int(row['成交量']),
                    'amount': float(row['成交额']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                })
            
            total_amount = sum([d['amount'] for d in intraday_data])
            total_volume = sum([d['volume'] for d in intraday_data])
            avg_price = total_amount / total_volume if total_volume > 0 else 0
            
            pre_close = intraday_data[0]['price'] if intraday_data else 0
            
            return {
                'code': stock_code,
                'data': intraday_data,
                'avg_price': avg_price,
                'pre_close': pre_close,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Akshare 获取分时数据失败 {stock_code}: {str(e)}")
            return None

    @provider(FunctionType.INDEX_KLINE)
    async def get_index_kline(self, index_code: str, period: str = "day", 
                             count: int = 100) -> Optional[List[Dict]]:
        """获取指数 K 线数据"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.stock_zh_index_daily, 
                symbol=f"sh{index_code}" if index_code.startswith("0") else f"sz{index_code}")
            
            if df.empty:
                return None
            
            df = df.tail(count)
            
            klines = []
            for _, row in df.iterrows():
                date_value = row.get('date')
                if pd.isna(date_value):
                    date_value = row.get('日期')
                if pd.isna(date_value):
                    date_value = row.name

                close_value = row.get('close')
                if pd.isna(close_value):
                    close_value = row.get('收盘')
                close = float(close_value) if pd.notna(close_value) else 0

                open_value = row.get('open')
                if pd.isna(open_value):
                    open_value = row.get('开盘')

                high_value = row.get('high')
                if pd.isna(high_value):
                    high_value = row.get('最高')

                low_value = row.get('low')
                if pd.isna(low_value):
                    low_value = row.get('最低')

                volume_value = row.get('volume')
                if pd.isna(volume_value):
                    volume_value = row.get('成交量')
                volume = float(volume_value) if pd.notna(volume_value) else 0

                amount_value = row.get('amount')
                if pd.isna(amount_value):
                    amount_value = row.get('成交额')
                amount = float(amount_value) if pd.notna(amount_value) else 0
                if amount <= 0 and volume > 0 and close > 0:
                    amount = volume * close
                
                klines.append({
                    'code': index_code,
                    'date': str(date_value),
                    'open': float(open_value) if pd.notna(open_value) else close,
                    'close': close,
                    'high': float(high_value) if pd.notna(high_value) else close,
                    'low': float(low_value) if pd.notna(low_value) else close,
                    'volume': volume,
                    'amount': amount,
                })
            
            return klines
            
        except Exception as e:
            logger.error(f"获取指数 K 线失败 {index_code}: {str(e)}")
            return None

    # ==================== 财务数据 ====================

    @provider(FunctionType.FINANCIAL_INDICATOR)
    async def get_financial_indicator(self, stock_code: str) -> Optional[Dict]:
        """获取财务指标"""
        if not self._available:
            return None
        
        function_name = "get_financial_indicator"
        if self._is_in_failure_cache(stock_code, function_name):
            logger.debug(f"跳过 {stock_code} 的财务指标请求（在失败缓存中）")
            return None
        
        try:
            df = await self._call_akshare(ak.stock_financial_analysis_indicator, symbol=stock_code)
            
            if df.empty:
                logger.warning(f"Akshare 未找到股票 {stock_code} 的财务指标数据")
                return None
            
            latest = df.iloc[0]
            
            pe_value = None
            for col in ['市盈率', '市盈(TTM)', 'PE(TTM)', 'pe_ttm']:
                if col in latest.index and pd.notna(latest.get(col)):
                    pe_value = float(latest.get(col))
                    break
            
            pb_value = None
            for col in ['市净率', 'PB', 'pb']:
                if col in latest.index and pd.notna(latest.get(col)):
                    pb_value = float(latest.get(col))
                    break
            
            roe_value = None
            for col in ['净资产收益率', 'ROE', 'roe']:
                if col in latest.index and pd.notna(latest.get(col)):
                    roe_value = float(latest.get(col)) / 100
                    break
            
            roa_value = None
            for col in ['总资产净利率', 'ROA', 'roa']:
                if col in latest.index and pd.notna(latest.get(col)):
                    roa_value = float(latest.get(col)) / 100
                    break
            
            gross_margin_value = None
            for col in ['销售毛利率', '毛利率', 'gross_margin']:
                if col in latest.index and pd.notna(latest.get(col)):
                    gross_margin_value = float(latest.get(col)) / 100
                    break
            
            net_margin_value = None
            for col in ['销售净利率', '净利率', 'net_margin']:
                if col in latest.index and pd.notna(latest.get(col)):
                    net_margin_value = float(latest.get(col)) / 100
                    break
            
            debt_ratio_value = None
            for col in ['资产负债率', 'debt_ratio']:
                if col in latest.index and pd.notna(latest.get(col)):
                    debt_ratio_value = float(latest.get(col)) / 100
                    break
            
            return {
                'pe_ttm': pe_value,
                'pb': pb_value,
                'roe': roe_value,
                'roa': roa_value,
                'gross_margin': gross_margin_value,
                'net_margin': net_margin_value,
                'debt_ratio': debt_ratio_value,
            }
            
        except Exception as e:
            logger.error(f"Akshare 获取财务指标失败 {stock_code}: {str(e)}", exc_info=True)
            self._add_to_failure_cache(stock_code, function_name)
            return None

    @provider(FunctionType.BALANCE_SHEET)
    async def get_balance_sheet(self, stock_code: str) -> Optional[Dict]:
        """获取资产负债表"""
        if not self._available:
            return None
        
        function_name = "get_balance_sheet"
        if self._is_in_failure_cache(stock_code, function_name):
            return None
        
        try:
            df = await self._call_akshare(ak.stock_balance_sheet_by_report_em, symbol=stock_code)
            
            if df is None or df.empty:
                self._add_to_failure_cache(stock_code, function_name)
                return None
            
            latest = df.iloc[0]
            
            total_assets = float(latest.get('资产总计', 0)) if latest.get('资产总计') else None
            total_liab = float(latest.get('负债合计', 0)) if latest.get('负债合计') else None
            
            return {
                'total_assets': total_assets,
                'total_liab': total_liab,
                'total_equity': float(latest.get('所有者权益合计', 0)) if latest.get('所有者权益合计') else None,
                'debt_ratio': (total_liab / total_assets) if total_assets and total_liab else None,
            }
            
        except Exception as e:
            logger.error(f"Akshare 获取资产负债表失败 {stock_code}: {str(e)}")
            self._add_to_failure_cache(stock_code, function_name)
            return None

    @provider(FunctionType.INCOME_STATEMENT)
    async def get_income_statement(self, stock_code: str) -> Optional[Dict]:
        """获取利润表"""
        if not self._available:
            return None
        
        function_name = "get_income_statement"
        if self._is_in_failure_cache(stock_code, function_name):
            return None
        
        try:
            df = await self._call_akshare(ak.stock_profit_sheet_by_report_em, symbol=stock_code)
            
            if df is None or df.empty:
                self._add_to_failure_cache(stock_code, function_name)
                return None
            
            latest = df.iloc[0]
            
            revenue = float(latest.get('营业总收入', 0)) if latest.get('营业总收入') else None
            net_profit = float(latest.get('净利润', 0)) if latest.get('净利润') else None
            
            return {
                'revenue': revenue,
                'net_profit': net_profit,
                'net_margin': (net_profit / revenue) if revenue and net_profit else None,
            }
            
        except Exception as e:
            logger.error(f"Akshare 获取利润表失败 {stock_code}: {str(e)}")
            self._add_to_failure_cache(stock_code, function_name)
            return None

    @provider(FunctionType.FINANCIAL_REPORT)
    async def get_financial_report_sina(self, stock_code: str, report_type: str = '利润表') -> Optional[Dict]:
        """使用新浪财经接口获取财务报表数据"""
        if not self._available:
            return None
        
        function_name = f"get_financial_report_sina_{report_type}"
        if self._is_in_failure_cache(stock_code, function_name):
            return None
        
        try:
            market = "sh" if stock_code.startswith("6") else "sz"
            symbol = f"{market}{stock_code}"
            
            try:
                df = await self._call_akshare(ak.stock_financial_report_sina, stock=symbol, symbol=report_type)
            except json.JSONDecodeError as json_err:
                logger.warning(f"新浪财经API返回无效JSON {stock_code}: {str(json_err)}")
                self._add_to_failure_cache(stock_code, function_name)
                return None
            except Exception as inner_e:
                logger.warning(f"Akshare 内部函数调用失败 {stock_code}: {str(inner_e)}")
                self._add_to_failure_cache(stock_code, function_name)
                return None
            
            if df is None or df.empty:
                self._add_to_failure_cache(stock_code, function_name)
                return None
            
            return {
                'data': df,
                'report_type': report_type
            }
            
        except Exception as e:
            logger.error(f"新浪财经获取{report_type}失败 {stock_code}: {str(e)}")
            return None

    # ==================== 市场数据 ====================

    @provider(FunctionType.STOCK_LIST)
    async def get_stock_list(self) -> Any:
        """获取股票列表"""
        if not self._available:
            return None
        return await self._call_akshare(ak.stock_info_a_code_name)

    @provider(FunctionType.STOCK_INFO)
    async def get_stock_info(self, stock_code: str) -> Optional[Dict]:
        """获取股票基本信息"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.stock_info_a_code_name)
            
            stock_data = df[df['code'] == stock_code]
            
            if stock_data.empty:
                return None
            
            return {
                'code': stock_code,
                'name': stock_data.iloc[0]['name'],
            }
            
        except Exception as e:
            logger.error(f"Akshare 获取股票信息失败 {stock_code}: {str(e)}")
            return None

    @provider(FunctionType.STOCK_SEARCH)
    async def search_stock_by_name(self, stock_name: str) -> Optional[str]:
        """根据股票名称搜索股票代码"""
        search_name = stock_name.strip()
        
        self._check_and_reload_mapping()
        
        # 1. 优先使用本地映射
        if search_name in self._local_name_mapping:
            code = self._local_name_mapping[search_name]
            return code
        
        # 2. 尝试模糊匹配本地映射
        for name, code in self._local_name_mapping.items():
            if search_name in name or name in search_name:
                return code
        
        # 3. 网络查询
        if not self._available:
            return None
        
        try:
            now = datetime.now()
            if (self._stock_list_cache is not None and 
                self._stock_list_cache_time is not None and 
                (now - self._stock_list_cache_time).total_seconds() < self._stock_list_cache_ttl):
                df = self._stock_list_cache
            else:
                df = await self._call_akshare(ak.stock_info_a_code_name)
                if df is None or df.empty:
                    df = await self._call_akshare(ak.stock_zh_a_spot_em)
                
                if df is not None and not df.empty:
                    self._stock_list_cache = df
                    self._stock_list_cache_time = now
                else:
                    return None
            
            if '名称' in df.columns and '代码' in df.columns:
                name_col = '名称'
                code_col = '代码'
            elif 'name' in df.columns and 'code' in df.columns:
                name_col = 'name'
                code_col = 'code'
            else:
                return None
            
            # 精确匹配
            match = df[df[name_col] == search_name]
            if not match.empty:
                code = str(match.iloc[0][code_col])
                code = code.zfill(6) if code.isdigit() else code
                self._local_name_mapping[search_name] = code
                self._save_local_name_mapping()
                return code
            
            # 模糊匹配
            match = df[df[name_col].str.contains(search_name, na=False)]
            if not match.empty:
                match = match.copy()
                match['name_len'] = match[name_col].str.len()
                match = match.sort_values('name_len')
                code = str(match.iloc[0][code_col])
                code = code.zfill(6) if code.isdigit() else code
                self._local_name_mapping[search_name] = code
                self._save_local_name_mapping()
                return code
            
            return None
            
        except Exception as e:
            logger.error(f"Akshare 搜索股票名称失败 {stock_name}: {str(e)}")
            return None

    # ==================== 市场情绪 ====================

    @staticmethod
    def _is_complete_market_sentiment(sentiment: Optional[Dict]) -> bool:
        if not sentiment:
            return False
        total_count = int(sentiment.get('total_count') or 0)
        if total_count < 5000:
            return False
        if sentiment.get('data_quality') != 'full':
            return False
        up_count = int(sentiment.get('up_count') or 0)
        down_count = int(sentiment.get('down_count') or 0)
        flat_count = int(sentiment.get('flat_count') or 0)
        if up_count <= 0 and down_count <= 0 and flat_count <= 0:
            return False
        return (up_count + down_count + flat_count) >= int(total_count * 0.95)

    @provider(FunctionType.MARKET_SENTIMENT)
    async def get_market_sentiment(self) -> Optional[Dict]:
        """获取市场情绪统计"""
        if not self._available:
            logger.warning("AKShare 服务不可用，尝试使用 Tushare")
        
        # 优先尝试Tushare
        from datasource import get_datasource, DataSourceType
        
        tushare = get_datasource().get_source(DataSourceType.TUSHARE)
        if tushare:
            try:
                if await tushare.is_available():
                    sentiment = await tushare.get_market_sentiment()
                    if self._is_complete_market_sentiment(sentiment):
                        return sentiment
            except Exception as e:
                logger.warning(f"Tushare 获取市场情绪数据失败: {str(e)}")
        
        # 尝试AKShare数据源
        data_sources = [
            {
                'name': '东方财富',
                'function': ak.stock_zh_a_spot_em,
                'change_col': '涨跌幅',
                'code_col': '代码',
            },
            {
                'name': '腾讯财经',
                'function': ak.stock_zh_a_spot,
                'change_col': '涨跌幅',
                'code_col': '代码',
            }
        ]
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            for source in data_sources:
                try:
                    df = await self._call_akshare(source['function'])
                    
                    if df.empty:
                        continue

                    if source['code_col'] in df.columns:
                        df = df[df[source['code_col']].astype(str).str.fullmatch(r'\d{6}', na=False)]
                    if df.empty or source['change_col'] not in df.columns:
                        continue

                    change_pct = pd.to_numeric(df[source['change_col']], errors='coerce')
                    valid_change_pct = change_pct.dropna()
                    if valid_change_pct.empty:
                        continue
                    
                    total_count = len(valid_change_pct)
                    
                    if total_count < 5000:
                        if attempt < max_retries - 1:
                            continue
                    else:
                        logger.info(f"[OK] {source['name']} 成功获取 {total_count} 只股票数据")
                    
                    limit_up = int((valid_change_pct >= 9.9).sum())
                    limit_down = int((valid_change_pct <= -9.9).sum())
                    
                    up_count = int((valid_change_pct > 0).sum())
                    down_count = int((valid_change_pct < 0).sum())
                    flat_count = int((valid_change_pct == 0).sum())
                    
                    market_breadth = (up_count / total_count * 100) if total_count > 0 else 0
                    avg_change_pct = valid_change_pct.mean()
                    data_quality = 'full' if total_count >= 5000 else 'partial'
                    
                    return {
                        'total_count': total_count,
                        'up_count': up_count,
                        'down_count': down_count,
                        'flat_count': flat_count,
                        'limit_up': limit_up,
                        'limit_down': limit_down,
                        'market_breadth': round(market_breadth, 2),
                        'avg_change_pct': round(float(avg_change_pct), 2) if pd.notna(avg_change_pct) else None,
                        'timestamp': datetime.now().isoformat(),
                        'data_quality': data_quality,
                        'data_source': source['name'],
                    }
                    
                except Exception as e:
                    logger.error(f"{source['name']} 获取失败 (第 {attempt + 1} 次): {str(e)}")
                    continue
            
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
        
        logger.error("已达到最大重试次数，所有数据源均失败")
        return None

    # ==================== 板块数据 ====================

    @provider(FunctionType.INDUSTRY_SECTORS)
    async def get_industry_sectors(self) -> Optional[List[Dict]]:
        """获取行业板块列表"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.stock_board_industry_name_em)
            
            if df.empty:
                return None
            
            sectors = []
            for _, row in df.iterrows():
                sectors.append({
                    'code': row['板块代码'],
                    'name': row['板块名称'],
                    'change_pct': float(row['涨跌幅']) if pd.notna(row.get('涨跌幅')) else None,
                    'up_count': int(row['上涨家数']) if pd.notna(row.get('上涨家数')) else 0,
                    'down_count': int(row['下跌家数']) if pd.notna(row.get('下跌家数')) else 0,
                })
            
            return sectors
            
        except Exception as e:
            logger.error(f"获取行业板块列表失败: {str(e)}")
            return None

    @provider(FunctionType.CONCEPT_SECTORS)
    async def get_concept_sectors(self) -> Optional[List[Dict]]:
        """获取概念板块列表"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.stock_board_concept_name_em)
            
            if df.empty:
                return None
            
            sectors = []
            for _, row in df.iterrows():
                sectors.append({
                    'code': row['板块代码'],
                    'name': row['板块名称'],
                    'change_pct': float(row['涨跌幅']) if pd.notna(row.get('涨跌幅')) else None,
                    'up_count': int(row['上涨家数']) if pd.notna(row.get('上涨家数')) else 0,
                    'down_count': int(row['下跌家数']) if pd.notna(row.get('下跌家数')) else 0,
                })
            
            return sectors
            
        except Exception as e:
            logger.error(f"获取概念板块列表失败: {str(e)}")
            return None

    @provider(FunctionType.SECTOR_STOCKS)
    async def get_sector_stocks(self, sector_name: str) -> Optional[List[Dict]]:
        """获取板块成分股"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.stock_board_industry_cons_em, symbol=sector_name)
            
            if df.empty:
                return None
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': row['代码'],
                    'name': row['名称'],
                    'price': float(row['最新价']) if pd.notna(row.get('最新价')) else None,
                    'change_pct': float(row['涨跌幅']) if pd.notna(row.get('涨跌幅')) else None,
                    'amount': float(row['成交额']) if pd.notna(row.get('成交额')) else None,
                })
            
            return stocks
            
        except Exception as e:
            logger.error(f"获取板块成分股失败 {sector_name}: {str(e)}")
            return None

    # ==================== 资金流向 ====================

    @provider(FunctionType.MONEY_FLOW)
    async def get_individual_fund_flow(self, stock_code: str) -> Optional[Dict]:
        """获取个股资金流向"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.stock_individual_fund_flow, 
                stock=stock_code, market="sh" if stock_code.startswith("6") else "sz")
            
            if df.empty:
                return None
            
            latest = df.iloc[0]
            
            return {
                'code': stock_code,
                'date': str(latest['日期']),
                'main_net_inflow': float(latest['主力净流入-净额']) if pd.notna(latest.get('主力净流入-净额')) else None,
                'main_net_inflow_pct': float(latest['主力净流入-净占比']) if pd.notna(latest.get('主力净流入-净占比')) else None,
                'retail_net_inflow': float(latest['小单净流入-净额']) if pd.notna(latest.get('小单净流入-净额')) else None,
                'retail_net_inflow_pct': float(latest['小单净流入-净占比']) if pd.notna(latest.get('小单净流入-净占比')) else None,
            }
            
        except Exception as e:
            logger.error(f"获取个股资金流向失败 {stock_code}: {str(e)}")
            return None

    @provider(FunctionType.SECTOR_MONEY_FLOW)
    async def get_sector_fund_flow(self, sector_type: str = "行业") -> Optional[List[Dict]]:
        """获取板块资金流向"""
        if not self._available:
            return None
        
        try:
            if sector_type == "行业":
                df = await self._call_akshare(ak.stock_sector_fund_flow_rank, indicator="今日", sector_type="行业资金流")
            else:
                df = await self._call_akshare(ak.stock_sector_fund_flow_rank, indicator="今日", sector_type="概念资金流")
            
            if df.empty:
                return None
            
            flows = []
            for _, row in df.iterrows():
                flows.append({
                    'name': row['名称'],
                    'change_pct': float(row['涨跌幅']) if pd.notna(row.get('涨跌幅')) else None,
                    'main_net_inflow': float(row['主力净流入-净额']) if pd.notna(row.get('主力净流入-净额')) else None,
                    'main_net_inflow_pct': float(row['主力净流入-净占比']) if pd.notna(row.get('主力净流入-净占比')) else None,
                })
            
            return flows
            
        except Exception as e:
            logger.error(f"获取板块资金流向失败: {str(e)}")
            return None

    @provider(FunctionType.MARKET_MONEY_FLOW)
    async def get_market_fund_flow(self, days: int = 20) -> Optional[List[Dict]]:
        """获取大盘资金流向数据"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.stock_market_fund_flow)
            
            if df.empty:
                return None
            
            df = df.head(days)
            
            flows = []
            for _, row in df.iterrows():
                flows.append({
                    'date': str(row['日期']) if '日期' in row else '',
                    'amount': float(row['成交额']) if pd.notna(row.get('成交额')) else 0,
                    'main_net_inflow': float(row['主力净流入-净额']) if pd.notna(row.get('主力净流入-净额')) else 0,
                    'main_net_inflow_pct': float(row['主力净流入-净占比']) if pd.notna(row.get('主力净流入-净占比')) else 0,
                    'super_net_inflow': float(row.get('超大单净流入-净额', 0)) if pd.notna(row.get('超大单净流入-净额')) else 0,
                    'big_net_inflow': float(row.get('大单净流入-净额', 0)) if pd.notna(row.get('大单净流入-净额')) else 0,
                    'medium_net_inflow': float(row.get('中单净流入-净额', 0)) if pd.notna(row.get('中单净流入-净额')) else 0,
                    'small_net_inflow': float(row.get('小单净流入-净额', 0)) if pd.notna(row.get('小单净流入-净额')) else 0,
                })
            
            return flows
            
        except Exception as e:
            logger.error(f"获取大盘资金流数据失败: {str(e)}", exc_info=True)
            return None

    # ==================== 龙虎榜 ====================

    @provider(FunctionType.LHB_DETAIL)
    async def get_lhb_detail(self, start_date: str, end_date: str) -> Optional[List[Dict]]:
        """获取龙虎榜详情"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.stock_lhb_detail_em, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return None
            
            details = []
            for _, row in df.iterrows():
                details.append({
                    'code': row['代码'],
                    'name': row['名称'],
                    'price': float(row['收盘价']) if pd.notna(row.get('收盘价')) else None,
                    'change_pct': float(row['涨跌幅']) if pd.notna(row.get('涨跌幅')) else None,
                    'turnover_rate': float(row['换手率']) if pd.notna(row.get('换手率')) else None,
                    'net_buy': float(row['龙虎榜净买额']) if pd.notna(row.get('龙虎榜净买额')) else None,
                    'buy_amount': float(row['龙虎榜买入额']) if pd.notna(row.get('龙虎榜买入额')) else None,
                    'sell_amount': float(row['龙虎榜卖出额']) if pd.notna(row.get('龙虎榜卖出额')) else None,
                    'reason': row.get('上榜原因', ''),
                })
            
            return details
            
        except Exception as e:
            logger.error(f"获取龙虎榜详情失败: {str(e)}")
            return None

    # ==================== 港股美股ETF ====================

    @provider(FunctionType.HK_QUOTE)
    async def get_hk_spot(self) -> Optional[List[Dict]]:
        """获取港股实时行情"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.stock_hk_spot_em)
            
            if df.empty:
                return None
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': row['代码'],
                    'name': row['名称'],
                    'price': float(row['最新价']) if pd.notna(row.get('最新价')) else None,
                    'change_pct': float(row['涨跌幅']) if pd.notna(row.get('涨跌幅')) else None,
                    'volume': float(row['成交量']) if pd.notna(row.get('成交量')) else None,
                    'amount': float(row['成交额']) if pd.notna(row.get('成交额')) else None,
                })
            
            return stocks
            
        except Exception as e:
            logger.error(f"获取港股实时行情失败: {str(e)}")
            return None

    @provider(FunctionType.US_QUOTE)
    async def get_us_spot(self) -> Optional[List[Dict]]:
        """获取美股实时行情"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.stock_us_spot_em)
            
            if df.empty:
                return None
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': row['代码'],
                    'name': row['名称'],
                    'price': float(row['最新价']) if pd.notna(row.get('最新价')) else None,
                    'change_pct': float(row['涨跌幅']) if pd.notna(row.get('涨跌幅')) else None,
                    'volume': float(row['成交量']) if pd.notna(row.get('成交量')) else None,
                })
            
            return stocks
            
        except Exception as e:
            logger.error(f"获取美股实时行情失败: {str(e)}")
            return None

    @provider(FunctionType.ETF_QUOTE)
    async def get_etf_spot(self) -> Optional[List[Dict]]:
        """获取 ETF 实时行情"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.fund_etf_spot_em)
            
            if df.empty:
                return None
            
            etfs = []
            for _, row in df.iterrows():
                etfs.append({
                    'code': row['代码'],
                    'name': row['名称'],
                    'price': float(row['最新价']) if pd.notna(row.get('最新价')) else None,
                    'change_pct': float(row['涨跌幅']) if pd.notna(row.get('涨跌幅')) else None,
                    'volume': float(row['成交量']) if pd.notna(row.get('成交量')) else None,
                    'amount': float(row['成交额']) if pd.notna(row.get('成交额')) else None,
                })
            
            return etfs
            
        except Exception as e:
            logger.error(f"获取 ETF 实时行情失败: {str(e)}")
            return None

    # ==================== 宏观经济 ====================

    @provider(FunctionType.MACRO_CPI)
    async def get_china_cpi(self) -> Optional[List[Dict]]:
        """获取中国 CPI 数据"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.macro_china_cpi_yearly)
            
            if df.empty:
                return None
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'month': str(row['月份']),
                    'cpi': float(row['全国当月']) if pd.notna(row.get('全国当月')) else None,
                    'cpi_yoy': float(row['全国同比']) if pd.notna(row.get('全国同比')) else None,
                })
            
            return data[-12:]
            
        except Exception as e:
            logger.error(f"获取中国 CPI 数据失败: {str(e)}")
            return None

    @provider(FunctionType.MACRO_GDP)
    async def get_china_gdp(self) -> Optional[List[Dict]]:
        """获取中国 GDP 数据"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.macro_china_gdp_yearly)
            
            if df.empty:
                return None
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'quarter': str(row['季度']),
                    'gdp': float(row['国内生产总值-绝对值']) if pd.notna(row.get('国内生产总值-绝对值')) else None,
                    'gdp_yoy': float(row['国内生产总值-同比增长']) if pd.notna(row.get('国内生产总值-同比增长')) else None,
                })
            
            return data[-8:]
            
        except Exception as e:
            logger.error(f"获取中国 GDP 数据失败: {str(e)}")
            return None

    @provider(FunctionType.MACRO_PMI)
    async def get_china_pmi(self) -> Optional[List[Dict]]:
        """获取中国 PMI 数据"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.macro_china_pmi_yearly)
            
            if df.empty:
                return None
            
            data = []
            for _, row in df.iterrows():
                data.append({
                    'month': str(row['月份']),
                    'pmi': float(row['制造业-指数']) if pd.notna(row.get('制造业-指数')) else None,
                    'non_manufacturing_pmi': float(row['非制造业-指数']) if pd.notna(row.get('非制造业-指数')) else None,
                })
            
            return data[-12:]
            
        except Exception as e:
            logger.error(f"获取中国 PMI 数据失败: {str(e)}")
            return None

    # ==================== 北向资金 ====================

    @provider(FunctionType.NORTH_MONEY_FLOW)
    async def get_north_money_flow(self) -> Optional[Dict]:
        """获取北向资金流向"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.stock_hsgt_north_net_flow_in_em)
            
            if df.empty:
                return None
            
            latest = df.iloc[0]
            
            return {
                'date': str(latest['日期']),
                'net_inflow': float(latest['当日净流入']) if pd.notna(latest.get('当日净流入')) else None,
                'balance': float(latest['当日资金余额']) if pd.notna(latest.get('当日资金余额')) else None,
                'accumulate': float(latest['累计净流入']) if pd.notna(latest.get('累计净流入')) else None,
            }
            
        except Exception as e:
            logger.error(f"获取北向资金流向失败: {str(e)}")
            return None

    @provider(FunctionType.NORTH_MONEY_TOP10)
    async def get_north_money_top10(self) -> Optional[List[Dict]]:
        """获取北向资金持股前十"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.stock_hsgt_hold_stock_em, market="北向")
            
            if df.empty:
                return None
            
            stocks = []
            for _, row in df.head(10).iterrows():
                stocks.append({
                    'code': row['代码'],
                    'name': row['名称'],
                    'hold_amount': float(row['持股数量']) if pd.notna(row.get('持股数量')) else None,
                    'hold_value': float(row['持股市值']) if pd.notna(row.get('持股市值')) else None,
                    'hold_pct': float(row['持股比例']) if pd.notna(row.get('持股比例')) else None,
                })
            
            return stocks
            
        except Exception as e:
            logger.error(f"获取北向资金持股前十失败: {str(e)}")
            return None

    # ==================== 机构持仓 ====================

    @provider(FunctionType.INSTITUTION_HOLDINGS)
    async def get_institution_holdings(self, stock_code: str) -> Optional[List[Dict]]:
        """获取机构持仓数据"""
        if not self._available:
            return None
        
        try:
            df = await self._call_akshare(ak.stock_institute_hold_detail, symbol=stock_code)
            
            if df.empty:
                return None
            
            holdings = []
            for _, row in df.iterrows():
                holdings.append({
                    'date': str(row['持股日期']),
                    'institution': row['机构名称'],
                    'hold_amount': float(row['持股数量']) if pd.notna(row.get('持股数量')) else None,
                    'hold_pct': float(row['持股比例']) if pd.notna(row.get('持股比例')) else None,
                })
            
            return holdings
            
        except Exception as e:
            logger.error(f"获取机构持仓数据失败 {stock_code}: {str(e)}")
            return None
