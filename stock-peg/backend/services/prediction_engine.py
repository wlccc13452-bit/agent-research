"""预测分析引擎"""
import asyncio
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import numpy as np

from config.settings import settings
from models import (
    PredictionResult,
    SectorRotationAnalysis,
    InternationalMarketAnalysis,
    ComprehensivePrediction
)
from services.stock_service import StockService
from services.fundamental_analyzer import FundamentalAnalyzer
from services.us_market_analyzer import USMarketAnalyzer, USMarketCorrelationEngine
from services.ml_predictor import prediction_model
from database.session import async_session_maker
from database.models import SectorReport

logger = logging.getLogger(__name__)


class SectorRotationAnalyzer:
    """板块轮动分析器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SectorRotationAnalyzer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True

    def _get_ts_source(self):
        """获取 TushareDataSource（通过 datasource 统一入口）"""
        from datasource import get_datasource, DataSourceType
        return get_datasource().get_source(DataSourceType.TUSHARE)

    async def get_ts_pro(self):
        """异步获取 Tushare API（通过 datasource 层）"""
        source = self._get_ts_source()
        if source:
            return source
        return None

    @property
    def ts_pro(self):
        """获取 TushareDataSource（通过 datasource 统一入口）"""
        return self._get_ts_source()
    
    async def analyze_rotation(self, holdings_sectors: List[str]) -> Optional[SectorRotationAnalysis]:
        """分析板块轮动 - 基于真实数据
        
        预测算法:
        1. 获取行业和概念板块的资金流向数据
        2. 结合持仓板块,计算综合热度评分
        3. 预测下一个热点板块
        
        评分公式:
        热度评分 = 资金流向权重 * 0.6 + 涨跌幅权重 * 0.4
        """
        try:
            from datasource import get_datasource, DataSourceType
            
            # 1. 获取行业和概念板块资金流向数据
            logger.info(f"正在获取板块资金流向数据，持仓板块: {holdings_sectors}")
            
            akshare_source = get_datasource().get_source(DataSourceType.AKSHARE)
            industry_flows = await akshare_source.get_sector_fund_flow("行业") if akshare_source else None
            concept_flows = await akshare_source.get_sector_fund_flow("概念") if akshare_source else None
            
            if not industry_flows and not concept_flows:
                error_msg = "无法获取板块资金流向数据，可能是网络连接问题或API限流"
                logger.warning(error_msg)
                # 返回一个空的分析结果而不是None
                return SectorRotationAnalysis(
                    date=datetime.now().strftime('%Y-%m-%d'),
                    hotspot_sectors=[],
                    hotspot_changes={},
                    money_flow={},
                    next_hotspot_prediction=None,
                    timestamp=datetime.now()
                )
            
            # 2. 构建板块数据字典 (名称 -> 数据)
            sector_data = {}
            
            # 添加行业板块数据
            if industry_flows:
                for flow in industry_flows:
                    sector_data[flow['name']] = {
                        'name': flow['name'],
                        'change_pct': flow.get('change_pct', 0),
                        'main_net_inflow': flow.get('main_net_inflow', 0),
                        'main_net_inflow_pct': flow.get('main_net_inflow_pct', 0),
                        'type': '行业'
                    }
            
            # 添加概念板块数据
            if concept_flows:
                for flow in concept_flows:
                    sector_data[flow['name']] = {
                        'name': flow['name'],
                        'change_pct': flow.get('change_pct', 0),
                        'main_net_inflow': flow.get('main_net_inflow', 0),
                        'main_net_inflow_pct': flow.get('main_net_inflow_pct', 0),
                        'type': '概念'
                    }
            
            # 3. 分析持仓板块的热度
            hotspot_sectors = []
            hotspot_changes = {}
            money_flow = {}
            sector_scores = {}
            
            # 找到持仓板块对应的资金流向数据
            for sector_name in holdings_sectors:
                # 尝试匹配板块名称 (支持模糊匹配)
                matched_data = None
                for data_name, data in sector_data.items():
                    if sector_name in data_name or data_name in sector_name:
                        matched_data = data
                        break
                
                if matched_data:
                    # 计算热度评分 (综合资金流向和涨跌幅)
                    # 归一化资金流向 (亿元单位,映射到0-100分)
                    inflow = matched_data.get('main_net_inflow') or 0
                    inflow_normalized = min(max(inflow / 10, -100), 100)
                    # 归一化涨跌幅 (映射到0-100分)
                    change_pct = matched_data.get('change_pct') or 0
                    change_normalized = min(max(change_pct * 10, -100), 100)
                    
                    # 综合评分: 资金流向权重0.6 + 涨跌幅权重0.4
                    score = inflow_normalized * 0.6 + change_normalized * 0.4
                    
                    hotspot_sectors.append(sector_name)
                    hotspot_changes[sector_name] = int(matched_data['change_pct'] * 100)  # 转为百分比整数
                    money_flow[sector_name] = matched_data['main_net_inflow']
                    sector_scores[sector_name] = score
                else:
                    # 如果没有找到数据,使用默认值
                    logger.warning(f"未找到板块 '{sector_name}' 的资金流向数据")
                    hotspot_sectors.append(sector_name)
                    hotspot_changes[sector_name] = 0
                    money_flow[sector_name] = 0
                    sector_scores[sector_name] = 0
            
            # 4. 从所有板块中寻找潜在热点 (不仅是持仓板块)
            potential_hotspots = []
            
            # 筛选出资金净流入 > 1亿 且涨幅 > 0 的板块
            for sector_name, data in sector_data.items():
                inflow = data.get('main_net_inflow') or 0
                change_pct = data.get('change_pct') or 0
                if inflow > 10000 and change_pct > 0:
                    # 计算热度评分
                    inflow_normalized = min(max(inflow / 10, -100), 100)
                    change_normalized = min(max(change_pct * 10, -100), 100)
                    score = inflow_normalized * 0.6 + change_normalized * 0.4
                    
                    potential_hotspots.append({
                        'name': sector_name,
                        'score': score,
                        'main_net_inflow': data['main_net_inflow'],
                        'change_pct': data['change_pct'],
                        'type': data['type']
                    })
            
            # 5. 按评分排序
            # 持仓板块按热度排序
            sorted_holdings = sorted(sector_scores.items(), key=lambda x: x[1], reverse=True)
            hotspot_sectors = [s[0] for s in sorted_holdings[:3]]
            
            # 潜在热点板块排序
            potential_hotspots.sort(key=lambda x: x['score'], reverse=True)
            
            # 6. 预测下一个热点板块
            next_hotspot = None
            
            # 从潜在热点中选择评分最高且不在当前热点中的板块
            for hotspot in potential_hotspots:
                if hotspot['name'] not in hotspot_sectors:
                    # 如果该板块资金流入 > 5亿 且评分 > 50
                    if hotspot['main_net_inflow'] > 50000 and hotspot['score'] > 50:
                        next_hotspot = hotspot['name']
                        logger.info(f"预测下一个热点板块: {next_hotspot} (评分:{hotspot['score']:.2f}, 资金流入:{hotspot['main_net_inflow']/10000:.2f}亿)")
                        break
            
            return SectorRotationAnalysis(
                date=datetime.now().strftime('%Y-%m-%d'),
                hotspot_sectors=hotspot_sectors,
                hotspot_changes=hotspot_changes,
                money_flow=money_flow,
                next_hotspot_prediction=next_hotspot,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"板块轮动分析失败: {str(e)}", exc_info=True)
            return None


class TechnicalAnalyzer:
    """技术指标分析器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TechnicalAnalyzer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.stock_service = StockService()
        self._initialized = True
    
    async def analyze_technical(self, stock_code: str) -> Dict:
        """技术指标综合分析"""
        try:
            # 获取技术指标
            indicators = await self.stock_service.get_technical_indicators(stock_code)
            
            if not indicators:
                return self._get_default_technical_analysis()
            
            # 分析MA均线
            ma_status = self._analyze_ma(indicators.ma5, indicators.ma10, indicators.ma20)
            
            # 分析MACD
            macd_signal = self._analyze_macd(indicators.macd, indicators.macd_signal, indicators.macd_hist)
            
            # 分析RSI
            rsi_signal = self._analyze_rsi(indicators.rsi)
            
            # 分析KDJ
            kdj_signal = self._analyze_kdj(indicators.kdj_k, indicators.kdj_d, indicators.kdj_j)
            
            # 综合评分
            score = self._calculate_technical_score(ma_status, macd_signal, rsi_signal, kdj_signal)
            
            return {
                'ma_status': ma_status,
                'macd_signal': macd_signal,
                'rsi_signal': rsi_signal,
                'kdj_signal': kdj_signal,
                'score': score,
                'indicators': {
                    'ma5': indicators.ma5,
                    'ma10': indicators.ma10,
                    'ma20': indicators.ma20,
                    'macd': indicators.macd,
                    'macd_signal': indicators.macd_signal,
                    'macd_hist': indicators.macd_hist,
                    'rsi': indicators.rsi,
                    'kdj_k': indicators.kdj_k,
                    'kdj_d': indicators.kdj_d,
                    'kdj_j': indicators.kdj_j
                }
            }
            
        except Exception as e:
            logger.error(f"技术指标分析失败 {stock_code}: {str(e)}")
            return self._get_default_technical_analysis()
    
    def _analyze_ma(self, ma5: Optional[float], ma10: Optional[float], 
                   ma20: Optional[float]) -> Dict:
        """分析MA均线"""
        if not all([ma5, ma10, ma20]):
            return {'status': 'unknown', 'description': '数据不足'}
        
        # 多头排列: ma5 > ma10 > ma20
        if ma5 > ma10 > ma20:
            return {'status': 'bullish', 'description': '多头排列,趋势向上'}
        # 空头排列: ma5 < ma10 < ma20
        elif ma5 < ma10 < ma20:
            return {'status': 'bearish', 'description': '空头排列,趋势向下'}
        else:
            return {'status': 'oscillation', 'description': '均线缠绕,震荡走势'}
    
    def _analyze_macd(self, macd: Optional[float], macd_signal: Optional[float],
                     macd_hist: Optional[float]) -> Dict:
        """分析MACD"""
        if macd is None or macd_signal is None or macd_hist is None:
            return {'status': 'unknown', 'description': '数据不足'}
        
        signals = []
        
        # 金叉/死叉
        if macd > macd_signal:
            if macd_hist > 0:
                signals.append('金叉')
            else:
                signals.append('即将金叉')
        else:
            if macd_hist < 0:
                signals.append('死叉')
            else:
                signals.append('即将死叉')
        
        # 多空趋势
        if macd > 0:
            signals.append('多头趋势')
        else:
            signals.append('空头趋势')
        
        return {
            'status': 'bullish' if macd_hist > 0 else 'bearish',
            'description': ', '.join(signals)
        }
    
    def _analyze_rsi(self, rsi: Optional[float]) -> Dict:
        """分析RSI"""
        if rsi is None:
            return {'status': 'unknown', 'description': '数据不足'}
        
        if rsi > 80:
            return {'status': 'overbought', 'description': '严重超买,风险较高'}
        elif rsi > 70:
            return {'status': 'overbought', 'description': '超买,注意风险'}
        elif rsi < 20:
            return {'status': 'oversold', 'description': '严重超卖,可能反弹'}
        elif rsi < 30:
            return {'status': 'oversold', 'description': '超卖,关注反弹机会'}
        else:
            return {'status': 'neutral', 'description': '正常区间'}
    
    def _analyze_kdj(self, k: Optional[float], d: Optional[float], 
                    j: Optional[float]) -> Dict:
        """分析KDJ"""
        if k is None or d is None or j is None:
            return {'status': 'unknown', 'description': '数据不足'}
        
        signals = []
        
        # 超买超卖
        if k > 80 and d > 80:
            signals.append('超买区域')
        elif k < 20 and d < 20:
            signals.append('超卖区域')
        else:
            signals.append('正常区域')
        
        # 金叉死叉
        if k > d:
            signals.append('金叉')
        else:
            signals.append('死叉')
        
        return {
            'status': 'bullish' if k > d else 'bearish',
            'description': ', '.join(signals)
        }
    
    def _calculate_technical_score(self, ma_status: Dict, macd_signal: Dict,
                                   rsi_signal: Dict, kdj_signal: Dict) -> float:
        """计算技术面综合评分 (1-5分)"""
        score = 3.0  # 基础分
        
        # MA评分
        if ma_status['status'] == 'bullish':
            score += 0.5
        elif ma_status['status'] == 'bearish':
            score -= 0.5
        
        # MACD评分
        if macd_signal['status'] == 'bullish':
            score += 0.5
        elif macd_signal['status'] == 'bearish':
            score -= 0.5
        
        # RSI评分
        if rsi_signal['status'] == 'oversold':
            score += 0.3  # 超卖可能反弹
        elif rsi_signal['status'] == 'overbought':
            score -= 0.3  # 超买有风险
        
        # KDJ评分
        if kdj_signal['status'] == 'bullish':
            score += 0.3
        elif kdj_signal['status'] == 'bearish':
            score -= 0.3
        
        return max(1.0, min(5.0, score))  # 限制在1-5分
    
    def _get_default_technical_analysis(self) -> Dict:
        """返回默认技术分析"""
        return {
            'ma_status': {'status': 'unknown', 'description': '数据不足'},
            'macd_signal': {'status': 'unknown', 'description': '数据不足'},
            'rsi_signal': {'status': 'unknown', 'description': '数据不足'},
            'kdj_signal': {'status': 'unknown', 'description': '数据不足'},
            'score': 3.0,
            'indicators': {}
        }


class PredictionEngine:
    """预测引擎"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PredictionEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.stock_service = StockService()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.us_market_analyzer = USMarketAnalyzer()
        self.sector_analyzer = SectorRotationAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        self._initialized = True
    
    async def predict(self, stock_code: str, stock_name: str, 
                     sector: str) -> Optional[ComprehensivePrediction]:
        """
        综合预测
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            sector: 所属板块
            
        Returns:
            综合预测结果
        """
        try:
            logger.info(f"开始预测 {stock_code} {stock_name}")
            
            # 1. 获取实时行情
            quote = await self.stock_service.get_quote(stock_code)
            if not quote:
                logger.warning(f"未获取到 {stock_code} 行情数据")
                return None
            
            # 2-5. 并行执行分析步骤（技术面、基本面、板块轮动、国际市场）
            logger.info(f"并行执行分析步骤...")
            technical_analysis, fundamental_data, sector_rotation, international = await asyncio.gather(
                self.technical_analyzer.analyze_technical(stock_code),
                self.fundamental_analyzer.analyze_fundamental(stock_code),
                self.sector_analyzer.analyze_rotation([sector]),
                self._analyze_international_impact(stock_code, stock_name, sector),
                return_exceptions=True  # 允许部分失败
            )
            
            # 处理可能的异常结果
            if isinstance(technical_analysis, Exception):
                logger.warning(f"技术面分析失败: {technical_analysis}")
                technical_analysis = {'score': 3.0}
            if isinstance(fundamental_data, Exception):
                logger.warning(f"基本面分析失败: {fundamental_data}")
                fundamental_data = {}
            if isinstance(sector_rotation, Exception):
                logger.warning(f"板块轮动分析失败: {sector_rotation}")
                sector_rotation = None
            if isinstance(international, Exception):
                logger.warning(f"国际市场分析失败: {international}")
                international = None
            
            fundamental_score = fundamental_data.get('overall_score', 3.0) if fundamental_data else 3.0
            
            # 6. 综合预测
            prediction_result = await self._generate_prediction(
                quote, technical_analysis, fundamental_score, 
                sector_rotation, international
            )
            
            # 7. 构建综合预测结果
            comprehensive_prediction = ComprehensivePrediction(
                stock_code=stock_code,
                stock_name=stock_name,
                prediction_date=datetime.now().strftime('%Y-%m-%d'),
                prediction=prediction_result,
                sector_rotation=sector_rotation,
                international=international,
                technical_score=technical_analysis.get('score', 3.0),
                fundamental_score=fundamental_score,
                overall_score=prediction_result.probability * 5 if prediction_result.direction == '上涨' else (1 - prediction_result.probability) * 5,
                timestamp=datetime.now()
            )
            
            logger.info(f"预测完成: {stock_code} {prediction_result.direction} 概率{prediction_result.probability:.2%}")
            
            return comprehensive_prediction
            
        except Exception as e:
            logger.error(f"预测失败 {stock_code}: {str(e)}")
            return None
    
    async def _analyze_international_impact(self, stock_code: str, stock_name: str,
                                           sector: str) -> Optional[InternationalMarketAnalysis]:
        """分析国际市场影响 - 并行获取数据"""
        try:
            # 并行获取美股指数和相关美股数据
            us_market, correlations = await asyncio.gather(
                self.us_market_analyzer.data_service.get_us_market_indices(),
                self.us_market_analyzer.correlation_engine.identify_related_us_stocks(
                    stock_name, sector
                ),
                return_exceptions=True
            )
            
            # 处理异常
            if isinstance(us_market, Exception):
                logger.warning(f"获取美股指数失败: {us_market}")
                us_market = {}
            if isinstance(correlations, Exception):
                logger.warning(f"获取相关美股失败: {correlations}")
                correlations = {}
            
            # 计算影响权重 (简化版)
            impact_weight = {}
            
            # 美股影响
            if us_market:
                sp500_change = us_market.get('标普500', {}).get('change_pct', 0)
                nasdaq_change = us_market.get('纳斯达克', {}).get('change_pct', 0)
                impact_weight['us_market'] = (sp500_change + nasdaq_change) / 2 * 0.01
            
            # 相关美股影响
            for category, stocks in correlations.items():
                for stock in stocks:
                    symbol = stock['symbol']
                    relevance = stock.get('relevance_score', 0.5)
                    impact_weight[f'{category}_{symbol}'] = relevance
            
            return InternationalMarketAnalysis(
                date=datetime.now().strftime('%Y-%m-%d'),
                us_market=us_market,
                hk_market={},  # 简化版,不获取港股数据
                commodity_prices={},  # 简化版,不获取大宗商品数据
                correlation=impact_weight,
                impact_weight=impact_weight,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"分析国际市场影响失败: {str(e)}")
            return None
    
    async def _generate_prediction(self, quote, technical_analysis: Dict, 
                            fundamental_score: float,
                            sector_rotation: Optional[SectorRotationAnalysis],
                            international: Optional[InternationalMarketAnalysis]) -> PredictionResult:
        """生成预测结果（使用LightGBM模型）"""
        try:
            # 构建特征向量
            features = self._build_features(
                quote, technical_analysis, fundamental_score,
                sector_rotation, international
            )
            
            import asyncio
            # 使用 asyncio.to_thread 包装 CPU 密集型的预测操作
            ml_prediction = await asyncio.to_thread(prediction_model.predict, features)
            
            direction = ml_prediction['direction']
            probability = ml_prediction['probability']
            confidence = ml_prediction['confidence']
            
            # 计算目标价区间
            current_price = quote.price
            volatility = 0.02  # 假设波动率2%
            
            if direction == '上涨':
                target_low = current_price * (1 + volatility)
                target_high = current_price * (1 + volatility * 2)
            elif direction == '下跌':
                target_low = current_price * (1 - volatility * 2)
                target_high = current_price * (1 - volatility)
            else:
                target_low = current_price * (1 - volatility * 0.5)
                target_high = current_price * (1 + volatility * 0.5)
            
            # 判断风险等级
            if direction == '下跌' and probability > 0.6:
                risk_level = '高'
            elif direction == '上涨' and probability > 0.6:
                risk_level = '低'
            else:
                risk_level = '中'
            
            # 关键影响因素（使用特征重要性）
            feature_importance = await asyncio.to_thread(prediction_model.get_feature_importance)
            key_factors = []
            if feature_importance:
                # 取前4个最重要的特征
                for i, (feature, importance) in enumerate(list(feature_importance.items())[:4]):
                    key_factors.append({
                        'factor': feature,
                        'weight': importance / sum(feature_importance.values()) * 100
                    })
            else:
                # 如果没有特征重要性，使用默认值
                # 注意：key_factors 的格式是 List[Dict[str, float]]
                # 每个字典的键是特征名，值是对应的权重
                key_factors = [
                    {'技术面': 35.0},
                    {'基本面': 25.0},
                    {'板块轮动': 25.0},
                    {'国际市场': 15.0}
                ]
            
            return PredictionResult(
                stock_code=quote.code,
                stock_name=quote.name,
                prediction_date=datetime.now().strftime('%Y-%m-%d'),
                direction=direction,
                probability=probability,
                target_price_range=[round(target_low, 2), round(target_high, 2)],
                confidence=confidence,
                risk_level=risk_level,
                key_factors=key_factors,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"生成预测失败: {str(e)}")
            # 返回默认预测
            return PredictionResult(
                stock_code=quote.code if quote else 'UNKNOWN',
                stock_name=quote.name if quote else 'UNKNOWN',
                prediction_date=datetime.now().strftime('%Y-%m-%d'),
                direction='震荡',
                probability=0.5,
                target_price_range=[0.0, 0.0],
                confidence='低',
                risk_level='中',
                key_factors=[],
                timestamp=datetime.now()
            )
    
    def _build_features(self, quote, technical_analysis: Dict,
                       fundamental_score: float,
                       sector_rotation: Optional[SectorRotationAnalysis],
                       international: Optional[InternationalMarketAnalysis]) -> np.ndarray:
        """构建特征向量"""
        features = []
        
        # 技术指标特征
        indicators = technical_analysis.get('indicators', {})
        features.extend([
            float(indicators.get('ma5', 0)),
            float(indicators.get('ma10', 0)),
            float(indicators.get('ma20', 0)),
            float(indicators.get('ma5', 1) / indicators.get('ma10', 1) if indicators.get('ma10') else 1.0),  # ma_ratio
            float(indicators.get('macd', 0)),
            float(indicators.get('macd_signal', 0)),
            float(indicators.get('macd_hist', 0)),
            float(indicators.get('rsi', 50)),
            float(indicators.get('kdj_k', 50)),
            float(indicators.get('kdj_d', 50)),
            float(indicators.get('kdj_j', 50))
        ])
        
        # 价格特征
        features.extend([
            float(quote.change_pct or 0),  # 1日涨跌幅
            0.0,  # 5日涨跌幅（需要历史数据）
            0.0,  # 10日涨跌幅
            0.0,  # 10日波动率
            0.0   # 20日波动率
        ])
        
        # 成交量特征
        features.extend([
            1.0,  # volume_ratio
            float(quote.turnover_rate or 0)
        ])
        
        # 基本面特征
        features.extend([
            0.0,  # pe_ratio（需要从基本面分析获取）
            0.0,  # pb_ratio
            0.0,  # market_cap
            0.0,  # roe
            0.0,  # roa
            0.0   # debt_ratio
        ])
        
        # 市场特征
        sector_ranking = 0
        sector_money_flow = 0
        if sector_rotation:
            # 使用板块资金流向
            sector_money_flow = sum(sector_rotation.money_flow.values()) / len(sector_rotation.money_flow) if sector_rotation.money_flow else 0
        
        us_market_change = 0
        correlation_score = 0
        if international:
            us_market_change = international.impact_weight.get('us_market', 0)
            # 计算平均相关性分数
            if international.correlation:
                correlation_score = np.mean(list(international.correlation.values()))
        
        features.extend([
            float(sector_ranking),
            float(sector_money_flow),
            float(us_market_change),
            float(correlation_score)
        ])
        
        return np.array(features)
    
    async def predict_all_holdings(self, holdings: Dict) -> List[ComprehensivePrediction]:
        """
        预测所有持仓股票 (并行处理)
        """
        tasks = []
        for sector_info in holdings.get('sectors', []):
            sector = sector_info['name']
            for stock in sector_info.get('stocks', []):
                tasks.append(self.predict(stock['code'], stock['name'], sector))
        
        if not tasks:
            return []
            
        logger.info(f"正在并行预测 {len(tasks)} 只股票...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        predictions = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error(f"预测第 {i} 只股票失败: {str(res)}")
            elif res:
                predictions.append(res)
        
        return predictions
