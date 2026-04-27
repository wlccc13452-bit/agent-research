"""PMR (动量比值) 计算服务

根据 stock-pmr-v2.md 文档实现 PMR 计算和评级
"""
import logging
from typing import Dict, Optional, List
from datetime import date
import numpy as np

from database.session import async_session_maker
from database.operations import get_kline_data_by_date_range
from database.models import StockKLineData
from services.stock_service import StockService

logger = logging.getLogger(__name__)


class PMRCalculator:
    """PMR 计算器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PMRCalculator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.stock_service = StockService()
        self._initialized = True
    
    async def calculate_pmr(self, stock_code: str, report_date: Optional[date] = None) -> Optional[Dict]:
        """
        计算股票的 PMR 数据
        
        Args:
            stock_code: 股票代码
            report_date: 报告日期，默认为今天
            
        Returns:
            PMR 数据字典，包含各 MA 周期的 PMR 值和评级
        """
        try:
            import asyncio
            if report_date is None:
                report_date = date.today()
            
            logger.info(f"开始计算 PMR: {stock_code} {report_date}")
            
            # 1. 获取股票历史 K 线数据 (至少 60 个交易日)
            stock_klines = await self._get_stock_klines(stock_code, report_date, 65)
            if not stock_klines or len(stock_klines) < 60:
                logger.warning(f"股票 {stock_code} 历史数据不足")
                return None
            
            # 2. 获取大盘指数数据 (沪深300)
            market_klines = await self._get_market_klines("000300.SH", report_date, 65)
            if not market_klines or len(market_klines) < 60:
                logger.warning("大盘指数数据不足")
                return None
            
            # 3. 计算 PMR 值 (Offload to thread as it uses numpy and loops)
            def _sync_calculate():
                # 计算 PMR 值
                stock_pmr = self._calculate_stock_pmr(stock_klines)
                market_pmr = self._calculate_market_pmr(market_klines)
                
                # 判断行情环境
                market_environment = self._determine_market_environment(market_pmr)
                
                # 根据 PMR 值查表得到评级
                pmr_ratings = self._get_pmr_ratings(stock_pmr, market_environment)
                
                # 计算量能数据
                volume_ratio = self._calculate_volume_ratio(stock_klines)
                turnover_change = self._calculate_turnover_change(stock_klines)
                
                # 量能验证（降级处理）
                pmr_ratings = self._apply_volume_filter(pmr_ratings, volume_ratio)
                
                # 大盘过滤（屏蔽信号）
                pmr_ratings = self._apply_market_filter(pmr_ratings, market_pmr, market_environment)
                
                return stock_pmr, market_pmr, market_environment, pmr_ratings, volume_ratio, turnover_change

            stock_pmr, market_pmr, market_environment, pmr_ratings, volume_ratio, turnover_change = \
                await asyncio.to_thread(_sync_calculate)
            
            # 9. 构建返回数据
            result = {
                'stock_code': stock_code,
                'report_date': report_date.isoformat(),
                'market_environment': market_environment,
                'market_pmr': {
                    'index_code': '000300.SH',
                    'ma20_pmr': market_pmr.get('MA20', 0),
                    'ma60_pmr': market_pmr.get('MA60', 0)
                },
                'stock_pmr': pmr_ratings,
                'volume_ratio': volume_ratio,
                'turnover_change': turnover_change,
                'basic_info': {
                    'latest_close': float(stock_klines[-1].close),
                    'latest_volume': float(stock_klines[-1].volume) if stock_klines[-1].volume else 0
                }
            }
            
            logger.info(f"PMR 计算完成: {stock_code}")
            return result
            
        except Exception as e:
            logger.error(f"计算 PMR 失败 {stock_code}: {str(e)}")
            return None
    
    async def _get_stock_klines(self, stock_code: str, end_date: date, limit: int):
        """获取股票 K 线数据"""
        try:
            async with async_session_maker() as session:
                return await get_kline_data_by_date_range(session, stock_code, end_date, limit)
        except Exception as e:
            logger.error(f"获取股票 K 线失败: {str(e)}")
            return []
    
    async def _get_market_klines(self, index_code: str, end_date: date, limit: int) -> List[Dict]:
        """获取大盘指数 K 线数据"""
        try:
            # 从数据库或 API 获取沪深300数据
            # 这里使用 stock_service 的方法
            klines_data = await self.stock_service.get_index_kline(index_code, 'day', limit)
            
            if not klines_data:
                logger.warning(f"未获取到指数 {index_code} 数据")
                return []
            
            return klines_data
        except Exception as e:
            logger.error(f"获取大盘 K 线失败: {str(e)}")
            return []
    
    def _calculate_stock_pmr(self, klines: List[StockKLineData]) -> Dict:
        """计算股票各 MA 周期的 PMR 值"""
        try:
            # 提取收盘价
            close_prices = np.array([float(k.close) for k in klines])
            
            # 计算各 MA
            ma5 = self._calculate_ma(close_prices, 5)
            ma10 = self._calculate_ma(close_prices, 10)
            ma20 = self._calculate_ma(close_prices, 20)
            ma30 = self._calculate_ma(close_prices, 30)
            ma60 = self._calculate_ma(close_prices, 60)
            
            # 计算各 MA 的 PMR 值
            pmr = {}
            
            # PMR(N) = (股价N日涨幅率) / (MA_N的N日涨幅率)
            for period, ma_values, n in [
                ('MA5', ma5, 5),
                ('MA10', ma10, 10),
                ('MA20', ma20, 20),
                ('MA30', ma30, 30),
                ('MA60', ma60, 60)
            ]:
                if len(close_prices) < n + 1 or len(ma_values) < n + 1:
                    pmr[period] = 0
                    continue
                
                # 股价 N 日涨幅率
                price_return = (close_prices[-1] - close_prices[-n-1]) / close_prices[-n-1]
                
                # MA_N 的 N 日涨幅率
                ma_return = (ma_values[-1] - ma_values[-n-1]) / ma_values[-n-1]
                
                # PMR
                if abs(ma_return) < 1e-6:  # 避免除以 0
                    pmr_value = 1.0 if abs(price_return) < 1e-6 else 0
                else:
                    pmr_value = (1 + price_return) / (1 + ma_return)
                
                pmr[period] = pmr_value
            
            return pmr
            
        except Exception as e:
            logger.error(f"计算股票 PMR 失败: {str(e)}")
            return {}
    
    def _calculate_market_pmr(self, klines: List[Dict]) -> Dict:
        """计算大盘 PMR 值"""
        try:
            # 提取收盘价
            close_prices = np.array([k.get('close', 0) for k in klines])
            
            # 计算 MA20 和 MA60
            ma20 = self._calculate_ma(close_prices, 20)
            ma60 = self._calculate_ma(close_prices, 60)
            
            pmr = {}
            
            # MA20 PMR
            if len(close_prices) >= 21 and len(ma20) >= 21:
                price_return = (close_prices[-1] - close_prices[-21]) / close_prices[-21]
                ma_return = (ma20[-1] - ma20[-21]) / ma20[-21]
                pmr['MA20'] = (1 + price_return) / (1 + ma_return) if abs(ma_return) > 1e-6 else 1.0
            
            # MA60 PMR
            if len(close_prices) >= 61 and len(ma60) >= 61:
                price_return = (close_prices[-1] - close_prices[-61]) / close_prices[-61]
                ma_return = (ma60[-1] - ma60[-61]) / ma60[-61]
                pmr['MA60'] = (1 + price_return) / (1 + ma_return) if abs(ma_return) > 1e-6 else 1.0
            
            return pmr
            
        except Exception as e:
            logger.error(f"计算大盘 PMR 失败: {str(e)}")
            return {}
    
    def _calculate_ma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """计算移动平均线 (向量化优化)"""
        if len(prices) < period:
            return np.full_like(prices, np.nan)
        
        # 使用 numpy 的滑动窗口求均值
        ret = np.cumsum(prices, dtype=float)
        ret[period:] = ret[period:] - ret[:-period]
        ma = np.full_like(prices, np.nan)
        ma[period-1:] = ret[period-1:] / period
        return ma
    
    def _determine_market_environment(self, market_pmr: Dict) -> str:
        """
        判断行情环境
        
        上涨趋势: 大盘 MA20 PMR ≥1.05 且 MA60 PMR ≥1.02
        下跌/震荡: 其他情况
        """
        ma20_pmr = market_pmr.get('MA20', 0)
        ma60_pmr = market_pmr.get('MA60', 0)
        
        if ma20_pmr >= 1.05 and ma60_pmr >= 1.02:
            return "上涨行情"
        else:
            return "下跌/震荡行情"
    
    def _get_pmr_ratings(self, stock_pmr: Dict, market_environment: str) -> Dict:
        """
        根据 PMR 值查表得到评级
        
        使用 stock-pmr-v2.md 中的评级表
        """
        ratings = {}
        
        # 根据行情环境选择评级表
        if market_environment == "上涨行情":
            rating_table = self._get_uptrend_rating_table()
        else:
            rating_table = self._get_downtrend_rating_table()
        
        # 查表
        for ma_period, pmr_value in stock_pmr.items():
            rating = self._lookup_rating(pmr_value, rating_table[ma_period])
            ratings[ma_period] = {
                'pmr': round(pmr_value, 4),
                'rating': rating
            }
        
        return ratings
    
    def _get_uptrend_rating_table(self) -> Dict:
        """上涨行情评级标准表"""
        return {
            'MA5': {
                '很强': (1.35, float('inf')),
                '强': (1.20, 1.34),
                '中性偏强': (1.05, 1.19),
                '中性': (0.90, 1.04),
                '弱': (0, 0.89)
            },
            'MA10': {
                '很强': (1.30, float('inf')),
                '强': (1.15, 1.29),
                '中性偏强': (1.02, 1.14),
                '中性': (0.88, 1.01),
                '弱': (0, 0.87)
            },
            'MA20': {
                '很强': (1.25, float('inf')),
                '强': (1.12, 1.24),
                '中性偏强': (1.00, 1.11),
                '中性': (0.85, 0.99),
                '弱': (0, 0.84)
            },
            'MA30': {
                '很强': (1.20, float('inf')),
                '强': (1.08, 1.19),
                '中性偏强': (0.98, 1.07),
                '中性': (0.82, 0.97),
                '弱': (0, 0.81)
            },
            'MA60': {
                '很强': (1.15, float('inf')),
                '强': (1.05, 1.14),
                '中性偏强': (0.95, 1.04),
                '中性': (0.80, 0.94),
                '弱': (0, 0.79)
            }
        }
    
    def _get_downtrend_rating_table(self) -> Dict:
        """下跌/震荡行情评级标准表"""
        return {
            'MA5': {
                '很强': (1.55, float('inf')),
                '强': (1.35, 1.54),
                '中性偏强': (1.15, 1.34),
                '中性': (0.95, 1.14),
                '弱': (0, 0.94)
            },
            'MA10': {
                '很强': (1.45, float('inf')),
                '强': (1.25, 1.44),
                '中性偏强': (1.05, 1.24),
                '中性': (0.90, 1.04),
                '弱': (0, 0.89)
            },
            'MA20': {
                '很强': (1.35, float('inf')),
                '强': (1.15, 1.34),
                '中性偏强': (1.00, 1.14),
                '中性': (0.85, 0.99),
                '弱': (0, 0.84)
            },
            'MA30': {
                '很强': (1.25, float('inf')),
                '强': (1.10, 1.24),
                '中性偏强': (0.95, 1.09),
                '中性': (0.80, 0.94),
                '弱': (0, 0.79)
            },
            'MA60': {
                '很强': (1.15, float('inf')),
                '强': (1.05, 1.14),
                '中性偏强': (0.90, 1.04),
                '中性': (0.75, 0.89),
                '弱': (0, 0.74)
            }
        }
    
    def _lookup_rating(self, pmr_value: float, rating_ranges: Dict) -> str:
        """查表得到评级"""
        for rating, (low, high) in rating_ranges.items():
            if low <= pmr_value <= high:
                return rating
        return '弱'
    
    def _calculate_volume_ratio(self, klines: List[StockKLineData]) -> float:
        """计算量比 = 当日成交量 / 前5日平均成交量"""
        if len(klines) < 6:
            return 1.0
        
        try:
            current_volume = float(klines[-1].volume) if klines[-1].volume else 0
            avg_volume = np.mean([float(k.volume) if k.volume else 0 for k in klines[-6:-1]])
            
            if avg_volume < 1e-6:
                return 1.0
            
            return current_volume / avg_volume
        except Exception:
            return 1.0
    
    def _calculate_turnover_change(self, klines: List[StockKLineData]) -> float:
        """计算换手率变化"""
        if len(klines) < 2:
            return 0.0
        
        try:
            current_turnover = float(klines[-1].turnover_rate) if klines[-1].turnover_rate else 0
            prev_turnover = float(klines[-2].turnover_rate) if klines[-2].turnover_rate else 0
            
            if prev_turnover < 1e-6:
                return 0.0
            
            return (current_turnover - prev_turnover) / prev_turnover * 100
        except Exception:
            return 0.0
    
    def _apply_volume_filter(self, pmr_ratings: Dict, volume_ratio: float) -> Dict:
        """
        量能验证
        
        量比 < 1.2 时，PMR 评级降一档
        """
        if volume_ratio < 1.2:
            rating_order = ['很强', '强', '中性偏强', '中性', '弱']
            
            for ma_period in pmr_ratings:
                current_rating = pmr_ratings[ma_period]['rating']
                current_idx = rating_order.index(current_rating)
                
                # 降一档（如果已经是最低档则不变）
                if current_idx < len(rating_order) - 1:
                    pmr_ratings[ma_period]['rating'] = rating_order[current_idx + 1]
        
        return pmr_ratings
    
    def _apply_market_filter(self, pmr_ratings: Dict, market_pmr: Dict, market_environment: str) -> Dict:
        """
        大盘过滤
        
        大盘 MA60 PMR < 1.00 时，屏蔽所有"强"信号
        """
        ma60_pmr = market_pmr.get('MA60', 0)
        
        if ma60_pmr < 1.00:
            for ma_period in pmr_ratings:
                if pmr_ratings[ma_period]['rating'] == '强':
                    pmr_ratings[ma_period]['rating'] = '中性偏强'
        
        return pmr_ratings
