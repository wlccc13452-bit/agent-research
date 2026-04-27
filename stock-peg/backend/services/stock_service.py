"""股票数据服务"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import re
import time
import pandas as pd

from config.settings import settings
from models import StockQuote, StockKLine, TechnicalIndicators
from services.log_service import log_service
from services.extended_cache import quote_cache

logger = logging.getLogger(__name__)


class StockService:
    """股票数据服务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StockService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.tencent_base = settings.tencent_api_base
        self.eastmoney_base = settings.eastmoney_api_base
        self.client = None  # 延迟获取 TencentDataSource 的 httpx client
        # 失败计数器，用于熔断机制
        self._tencent_fail_count = 0
        self._tencent_circuit_breaker = False
        self._circuit_breaker_reset_time = None
        
        # 通过 datasource 获取 Tushare 数据源
        from datasource import get_datasource, DataSourceType
        tushare_source = get_datasource().get_source(DataSourceType.TUSHARE)
        self.ts_pro = tushare_source if tushare_source else None
        if not self.ts_pro:
            # 检查 Akshare 是否可用
            akshare_source = get_datasource().get_source(DataSourceType.AKSHARE)
            if akshare_source:
                logger.info("未配置 Tushare Token，已启用 Akshare 作为备用数据源")
            else:
                logger.warning("未配置 Tushare Token，且 Akshare 不可用，部分数据将无法获取")
            
        # 记录无权限的 Tushare 接口，避免重复请求
        self._unauthorized_apis = set()
            
        self._initialized = True
    
    def _get_akshare_source(self):
        """获取 Akshare 数据源（辅助方法）"""
        from datasource import get_datasource, DataSourceType
        return get_datasource().get_source(DataSourceType.AKSHARE)

    def _get_tencent_client(self):
        """获取腾讯数据源的 httpx client（延迟初始化）"""
        if self.client is not None:
            return self.client
        from datasource import get_datasource, DataSourceType
        tencent_source = get_datasource().get_source(DataSourceType.TENCENT)
        if tencent_source and hasattr(tencent_source, '_client'):
            self.client = tencent_source._client
        return self.client

    async def _call_tushare(self, api_name: str, **kwargs) -> pd.DataFrame:
        """调用 Tushare API（通过 datasource 层）"""
        if not self.ts_pro:
            return pd.DataFrame()
        
        if api_name in self._unauthorized_apis:
            return pd.DataFrame()
        
        try:
            # 使用 TushareDataSource 的 call_tushare_api 方法
            df = self.ts_pro.call_tushare_api(api_name, **kwargs)
            return df
        except Exception as e:
            error_msg = str(e)
            if "没有接口访问权限" in error_msg:
                if api_name not in self._unauthorized_apis:
                    logger.warning(f"Tushare 接口 [{api_name}] 无权限，后续将自动跳过此接口请求。权限详情: {error_msg}")
                    self._unauthorized_apis.add(api_name)
                return pd.DataFrame()
            
            logger.warning(f"调用 Tushare 接口 [{api_name}] 失败（可能是临时网络问题）: {error_msg}")
            raise e
    
    async def _log_and_request(self, api_name: str, url: str, method: str = "GET", 
                                params: Optional[Dict] = None):
        """记录并执行HTTP请求（通过 datasource 的腾讯数据源 client）"""
        start_time = time.time()
        error = None
        response_status = None
        response_data = None
        
        try:
            client = self._get_tencent_client()
            if not client:
                raise Exception("腾讯数据源 httpx client 不可用")
            response = await client.get(url, params=params)
            response_status = response.status_code
            response.raise_for_status()
            response_data = response.text
            return response
        except Exception as e:
            error = str(e)
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            log_service.log_external_api_call(
                api_name=api_name,
                url=url,
                method=method,
                request_params=params,
                response_status=response_status,
                response_data=response_data[:500] if response_data else None,
                error=error,
                duration_ms=duration_ms
            )

    def _to_tencent_symbol(self, stock_code: str) -> str:
        symbol = (stock_code or "").strip()
        lower_symbol = symbol.lower()

        if lower_symbol.startswith(('sh', 'sz', 'hk', 'us', 'bk')):
            return lower_symbol

        suffix_match = re.match(r'^(\d{6})\.(sh|sz)$', lower_symbol)
        if suffix_match:
            code, market = suffix_match.groups()
            return f"{market}{code}"
        
        # 处理行业板块 (如 BK0897)
        if lower_symbol.startswith('bk') and len(lower_symbol) == 6:
            return lower_symbol

        prefix_match = re.match(r'^(sh|sz)(\d{6})$', lower_symbol)
        if prefix_match:
            market, code = prefix_match.groups()
            return f"{market}{code}"

        market = "sh" if symbol.startswith("6") else "sz"
        return f"{market}{symbol}"
    
    async def get_quote(self, stock_code: str, use_cache: bool = True) -> Optional[StockQuote]:
        """
        获取股票实时行情（带缓存优化）
        
        优化策略：
        1. 优先从缓存读取（1分钟有效期）
        2. 缓存未命中时，快速请求外部API（2秒超时）
        3. 腾讯API失败自动降级到Akshare
        4. 熔断机制：连续失败3次后暂停使用腾讯API 5分钟
        """
        try:
            # 1. 优先从缓存读取（除非强制刷新）
            if use_cache:
                cached_quote = await quote_cache.get(stock_code)
                if cached_quote:
                    logger.info(f"[TARGET] 从缓存获取行情数据: {stock_code}")
                    return StockQuote(**cached_quote)
            
            logger.info(f"[CHART] 开始获取行情数据: {stock_code}")
            
            # 2. 检查熔断状态
            if self._tencent_circuit_breaker:
                if datetime.now() > self._circuit_breaker_reset_time:
                    # 熔断恢复
                    logger.info(f"🔄 腾讯API熔断恢复，重新尝试")
                    self._tencent_circuit_breaker = False
                    self._tencent_fail_count = 0
                else:
                    logger.warning(f"[WARN]️ 腾讯API熔断中，直接使用备用数据源")
                    # 跳过腾讯API，直接使用Akshare
                    return await self._get_quote_from_akshare(stock_code)
            
            # 3. 构建腾讯股票API请求
            # [OK] 特殊处理指数代码
            if '.' in stock_code:
                # 指数代码格式: 000001.SH → sh000001 (腾讯API格式)
                parts = stock_code.split('.')
                market = parts[1].lower()
                full_code = f"{market}{parts[0]}"
            elif stock_code.startswith(('sh', 'sz', 'hk', 'us')):
                full_code = stock_code
            else:
                market = "sh" if stock_code.startswith("6") else "sz"
                full_code = f"{market}{stock_code}"
            
            url = f"{self.tencent_base}/q={full_code}"
            
            # 4. 尝试腾讯API
            try:
                response = await self._log_and_request("tencent_quote", url)
                
                # 解析返回数据
                content = response.text
                data = self._parse_tencent_quote(content, stock_code)
                
                if data:
                    # 成功：重置失败计数
                    self._tencent_fail_count = 0
                    logger.info(f"[OK] 腾讯API获取行情成功: {stock_code}")
                    
                    # [OK] 特殊处理指数代码：确保返回的对象使用原始代码，特别是带后缀的格式
                    if '.' in stock_code:
                        data['code'] = stock_code
                    
                    # 存入缓存
                    await quote_cache.set(data, stock_code)
                    
                    return StockQuote(**data)
            except Exception as e:
                # 失败：增加失败计数
                self._tencent_fail_count += 1
                logger.warning(f"[WARN]️ 腾讯API获取行情失败 ({self._tencent_fail_count}/3): {stock_code}, 错误: {str(e)}")
                
                # 触发熔断
                if self._tencent_fail_count >= 3:
                    logger.error(f"[ERROR] 腾讯API连续失败{self._tencent_fail_count}次，触发熔断")
                    self._tencent_circuit_breaker = True
                    self._circuit_breaker_reset_time = datetime.now() + timedelta(minutes=5)
            
            # 5. 腾讯API失败，尝试Akshare备用方案
            return await self._get_quote_from_akshare(stock_code)
            
        except Exception as e:
            logger.error(f"[ERROR] 获取股票 {stock_code} 行情失败: {str(e)}", exc_info=True)
            return None
    
    async def _get_quote_from_akshare(self, stock_code: str) -> Optional[StockQuote]:
        """从Akshare获取行情数据（备用方案）"""
        akshare_source = self._get_akshare_source()
        if not akshare_source:
            logger.warning(f"[ERROR] Akshare数据源不可用，无法获取行情: {stock_code}")
            return None
        
        logger.info(f"🔄 尝试 Akshare 备用方案: {stock_code}")
        try:
            ak_data = await akshare_source.get_realtime_quote(stock_code)
            if ak_data:
                logger.info(f"[OK] Akshare获取行情成功: {stock_code}")
                
                # [OK] 特殊处理指数代码：确保返回的对象使用原始代码
                if '.' in stock_code:
                    ak_data['code'] = stock_code
                
                # 存入缓存
                await quote_cache.set(ak_data, stock_code)
                return StockQuote(**ak_data)
        except Exception as e:
            logger.error(f"[ERROR] Akshare获取行情也失败: {stock_code}, 错误: {str(e)}")
        
        logger.warning(f"[ERROR] 所有数据源都无法获取行情: {stock_code}")
        return None
    
    async def get_quotes(self, stock_codes: List[str]) -> List[StockQuote]:
        """批量获取股票实时行情"""
        try:
            # 构建股票代码列表
            codes = []
            code_map = {}  # 映射 API 代码到原始代码
            for code in stock_codes:
                if '.' in code:
                    # 指数代码格式: 000001.SH → sh000001
                    parts = code.split('.')
                    market = parts[1].lower()
                    api_code = f"{market}{parts[0]}"
                    codes.append(api_code)
                    code_map[parts[0]] = code  # 000001 -> 000001.SH
                    code_map[api_code] = code  # sh000001 -> 000001.SH
                elif code.startswith(('sh', 'sz', 'hk', 'us')):
                    codes.append(code)
                else:
                    market = "sh" if code.startswith("6") else "sz"
                    api_code = f"{market}{code}"
                    codes.append(api_code)
            
            url = f"{self.tencent_base}/q={','.join(codes)}"
            response = await self._log_and_request("tencent_quotes_batch", url)
            
            content = response.text
            quotes = []
            
            # 解析多只股票数据
            for line in content.split('\n'):
                if line.strip():
                    data = self._parse_tencent_quote(line, None)
                    if data:
                        # [OK] 特殊处理指数代码恢复原始格式
                        if data['code'] in code_map:
                            data['code'] = code_map[data['code']]
                        
                        quotes.append(StockQuote(**data))
            
            return quotes
            
        except Exception as e:
            logger.error(f"批量获取股票行情失败: {str(e)}")
            return []
    
    async def get_kline(self, stock_code: str, period: str = "day", 
                       count: int = 100) -> List[StockKLine]:
        """获取K线数据 (Tushare -> Akshare -> Tencent 级联 fallback)
        
        Args:
            stock_code: 股票代码
            period: K线周期 (m1/m5/m15/m30/m60/day/week/month)
            count: K线数量
            
        优化：
        - 板块代码（BK开头）直接使用Akshare，因为腾讯API不支持
        - 指数代码优先使用Akshare获取更准确数据
        - 股票代码使用级联fallback
        """
        # 特殊处理：板块代码（BK开头）直接使用Akshare
        # 因为腾讯K线API不支持板块代码
        lower_code = stock_code.lower()
        if lower_code.startswith('bk'):
            akshare_source = self._get_akshare_source()
            if akshare_source:
                try:
                    # 检查是否在失败缓存中
                    if hasattr(akshare_source, '_is_in_failure_cache') and \
                       akshare_source._is_in_failure_cache(stock_code, 'get_kline'):
                        logger.debug(f"板块 {stock_code} 在失败缓存中，跳过K线获取")
                        return []
                    
                    ak_data = await akshare_source.get_kline(stock_code, period, count)
                    if ak_data:
                        logger.info(f"板块K线数据从Akshare获取成功: {stock_code}")
                        return [StockKLine(
                            code=stock_code,
                            date=item['date'],
                            open=item['open'],
                            close=item['close'],
                            high=item['high'],
                            low=item['low'],
                            volume=item['volume'],
                            amount=item['amount']
                        ) for item in ak_data]
                    else:
                        # 没有获取到数据，可能是板块代码无效
                        logger.warning(f"板块 {stock_code} 未获取到K线数据，可能板块代码无效或不存在")
                        return []
                except Exception as e:
                    logger.warning(f"Akshare 获取板块K线失败 {stock_code}: {str(e)}")
                    return []
            else:
                logger.warning(f"板块 {stock_code} 无法获取K线：Akshare不可用")
                return []
        
        # 1. 尝试 Tushare (分钟线优先，日线也支持)
        if self.ts_pro:
            try:
                if period.startswith('m'):
                    data = await self._get_kline_tushare_minute(stock_code, period, count)
                    if data: return data
                elif period in ['day', 'week', 'month']:
                    # 这里可以添加 Tushare 日线获取逻辑，但由于 Tushare 日线通常需要积分且限流，
                    # 我们可以根据需要决定是否在这里调用。目前先保留分钟线逻辑。
                    pass
            except Exception as e:
                logger.warning(f"Tushare 获取 K 线失败 {stock_code}: {str(e)}")

        # 2. 尝试 Akshare (作为高质量的 A 股备用源)
        akshare_source = self._get_akshare_source()
        if akshare_source:
            try:
                ak_data = await akshare_source.get_kline(stock_code, period, count)
                if ak_data:
                    return [StockKLine(
                        code=stock_code,
                        date=item['date'],
                        open=item['open'],
                        close=item['close'],
                        high=item['high'],
                        low=item['low'],
                        volume=item['volume'],
                        amount=item['amount']
                    ) for item in ak_data]
            except Exception as e:
                logger.warning(f"Akshare 获取 K 线失败 {stock_code}: {str(e)}")

        # 3. 尝试 Tencent (作为最后的兜底，速度快但数据质量可能稍逊)
        try:
            full_code = self._to_tencent_symbol(stock_code)
            
            # 映射周期参数
            period_map = {
                'day': 'day',    # 日线
                'week': 'week',  # 周线
                'month': 'month' # 月线
            }
            
            api_period = period_map.get(period, period)
            
            # 腾讯K线API - 日线、周线、月线使用前复权
            url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
            
            # 优化：行业板块 (BKxxxx) 不支持复权参数 qfq，需特殊处理
            # 注意：板块代码已经在前面处理，这里不应该再出现
            is_bk = full_code.startswith('bk')
            if is_bk:
                logger.warning(f"板块代码 {stock_code} 不应走到腾讯API路径")
                return []
                
            api_param = f"{full_code},{api_period},,,{count}"
            api_param += ",qfq"
                
            params = {
                "_var": f"kline_{api_period}qfq",
                "param": api_param,
                "r": int(datetime.now().timestamp() * 1000)
            }
            
            logger.debug(f"Requesting K-line for {stock_code}, period={api_period}, url={url}, params={params}")
            response = await self._log_and_request("tencent_kline", url, params=params)
            
            # 解析返回数据
            content = response.text
            data = self._parse_tencent_kline(content, stock_code, api_period)
            
            if data:
                logger.info(f"Retrieved {len(data)} K-line items for {stock_code} (period={api_period}) from Tencent")
                return data
                
        except Exception as e:
            logger.error(f"Tencent 获取股票 {stock_code} K线数据失败: {str(e)}")
            
        return []
    
    async def get_intraday(self, stock_code: str) -> Optional[Dict]:
        """获取分时数据
        
        Returns:
            包含分时数据的字典，格式为：
            {
                'code': str,
                'data': List[Dict],  # 分时数据数组
                'avg_price': float,
                'pre_close': float,
                'timestamp': str
            }
            如果无法获取数据则返回 None
        """
        try:
            # 优先使用 Akshare 获取分时数据
            akshare_source = self._get_akshare_source()
            if akshare_source:
                data = await akshare_source.get_intraday_data(stock_code)
                if data:
                    return data
            
            logger.warning(f"无法获取股票 {stock_code} 的分时数据")
            return None
            
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 分时数据失败: {str(e)}", exc_info=True)
            return None
    
    async def _get_kline_tushare_minute(self, stock_code: str, period: str, count: int) -> List[StockKLine]:
        """使用Tushare获取分钟线数据，如果不可用则使用模拟数据"""
        try:
            # 检查Tushare是否可用
            if not self.ts_pro:
                logger.warning(f"股票 {stock_code} 无法获取分钟线数据：Tushare 未配置")
                return []
            
            import pandas as pd
            from datetime import datetime, timedelta
            
            # Tushare分钟线周期映射
            freq_map = {
                'm1': '1min',
                'm5': '5min',
                'm15': '15min',
                'm30': '30min',
                'm60': '60min'
            }
            
            freq = freq_map.get(period, '5min')
            
            # 计算需要的日期范围（分钟线数据量较大，需要控制）
            end_date = datetime.now()
            # 根据周期计算需要的起始日期
            if period == 'm1':
                start_date = end_date - timedelta(days=3)  # 1分钟线只取最近3天
            elif period in ['m5', 'm15']:
                start_date = end_date - timedelta(days=7)  # 5/15分钟线取最近7天
            else:
                start_date = end_date - timedelta(days=14)  # 30/60分钟线取最近14天
            
            # 调用Tushare API
            if stock_code.endswith(('.SH', '.SZ')):
                ts_code = stock_code
            elif stock_code.startswith('6'):
                ts_code = f"{stock_code}.SH"
            else:
                ts_code = f"{stock_code}.SZ"
            
            df = await self._call_tushare(
                'query',
                api_name='stk_mins',
                ts_code=ts_code,
                start_date=start_date.strftime('%Y-%m-%d %H:%M:%S'),
                end_date=end_date.strftime('%Y-%m-%d %H:%M:%S'),
                freq=freq
            )
            
            if df is None or df.empty:
                logger.warning(f"股票 {stock_code} 未找到分钟线数据")
                return []
            
            # 按时间倒序，取最近的count条
            df = df.sort_values('trade_time', ascending=False).head(count)
            
            # 转换为StockKLine格式
            klines = []
            for _, row in df.iterrows():
                klines.append(StockKLine(
                    code=stock_code,
                    date=row['trade_time'],
                    open=float(row['open']),
                    close=float(row['close']),
                    high=float(row['high']),
                    low=float(row['low']),
                    volume=int(row['vol']),
                    amount=float(row['amount'])
                ))
            
            # 按时间正序返回
            klines.reverse()
            logger.info(f"Retrieved {len(klines)} minute K-line items for {stock_code} (period={period})")
            return klines
            
        except Exception as e:
            logger.error(f"获取分钟线失败: {str(e)}")
            return []
    
    async def get_technical_indicators(self, stock_code: str, db_session=None) -> Optional[TechnicalIndicators]:
        """获取技术指标（带缓存优化）
        
        Args:
            stock_code: 股票代码
            db_session: 数据库会话（可选，用于从数据库读取K线）
        """
        try:
            # [START] 性能优化：优先从缓存获取
            from services.extended_cache import technical_cache
            
            cached_indicators = await technical_cache.get(stock_code)
            if cached_indicators:
                logger.info(f"⚡ 从缓存获取技术指标: {stock_code}")
                return TechnicalIndicators(**cached_indicators)
            
            # 缓存未命中，计算技术指标
            logger.info(f"[CHART] 计算技术指标: {stock_code}")
            
            # [START] 优化：优先从数据库获取K线数据
            klines = None
            if db_session:
                try:
                    from services.stock_data_service import stock_data_service
                    klines = await stock_data_service.get_kline_from_db(db_session, stock_code, "day", 100)
                    if klines and len(klines) > 0:
                        logger.info(f"[OK] 从数据库获取K线数据用于技术指标计算: {stock_code}, {len(klines)}条")
                except Exception as e:
                    logger.warning(f"从数据库获取K线失败: {str(e)}，尝试从API获取")
            
            # 如果数据库无数据，从API获取
            if not klines or len(klines) == 0:
                logger.info(f"[CHART] 从API获取K线数据用于技术指标计算: {stock_code}")
                klines = await self.get_kline(stock_code, "day", 100)
            
            if not klines or len(klines) < 20:
                logger.warning(f"股票 {stock_code} K线数据不足，无法计算技术指标（需要至少20条，实际{len(klines) if klines else 0}条）")
                return None
            
            # [START] 性能优化：将同步计算任务移至线程，避免阻塞事件循环
            import asyncio
            
            def _sync_calculate_indicators(klines_data):
                # 计算MA均线
                ma5 = self._calculate_ma(klines_data, 5)
                ma10 = self._calculate_ma(klines_data, 10)
                ma20 = self._calculate_ma(klines_data, 20)
                
                # 计算MACD
                macd, macd_signal, macd_hist = self._calculate_macd(klines_data)
                
                # 计算RSI
                rsi = self._calculate_rsi(klines_data, 14)
                
                # 计算KDJ
                kdj_k, kdj_d, kdj_j = self._calculate_kdj(klines_data)
                
                return ma5, ma10, ma20, macd, macd_signal, macd_hist, rsi, kdj_k, kdj_d, kdj_j

            # 在线程池中执行同步计算
            ma5, ma10, ma20, macd, macd_signal, macd_hist, rsi, kdj_k, kdj_d, kdj_j = \
                await asyncio.to_thread(_sync_calculate_indicators, klines)
            
            latest = klines[-1]
            
            result = TechnicalIndicators(
                code=stock_code,
                date=latest.date,
                ma5=ma5,
                ma10=ma10,
                ma20=ma20,
                macd=macd,
                macd_signal=macd_signal,
                macd_hist=macd_hist,
                rsi=rsi,
                kdj_k=kdj_k,
                kdj_d=kdj_d,
                kdj_j=kdj_j
            )
            
            # [START] 存入缓存
            await technical_cache.set(result.dict(), stock_code)
            logger.info(f"[OK] 技术指标已缓存: {stock_code}")
            
            return result
            
        except Exception as e:
            logger.error(f"计算股票 {stock_code} 技术指标失败: {str(e)}")
            return None
    
    def _parse_tencent_quote(self, content: str, stock_code: Optional[str]) -> Optional[Dict]:
        """解析腾讯股票API返回数据"""
        try:
            # 腾讯API返回格式：v_sh600219="1~南山铝业~600219~..."
            if not content or '=' not in content:
                return None
            
            # 提取数据部分
            match = re.search(r'="(.+)"', content)
            if not match:
                return None
            
            data_str = match.group(1)
            parts = data_str.split('~')
            
            if len(parts) < 35:
                return None
            
            return {
                'code': parts[2],
                'name': parts[1],
                'price': float(parts[3]),
                'change': float(parts[31]),
                'change_pct': float(parts[32]),
                'open': float(parts[5]),
                'high': float(parts[33]),
                'low': float(parts[34]),
                'volume': int(parts[6]),
                'amount': float(parts[37]),
                'turnover_rate': float(parts[38]) if len(parts) > 38 else None,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"解析腾讯行情数据失败: {str(e)}")
            return None
    
    def _parse_tencent_kline(self, content: str, stock_code: str, api_period: str = "day") -> List[StockKLine]:
        """解析腾讯K线数据"""
        try:
            # 移除JSONP回调函数名
            if '=' in content:
                content = content.split('=', 1)[1]
            
            data = json.loads(content)
            
            klines = []
            if data.get('data'):
                full_code = self._to_tencent_symbol(stock_code)
                pure_code = full_code[2:] if len(full_code) > 2 else stock_code
                
                stock_data = data['data'].get(full_code) or data['data'].get(stock_code) or data['data'].get(pure_code)
                
                if stock_data:
                    # 查找包含K线数据的键 (day, week, month, or qfqday, etc.)
                    # 腾讯API在某些情况下返回 qfqday 而不是 day
                    kline_key = None
                    keys_to_check = [
                        api_period, f"qfq{api_period}", 
                        'day', 'week', 'month', 'qfqday', 'qfqweek', 'qfqmonth'
                    ]
                    for key in keys_to_check:
                        if stock_data.get(key):
                            kline_key = key
                            break
                    
                    if kline_key:
                        kline_data = stock_data[kline_key]
                        logger.debug(f"Found {len(kline_data)} K-line items with key '{kline_key}' for {stock_code}")
                        
                        if kline_data and len(kline_data) > 0:
                            # 记录第一个数据项的完整格式，帮助调试
                            logger.debug(f"First K-line item type: {type(kline_data[0])}")
                            logger.debug(f"First K-line item sample: {kline_data[0]}")
                            if isinstance(kline_data[0], dict):
                                # 记录字典的每个字段类型
                                logger.debug(f"K-line dict keys: {list(kline_data[0].keys())}")
                                for key, value in kline_data[0].items():
                                    logger.debug(f"  {key}: type={type(value)}, value={value}")
                        
                        for idx, item in enumerate(kline_data):
                            try:
                                # 检查item格式，腾讯API可能返回不同的数据结构
                                if isinstance(item, dict):
                                    # 新格式：字典形式
                                    # 辅助函数：安全提取数值
                                    def safe_float(value, field_name=""):
                                        if value is None:
                                            return 0.0
                                        if isinstance(value, (int, float)):
                                            return float(value)
                                        if isinstance(value, str):
                                            try:
                                                return float(value)
                                            except ValueError:
                                                logger.warning(f"Cannot convert string to float for {field_name}: {value}")
                                                return 0.0
                                        if isinstance(value, dict):
                                            # 尝试从字典中提取常见的数值字段
                                            for key in ['value', 'v', 'val', 'num']:
                                                if key in value:
                                                    return safe_float(value[key], f"{field_name}.{key}")
                                            logger.warning(f"Dict value for {field_name} has no numeric field: {value}")
                                            return 0.0
                                        logger.warning(f"Unknown type for {field_name}: {type(value)}, value: {value}")
                                        return 0.0
                                    
                                    def safe_int(value, field_name=""):
                                        return int(safe_float(value, field_name))
                                    
                                    klines.append(StockKLine(
                                        code=stock_code,
                                        date=item.get('date', item.get('d', '')),
                                        open=safe_float(item.get('open', item.get('o', 0)), 'open'),
                                        close=safe_float(item.get('close', item.get('c', 0)), 'close'),
                                        high=safe_float(item.get('high', item.get('h', 0)), 'high'),
                                        low=safe_float(item.get('low', item.get('l', 0)), 'low'),
                                        volume=safe_int(item.get('volume', item.get('v', 0)), 'volume'),
                                        amount=safe_float(item.get('amount', item.get('a', 0)), 'amount')
                                    ))
                                elif isinstance(item, (list, tuple)) and len(item) >= 6:
                                    # 旧格式：数组形式
                                    klines.append(StockKLine(
                                        code=stock_code,
                                        date=item[0],
                                        open=float(item[1]) if not isinstance(item[1], dict) else 0.0,
                                        close=float(item[2]) if not isinstance(item[2], dict) else 0.0,
                                        high=float(item[3]) if not isinstance(item[3], dict) else 0.0,
                                        low=float(item[4]) if not isinstance(item[4], dict) else 0.0,
                                        volume=int(float(item[5]) if not isinstance(item[5], dict) else 0),
                                        amount=float(item[6]) if len(item) > 6 and not isinstance(item[6], dict) else 0.0
                                    ))
                                else:
                                    logger.warning(f"Unknown K-line item format at index {idx}: {item}")
                            except Exception as e:
                                logger.error(f"Failed to parse K-line item {idx}: {item}, error: {str(e)}")
                                continue
                else:
                    logger.warning(f"Tencent K-line data not found for {full_code} in response")
            else:
                logger.warning(f"Tencent K-line response has no 'data' field: {content[:100]}")
            
            return klines
            
        except Exception as e:
            logger.error(f"解析K线数据失败: {str(e)}")
            return []
    
    def _calculate_ma(self, klines: List[StockKLine], period: int) -> Optional[float]:
        """计算移动平均线"""
        try:
            if len(klines) < period:
                return None
            
            closes = [k.close for k in klines[-period:]]
            return sum(closes) / period
        except:
            return None
    
    def _calculate_macd(self, klines: List[StockKLine]) -> tuple:
        """计算MACD指标"""
        try:
            import numpy as np
            
            closes = np.array([k.close for k in klines])
            
            # EMA12
            ema12 = self._calculate_ema(closes, 12)
            # EMA26
            ema26 = self._calculate_ema(closes, 26)
            # DIF
            dif = ema12 - ema26
            # DEA
            dea = self._calculate_ema(dif, 9)
            # MACD柱
            macd_hist = (dif - dea) * 2
            
            return float(dif[-1]), float(dea[-1]), float(macd_hist[-1])
            
        except Exception as e:
            logger.error(f"计算MACD失败: {str(e)}")
            return None, None, None
    
    def _calculate_ema(self, data, period: int):
        """计算EMA"""
        import numpy as np
        
        ema = np.zeros_like(data)
        ema[0] = data[0]
        alpha = 2 / (period + 1)
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
        
        return ema
    
    def _calculate_rsi(self, klines: List[StockKLine], period: int = 14) -> Optional[float]:
        """计算RSI指标"""
        try:
            import numpy as np
            
            closes = np.array([k.close for k in klines])
            deltas = np.diff(closes)
            
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi)
            
        except Exception as e:
            logger.error(f"计算RSI失败: {str(e)}")
            return None
    
    def _calculate_kdj(self, klines: List[StockKLine]) -> tuple:
        """计算KDJ指标"""
        try:
            import numpy as np
            
            period = 9
            highs = np.array([k.high for k in klines])
            lows = np.array([k.low for k in klines])
            closes = np.array([k.close for k in klines])
            
            # 计算RSV
            lowest_low = np.min(lows[-period:])
            highest_high = np.max(highs[-period:])
            
            if highest_high == lowest_low:
                rsv = 50
            else:
                rsv = (closes[-1] - lowest_low) / (highest_high - lowest_low) * 100
            
            # K值
            k = rsv
            # D值
            d = k
            # J值
            j = 3 * k - 2 * d
            
            return float(k), float(d), float(j)
            
        except Exception as e:
            logger.error(f"计算KDJ失败: {str(e)}")
            return None, None, None
    
    def _calculate_pmr(self, klines: List[StockKLine], periods: List[int] = [5, 10, 20, 30, 60]) -> Dict:
        """
        计算PMR(动量比值)
        
        PMR(N) = (股价N日涨幅率) / (MA_N的N日涨幅率)
        
        Args:
            klines: K线数据列表
            periods: 需要计算的周期列表，默认[5, 10, 20, 30, 60]
            
        Returns:
            Dict: {
                'pmr5': [...], 'pmr10': [...], 'pmr20': [...], 'pmr30': [...], 'pmr60': [...],
                'dates': [...]
            }
        """
        try:
            import numpy as np
            
            if not klines:
                return None
            
            closes = np.array([k.close for k in klines])
            dates = [k.date for k in klines]
            
            result = {'dates': dates}
            
            for period in periods:
                if len(closes) < period + 1:
                    # 如果数据不足以计算该周期的PMR，则填充None
                    result[f'pmr{period}'] = [None] * len(closes)
                    continue
                
                # 计算MA_N
                ma = np.convolve(closes, np.ones(period)/period, mode='valid')
                # 补齐前面的值
                ma_full = np.concatenate([[np.nan] * (period - 1), ma])
                
                # 计算PMR
                pmr_values = []
                for i in range(len(closes)):
                    if i < period:
                        # 前面不足N天的数据，无法计算
                        pmr_values.append(None)
                    else:
                        # 股价N日涨幅率
                        if closes[i - period] != 0:
                            price_return = (closes[i] - closes[i - period]) / closes[i - period]
                        else:
                            price_return = 0
                        
                        # MA_N的N日涨幅率
                        if ma_full[i - period] != 0 and not np.isnan(ma_full[i - period]):
                            ma_return = (ma_full[i] - ma_full[i - period]) / ma_full[i - period]
                        else:
                            ma_return = 0
                        
                        # 计算PMR
                        if ma_return != 0:
                            pmr = price_return / ma_return
                        else:
                            # 避免除以0，如果MA涨幅率为0，则PMR设为None
                            pmr = None
                        
                        pmr_values.append(pmr)
                
                result[f'pmr{period}'] = pmr_values
            
            return result
            
        except Exception as e:
            logger.error(f"计算PMR失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def get_pmr(self, stock_code: str, days: int = 120) -> Optional[Dict]:
        """
        获取股票的PMR数据（带缓存优化）
        
        Args:
            stock_code: 股票代码
            days: 获取的天数，默认120天
            
        Returns:
            Dict: PMR数据
        """
        try:
            # [START] 性能优化：优先从缓存获取
            from services.extended_cache import pmr_cache
            
            cached_pmr = await pmr_cache.get(stock_code, days)
            if cached_pmr:
                logger.info(f"⚡ 从缓存获取PMR数据: {stock_code}")
                return cached_pmr
            
            # 缓存未命中，获取K线数据
            logger.info(f"[CHART] 计算PMR数据: {stock_code}")
            
            # 1. 获取K线数据 (需要比计算天数更多的历史数据来计算MA)
            # MA60需要额外的60天数据，且MA计算本身需要N-1天延迟，所以取 days + 120
            klines = await self.get_kline(stock_code, 'day', days + 120)
            
            if not klines:
                logger.warning(f"K线数据为空，无法计算PMR: {stock_code}")
                return None
            
            # 2. 计算PMR (移至线程执行，避免阻塞)
            import asyncio
            pmr_data = await asyncio.to_thread(self._calculate_pmr, klines)
            
            if not pmr_data:
                return None
            
            # 3. 提取最后 days 条数据返回
            # 找到日期在 days 范围内的索引
            if len(pmr_data['dates']) > days:
                start_idx = len(pmr_data['dates']) - days
                result = {
                    'dates': pmr_data['dates'][start_idx:]
                }
                for key in pmr_data:
                    if key != 'dates':
                        result[key] = pmr_data[key][start_idx:]
                pmr_data = result
            
            # 4. 存入缓存
            await pmr_cache.set(pmr_data, stock_code, days)
            
            return pmr_data
            
        except Exception as e:
            logger.error(f"获取PMR数据失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def close(self):
        """关闭HTTP客户端（client 由 datasource 层管理，此处无需关闭）"""
        pass


# 单例实例
stock_service = StockService()

