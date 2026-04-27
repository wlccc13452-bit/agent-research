"""美股市场分析服务"""
import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
import json
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from datasource import get_datasource, DataSourceType
from services.ai_service import AIService
from database.operations import get_us_daily_data, save_us_daily_data

logger = logging.getLogger(__name__)


class USMarketDataService:
    """美股数据采集服务 - 支持多数据源"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(USMarketDataService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        logger.info("美股数据源初始化: 统一通过 datasource 模块")
    
    async def get_us_stock_data(self, symbol: str, period: str = "1mo", db: Optional[AsyncSession] = None,
                                  force_real: bool = False) -> Optional[Dict]:
        """获取美股数据 - 立即返回数据库数据，后台异步更新
        
        Args:
            symbol: 美股代码
            period: 时间周期
            db: 数据库会话
            force_real: 是否强制从真实数据源获取（用于后台更新）
        
        Returns:
            美股数据字典，如果数据库没数据则返回 None
        """
        
        # 0. 如果是后台更新任务，强制从真实数据源获取
        if force_real:
            return await self._get_from_real_sources(symbol, period)
        
        # 1. 如果提供了数据库会话，从数据库获取数据
        if db:
            try:
                db_data = await self.get_us_data_from_db(db, symbol, limit=1)
                if db_data:
                    latest = db_data[0]
                    # 转换格式以匹配 API 返回
                    return {
                        'symbol': symbol,
                        'name': symbol,
                        'previous_close': latest.get('close'),
                        'open': latest.get('open'),
                        'high': latest.get('high'),
                        'low': latest.get('low'),
                        'volume': latest.get('volume'),
                        'change_pct': latest.get('change_pct'),
                        'ma_5': latest.get('ma5'),
                        'ma_20': latest.get('ma20'),
                        'rsi': latest.get('rsi'),
                        'macd': latest.get('macd'),
                        'timestamp': datetime.combine(latest.get('trade_date'), datetime.min.time()),
                        'data_source': 'db'
                    }
            except Exception as e:
                logger.warning(f"从数据库获取美股数据失败 {symbol}: {str(e)}")
        
        # 2. 数据库没有数据，返回 None（不使用预设数据）
        logger.info(f"数据库无美股数据 {symbol}，返回 None，触发后台更新")
        return None
    
    def _convert_kline_to_us_data(self, kline: List[Dict], symbol: str, period: str) -> Dict:
        """将datasource的kline格式转换为USMarketDataService的返回格式"""
        if not kline:
            return {}
        latest = kline[-1]
        prev = kline[-2] if len(kline) >= 2 else latest
        change = round(latest['close'] - prev['close'], 2)
        change_pct = round(change / prev['close'] * 100, 2) if prev['close'] else 0
        
        return {
            'symbol': symbol,
            'name': '',
            'current': latest['close'],
            'change': change,
            'change_pct': change_pct,
            'open': latest['open'],
            'high': latest['high'],
            'low': latest['low'],
            'prev_close': prev['close'],
            'volume': latest.get('volume', 0),
            'history': kline,
            'period': period,
            'timestamp': datetime.now(),
            'data_source': 'datasource',
        }
    
    def _convert_quote_to_us_data(self, quote: Dict, symbol: str, period: str) -> Dict:
        """将datasource的quote格式转换为USMarketDataService的返回格式"""
        return {
            'symbol': symbol,
            'name': quote.get('name', ''),
            'current': quote.get('current'),
            'change': quote.get('change'),
            'change_pct': quote.get('change_pct'),
            'open': quote.get('open'),
            'high': quote.get('high'),
            'low': quote.get('low'),
            'prev_close': quote.get('prev_close'),
            'volume': quote.get('volume', 0),
            'history': [],
            'period': period,
            'timestamp': datetime.now(),
            'data_source': quote.get('source', 'datasource'),
        }
    
    async def _get_from_real_sources(self, symbol: str, period: str = "1mo") -> Optional[Dict]:
        """从真实数据源获取数据 - 完全委托给 USMarketDataSource"""
        is_index_symbol = symbol.startswith('^')

        us_ds = get_datasource().get_source(DataSourceType.YFINANCE)
        if not us_ds or not await us_ds.is_available():
            logger.warning(f"USMarketDataSource 不可用: {symbol}")
            return None

        try:
            if is_index_symbol:
                kline = await us_ds.get_index_kline(symbol, period=period, count=30)
                if kline:
                    return self._convert_kline_to_us_data(kline, symbol, period)
            else:
                quote = await us_ds.get_us_quote(symbol)
                if quote:
                    return self._convert_quote_to_us_data(quote, symbol, period)
        except Exception as e:
            logger.warning(f"USMarketDataSource 获取 {symbol} 失败: {str(e)}")

        return None

    async def get_us_market_indices(self, db: Optional[AsyncSession] = None) -> Dict:
        """获取全球主要指数数据（美股 + 日韩）- 并行获取"""
        indices = {
            '^GSPC': '标普500',
            '^IXIC': '纳斯达克',
            '^DJI': '道琼斯',
            '^VIX': 'VIX恐慌指数',
            '^N225': '日经225',
            '^KS11': '韩国综合',
        }
        
        # 并行获取所有指数数据
        tasks = [self.get_us_stock_data(symbol, db=db) for symbol in indices.keys()]
        data_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = {}
        for (symbol, name), data in zip(indices.items(), data_list):
            # 跳过失败的数据
            if isinstance(data, Exception):
                logger.warning(f"获取 {name} 数据失败: {data}")
                continue
            if data:
                data['name'] = name
                # 兼容旧版本使用 symbol 作为 key，同时也支持前端直接用中文名作为 key
                results[symbol] = data
                results[name] = data
                
        return results

    async def save_us_data_to_db(self, db, data: Dict) -> bool:
        """保存美股数据到数据库"""
        try:
            await save_us_daily_data(db, data)
            return True
        except Exception as e:
            logger.error(f"保存美股数据失败 {data.get('symbol')}: {str(e)}")
            return False

    async def get_us_data_from_db(self, db, symbol: str, limit: int = 1) -> List[Dict]:
        """从数据库获取美股数据"""
        return await get_us_daily_data(db, symbol, limit)
    
    def _calculate_rsi(self, prices: np.array, period: int = 14) -> Optional[float]:
        """计算RSI"""
        try:
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi)
        except:
            return None
    
    def _calculate_macd(self, prices: np.array, slow: int = 26, 
                       fast: int = 12, signal: int = 9) -> Optional[Dict]:
        """计算MACD"""
        try:
            ema_fast = self._calculate_ema(prices, fast)
            ema_slow = self._calculate_ema(prices, slow)
            macd = ema_fast - ema_slow
            signal_line = self._calculate_ema(macd, signal)
            histogram = macd - signal_line
            
            return {
                'macd': float(macd[-1]),
                'signal': float(signal_line[-1]),
                'histogram': float(histogram[-1])
            }
        except:
            return None
    
    def _calculate_ema(self, data: np.array, period: int) -> np.array:
        """计算EMA"""
        ema = np.zeros_like(data)
        ema[0] = data[0]
        alpha = 2 / (period + 1)
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
        
        return ema
    
    async def close(self):
        """关闭资源（datasource 自行管理连接）"""
        pass


class USMarketCorrelationEngine:
    """美股相关标的识别引擎"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(USMarketCorrelationEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.ai_service = AIService()
        self._initialized = True

    def _normalize_text(self, text: str) -> str:
        return (text or "").lower().replace(" ", "").replace("-", "").replace("_", "")

    def _ensure_result_shape(self, data: Optional[Dict]) -> Dict:
        normalized = data or {}
        return {
            "industry_leaders": normalized.get("industry_leaders") or [],
            "supply_chain": normalized.get("supply_chain") or [],
            "etfs": normalized.get("etfs") or [],
            "commodities": normalized.get("commodities") or [],
            "energy": normalized.get("energy") or [],
            "metals": normalized.get("metals") or [],
            "chemicals": normalized.get("chemicals") or [],
        }

    def _match_sector_profile(self, stock_name: str, sector: str, correlation_map: Dict) -> Dict:
        normalized_context = self._normalize_text(f"{stock_name}{sector}")
        for key, value in correlation_map.items():
            normalized_key = self._normalize_text(key)
            if normalized_key and normalized_key in normalized_context:
                return value
        return self._get_default_correlation()

    def _merge_correlation_result(self, base: Dict, override: Dict) -> Dict:
        merged = self._ensure_result_shape(base)
        source = self._ensure_result_shape(override)
        for key in merged.keys():
            if source.get(key):
                merged[key] = source[key]
        return merged
    
    async def identify_related_us_stocks(self, stock_name: str, sector: str) -> Dict:
        """
        AI识别A股持仓股票的美股相关标的
        
        Args:
            stock_name: A股股票名称
            sector: 所属板块
            
        Returns:
            相关美股标的列表
        """
        try:
            correlation_map = {
                "铝": {
                    "industry_leaders": [
                        {"symbol": "AA", "name": "美国铝业", "correlation": "同行业龙头", "relevance_score": 0.9}
                    ],
                    "etfs": [
                        {"symbol": "XME", "name": "SPDR金属材料ETF", "correlation": "行业ETF", "relevance_score": 0.8}
                    ],
                    "commodities": [
                        {"symbol": "ALI", "name": "LME铝期货", "correlation": "大宗商品", "relevance_score": 0.95}
                    ],
                    "metals": [
                        {"symbol": "ALI", "name": "LME铝期货", "correlation": "国际铝价", "relevance_score": 0.95},
                        {"symbol": "AA", "name": "美国铝业", "correlation": "金属景气代理", "relevance_score": 0.82}
                    ],
                    "energy": [
                        {"symbol": "BZ=F", "name": "布伦特原油", "correlation": "电解铝能源成本", "relevance_score": 0.65}
                    ]
                },
                "光伏": {
                    "industry_leaders": [
                        {"symbol": "ENPH", "name": "Enphase Energy", "correlation": "同行业龙头", "relevance_score": 0.85},
                        {"symbol": "SEDG", "name": "SolarEdge", "correlation": "同行业龙头", "relevance_score": 0.85}
                    ],
                    "etfs": [
                        {"symbol": "TAN", "name": "太阳能ETF", "correlation": "行业ETF", "relevance_score": 0.9}
                    ],
                    "commodities": [
                        {"symbol": "SI", "name": "硅料期货", "correlation": "大宗商品", "relevance_score": 0.75}
                    ],
                    "energy": [
                        {"symbol": "BZ=F", "name": "布伦特原油", "correlation": "新能源替代成本锚", "relevance_score": 0.58}
                    ],
                    "chemicals": [
                        {"symbol": "SI=F", "name": "工业硅", "correlation": "光伏上游原料", "relevance_score": 0.82}
                    ]
                },
                "AI": {
                    "industry_leaders": [
                        {"symbol": "NVDA", "name": "英伟达", "correlation": "产业链上游", "relevance_score": 0.95},
                        {"symbol": "AMD", "name": "AMD", "correlation": "同行业", "relevance_score": 0.85}
                    ],
                    "etfs": [
                        {"symbol": "BOTZ", "name": "机器人与AI ETF", "correlation": "行业ETF", "relevance_score": 0.8}
                    ],
                    "energy": [
                        {"symbol": "NG=F", "name": "NYMEX天然气", "correlation": "算力能耗成本", "relevance_score": 0.68}
                    ],
                    "metals": [
                        {"symbol": "HG=F", "name": "COMEX铜期货", "correlation": "电子制造材料", "relevance_score": 0.72}
                    ]
                },
                "有色": {
                    "industry_leaders": [
                        {"symbol": "BHP", "name": "必和必拓", "correlation": "上游供应商", "relevance_score": 0.7}
                    ],
                    "etfs": [
                        {"symbol": "XLB", "name": "原材料ETF", "correlation": "行业ETF", "relevance_score": 0.75}
                    ],
                    "commodities": [
                        {"symbol": "HG", "name": "COMEX铜期货", "correlation": "大宗商品", "relevance_score": 0.85}
                    ],
                    "metals": [
                        {"symbol": "HG=F", "name": "COMEX铜期货", "correlation": "工业金属", "relevance_score": 0.9},
                        {"symbol": "GC=F", "name": "COMEX黄金期货", "correlation": "贵金属风险偏好", "relevance_score": 0.72}
                    ],
                    "energy": [
                        {"symbol": "BZ=F", "name": "布伦特原油", "correlation": "采选冶炼成本", "relevance_score": 0.66}
                    ]
                },
                "煤炭": {
                    "industry_leaders": [
                        {"symbol": "BTU", "name": "Peabody Energy", "correlation": "国际煤炭龙头", "relevance_score": 0.84}
                    ],
                    "energy": [
                        {"symbol": "BZ=F", "name": "布伦特原油", "correlation": "全球能源联动", "relevance_score": 0.95},
                        {"symbol": "NG=F", "name": "NYMEX天然气", "correlation": "替代燃料联动", "relevance_score": 0.88}
                    ],
                    "commodities": [
                        {"symbol": "BZ=F", "name": "布伦特原油", "correlation": "国际能源锚点", "relevance_score": 0.95}
                    ]
                },
                "化工": {
                    "industry_leaders": [
                        {"symbol": "DD", "name": "杜邦", "correlation": "化工材料龙头", "relevance_score": 0.78}
                    ],
                    "chemicals": [
                        {"symbol": "UAN", "name": "氮肥价格代理", "correlation": "化工原料景气", "relevance_score": 0.82},
                        {"symbol": "BNO", "name": "布伦特原油ETF", "correlation": "石化成本锚", "relevance_score": 0.9}
                    ],
                    "energy": [
                        {"symbol": "BZ=F", "name": "布伦特原油", "correlation": "石化成本传导", "relevance_score": 0.93}
                    ]
                }
            }

            result = self._match_sector_profile(stock_name, sector, correlation_map)

            # AI 功能通过 AIService 处理，settings 由 AIService 内部管理
            try:
                ai_result = await self._ai_identify_correlations(stock_name, sector)
                if ai_result:
                    result = self._merge_correlation_result(result, ai_result)
            except Exception as e:
                logger.warning(f"AI识别相关标的失败: {str(e)},使用预定义映射")

            return self._ensure_result_shape(result)
            
        except Exception as e:
            logger.error(f"识别相关美股标的失败: {str(e)}")
            return self._get_default_correlation()
    
    async def _ai_identify_correlations(self, stock_name: str, sector: str) -> Optional[Dict]:
        """AI识别相关美股标的"""
        try:
            prompt = f"""
请分析A股股票"{stock_name}"(所属板块:{sector})的美股相关标的。

请返回以下类型的标的:
1. 同行业美股龙头(股票代码 + 公司名称 + 相关性说明)
2. 产业链上下游美股公司(股票代码 + 公司名称 + 关系说明)
3. 相关ETF基金(基金代码 + 基金名称 + 投资方向)
4. 相关大宗商品期货(期货代码 + 名称 + 影响关系)
5. 国际能源指数/品种(如布伦特原油等)
6. 国际金属指数/期货
7. 国际化工原料指数/期货

请以JSON格式返回,格式如下:
{{
    "industry_leaders": [
        {{"symbol": "AA", "name": "美国铝业", "correlation": "同行业龙头", "relevance_score": 0.9}}
    ],
    "supply_chain": [
        {{"symbol": "BHP", "name": "必和必拓", "correlation": "上游供应商", "relevance_score": 0.7}}
    ],
    "etfs": [
        {{"symbol": "XME", "name": "SPDR金属材料ETF", "correlation": "行业ETF", "relevance_score": 0.8}}
    ],
    "commodities": [
        {{"symbol": "ALI", "name": "LME铝期货", "correlation": "大宗商品", "relevance_score": 0.95}}
    ],
    "energy": [
        {{"symbol": "BZ=F", "name": "布伦特原油", "correlation": "国际能源锚点", "relevance_score": 0.88}}
    ],
    "metals": [
        {{"symbol": "HG=F", "name": "COMEX铜期货", "correlation": "国际金属联动", "relevance_score": 0.83}}
    ],
    "chemicals": [
        {{"symbol": "UAN", "name": "化工原料代理", "correlation": "化工链成本", "relevance_score": 0.75}}
    ]
}}
"""
            
            response = await self.ai_service.analyze(prompt)
            
            if response:
                # 解析JSON响应
                import re
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return self._ensure_result_shape(parsed)
            
            return None
            
        except Exception as e:
            logger.error(f"AI识别失败: {str(e)}")
            return None
    
    def _get_default_correlation(self) -> Dict:
        """返回默认相关标的"""
        return self._ensure_result_shape({
            "industry_leaders": [],
            "etfs": [
                {"symbol": "SPY", "name": "标普500 ETF", "correlation": "大盘ETF", "relevance_score": 0.5}
            ],
            "commodities": [],
            "energy": [
                {"symbol": "BZ=F", "name": "布伦特原油", "correlation": "全球风险偏好锚点", "relevance_score": 0.58}
            ],
            "metals": [],
            "chemicals": []
        })


class USMarketAnalyzer:
    """美股市场AI分析服务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(USMarketAnalyzer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.data_service = USMarketDataService()
        self.correlation_engine = USMarketCorrelationEngine()
        self.ai_service = AIService()
        self._initialized = True
    
    async def analyze_us_market_sentiment(self, market_data: Dict) -> Dict:
        """AI分析美股市场情绪"""
        try:
            sp500 = market_data.get('标普500', {})
            nasdaq = market_data.get('纳斯达克', {})
            
            prompt = f"""
请分析昨日美股市场表现和市场情绪:

标普500:
- 收盘价: {sp500.get('previous_close')}
- 涨跌幅: {sp500.get('change_pct', 0):.2f}%

纳斯达克:
- 收盘价: {nasdaq.get('previous_close')}
- 涨跌幅: {nasdaq.get('change_pct', 0):.2f}%

请从以下维度分析:
1. 整体市场情绪(乐观/悲观/中性)
2. 关键驱动因素(科技股/利率/经济数据等)
3. 技术形态解读(支撑位/阻力位/趋势)
4. 对A股市场的影响预测
5. 明日A股开盘预期

请以JSON格式返回:
{{
    "market_sentiment": "乐观/悲观/中性",
    "key_drivers": "关键驱动因素说明",
    "technical_analysis": "技术形态解读",
    "cn_market_impact": "对A股的影响预测",
    "cn_opening_prediction": "明日A股开盘预期"
}}
"""
            
            response = await self.ai_service.analyze(prompt)
            
            if response:
                import re
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    return json.loads(json_match.group())
            
            # 返回默认分析
            return self._get_default_sentiment_analysis(sp500.get('change_pct', 0))
            
        except Exception as e:
            logger.error(f"分析美股市场情绪失败: {str(e)}")
            return self._get_default_sentiment_analysis(0)
    
    async def analyze_related_stock(self, stock_symbol: str, us_stock_data: Dict,
                                   cn_stock_name: str) -> Dict:
        """AI分析单个相关美股标的"""
        try:
            prompt = f"""
请分析美股 {us_stock_data['name']} ({stock_symbol}) 对A股 {cn_stock_name} 的影响:

美股昨日表现:
- 收盘价: ${us_stock_data['previous_close']}
- 涨跌幅: {us_stock_data['change_pct']:.2f}%
- 成交量: {us_stock_data['volume']}
- RSI: {us_stock_data.get('rsi', 'N/A')}
- MACD: {us_stock_data.get('macd', 'N/A')}

请分析:
1. 美股技术形态(多头/空头/震荡)
2. 短期走势预测(上涨/下跌/横盘)
3. 对A股 {cn_stock_name} 的影响(正面/负面/中性)
4. 相关性强度评估(强相关/弱相关/无相关)
5. 投资建议(关注/观望/规避)

以JSON格式返回:
{{
    "technical_pattern": "多头/空头/震荡",
    "short_term_trend": "上涨/下跌/横盘",
    "impact": "正面/负面/中性",
    "correlation_strength": "强相关/弱相关/无相关",
    "recommendation": "关注/观望/规避"
}}
"""
            
            response = await self.ai_service.analyze(prompt)
            
            if response:
                import re
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    return json.loads(json_match.group())
            
            return self._get_default_stock_analysis(us_stock_data['change_pct'])
            
        except Exception as e:
            logger.error(f"分析相关美股失败: {str(e)}")
            return self._get_default_stock_analysis(0)
    
    async def generate_daily_us_report(self, holdings: Dict, max_concurrency: int = 5) -> str:
        """生成每日美股市场分析报告"""
        try:
            # 1. 获取美股主要指数数据
            market_indices = await self.data_service.get_us_market_indices()
            
            # 2. 分析市场情绪
            sentiment = await self.analyze_us_market_sentiment(market_indices)
            
            # 3. 获取持仓股票相关美股数据 (并行执行)
            related_analysis = []
            semaphore = asyncio.Semaphore(max_concurrency)
            
            async def _process_stock(stock, sector_name):
                # 识别相关美股
                correlations = await self.correlation_engine.identify_related_us_stocks(
                    stock['name'], sector_name
                )
                
                tasks = []
                for category, stocks in correlations.items():
                    for us_stock in stocks:
                        async def _process_us_stock(us_s, cat):
                            async with semaphore:
                                us_data = await self.data_service.get_us_stock_data(us_s['symbol'])
                                if us_data:
                                    analysis = await self.analyze_related_stock(
                                        us_s['symbol'],
                                        us_data,
                                        stock['name']
                                    )
                                    return {
                                        'cn_stock': stock['name'],
                                        'us_stock': us_s['symbol'],
                                        'us_stock_name': us_s['name'],
                                        'category': cat,
                                        'data': us_data,
                                        'analysis': analysis
                                    }
                                return None
                        
                        tasks.append(_process_us_stock(us_stock, category))
                
                if tasks:
                    results = await asyncio.gather(*tasks)
                    return [r for r in results if r]
                return []

            all_tasks = []
            for sector in holdings.get('sectors', []):
                sector_name = sector['name']
                for stock in sector.get('stocks', []):
                    all_tasks.append(_process_stock(stock, sector_name))
            
            if all_tasks:
                results_list = await asyncio.gather(*all_tasks)
                for results in results_list:
                    related_analysis.extend(results)
            
            # 4. 生成综合报告
            report = self._format_report(market_indices, sentiment, related_analysis)
            
            return report
            
        except Exception as e:
            logger.error(f"生成美股市场报告失败: {str(e)}")
            return f"# 美股市场日报生成失败\n\n错误: {str(e)}"
    
    def _format_report(self, market_indices: Dict, sentiment: Dict,
                      related_analysis: List) -> str:
        """格式化报告"""
        report = f"""# 美股市场日报 - {datetime.now().strftime('%Y年%m月%d日')}

## 一、市场概况

### 主要指数表现
"""
        
        for name, data in market_indices.items():
            change_pct = data.get('change_pct', 0)
            change_symbol = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
            report += f"- **{name}**: {data['previous_close']:.2f} ({change_symbol} {change_pct:+.2f}%)\n"
        
        report += f"""
### 市场情绪
{sentiment.get('market_sentiment', '中性')}

**关键驱动因素**: {sentiment.get('key_drivers', '无')}

## 二、持仓股票相关美股分析

"""
        
        for item in related_analysis:
            change_pct = item['data']['change_pct']
            change_symbol = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
            
            report += f"""### {item['cn_stock']} ← {item['us_stock_name']} ({item['us_stock']})
- **相关性**: {item['category']}
- **美股表现**: ${item['data']['previous_close']:.2f} ({change_symbol} {change_pct:+.2f}%)
- **技术形态**: {item['analysis'].get('technical_pattern', 'N/A')}
- **影响评估**: {item['analysis'].get('impact', '中性')}
- **建议**: {item['analysis'].get('recommendation', '观望')}

"""
        
        # 添加投资建议
        positive_count = sum(1 for a in related_analysis if a['analysis'].get('impact') == '正面')
        negative_count = sum(1 for a in related_analysis if a['analysis'].get('impact') == '负面')
        
        report += """## 三、投资建议

"""
        
        if positive_count > negative_count:
            report += "[OK] **整体影响偏正面**,多数相关美股表现良好,可适度关注A股相关持仓。"
        elif negative_count > positive_count:
            report += "[WARN]️ **整体影响偏负面**,相关美股走弱,建议谨慎操作,注意风险控制。"
        else:
            report += "➡️ **整体影响中性**,美股走势分化,建议观望等待明确信号。"
        
        return report
    
    def _get_default_sentiment_analysis(self, change_pct: float) -> Dict:
        """返回默认市场情绪分析"""
        if change_pct > 1:
            sentiment = "乐观"
        elif change_pct < -1:
            sentiment = "悲观"
        else:
            sentiment = "中性"
        
        return {
            "market_sentiment": sentiment,
            "key_drivers": "市场整体走势",
            "technical_analysis": "需要更多数据",
            "cn_market_impact": "影响有限",
            "cn_opening_prediction": "平开"
        }
    
    def _get_default_stock_analysis(self, change_pct: float) -> Dict:
        """返回默认个股分析"""
        if change_pct > 2:
            impact = "正面"
            recommendation = "关注"
        elif change_pct < -2:
            impact = "负面"
            recommendation = "规避"
        else:
            impact = "中性"
            recommendation = "观望"
        
        return {
            "technical_pattern": "震荡",
            "short_term_trend": "横盘",
            "impact": impact,
            "correlation_strength": "弱相关",
            "recommendation": recommendation
        }
