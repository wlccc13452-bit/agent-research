"""Alexander Elder强力指数（Force Index）计算服务

Force Index = (Close_t - Close_{t-1}) * Volume_t

用于评估股票的买卖力量和趋势强度
"""
import logging
import json
from typing import Dict, Optional, List, Union
from datetime import date, datetime, timedelta
from decimal import Decimal
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from services.stock_data_service import stock_data_service
from services.stock_service import StockService
from database.operations import get_force_index_cache, save_force_index_cache

logger = logging.getLogger(__name__)


class ForceIndexCalculator:
    """强力指数计算器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ForceIndexCalculator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.stock_service = StockService()
        self._initialized = True
    
    async def calculate_force_index(
        self,
        db: AsyncSession,
        stock_code: str,
        stock_name: str = None,
        period: str = "day",
        ema_short: int = 2,
        ema_long: int = 13,
        count: int = 100,
        use_cache: bool = True,
        local_only: bool = False
    ) -> Optional[Dict]:
        """
        计算股票的Force Index指标
        
        Args:
            db: 数据库会话
            stock_code: 股票代码
            stock_name: 股票名称（可选）
            period: K线周期 (day/week/month)
            ema_short: 短期EMA周期，默认2
            ema_long: 长期EMA周期，默认13
            count: 获取K线数量
            use_cache: 是否使用缓存，默认True
            
        Returns:
            Force Index分析结果，包含买卖信号
        """
        try:
            logger.info(f"Start calculating Force Index: {stock_code}")
            
            # 设置默认股票名称
            if not stock_name:
                stock_name = stock_code
            
            # 1. 检查数据库缓存（如果启用缓存且是日线数据）
            if use_cache and period == "day":
                cached_result = await self._get_cached_result(
                    db, stock_code, period, ema_short, ema_long
                )
                if cached_result:
                    logger.info(f"Using cached Force Index for {stock_code}")
                    # 确保缓存的stock_name是正确的
                    cached_result['stock_name'] = stock_name
                    return cached_result
            
            # 2. 获取K线数据 (优先本地数据库)
            klines = await self._get_klines_data(db, stock_code, period, count + 10, local_only=local_only)
            
            if not klines or len(klines) < ema_long + 5:
                logger.warning(f"Insufficient K-line data for {stock_code}, need at least {ema_long + 5} records")
                return None
            
            # 3. 计算Force Index
            raw_force_index = self._calculate_raw_force_index(klines)
            
            # 4. 计算EMA平滑
            fi_short_ema = self._calculate_ema(raw_force_index, ema_short)
            fi_long_ema = self._calculate_ema(raw_force_index, ema_long)
            
            # 5. 分析5天趋势变化
            trend_change = self._analyze_trend_change(fi_short_ema, fi_long_ema, raw_force_index)
            
            # 6. 生成买卖信号(考虑趋势)
            signals = self._generate_signals_with_trend(
                raw_force_index, 
                fi_short_ema, 
                fi_long_ema, 
                klines,
                trend_change
            )
            
            # 7. 构建返回结果
            logger.info(f"Building result with {len(klines)} klines, {len(raw_force_index)} force_index values")
            result = {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'period': period,
                'calculation_date': datetime.now().isoformat(),
                'parameters': {
                    'ema_short': ema_short,
                    'ema_long': ema_long
                },
                'current_values': {
                    'raw_force_index': round(raw_force_index[-1], 2),
                    'fi_short_ema': round(fi_short_ema[-1], 2),
                    'fi_long_ema': round(fi_long_ema[-1], 2),
                    'price_change': round(float(klines[-1].close) - float(klines[-2].close), 2),
                    'volume': int(klines[-1].volume) if klines[-1].volume else 0
                },
                'signals': signals,
                'trend_analysis': self._analyze_trend(fi_short_ema, fi_long_ema),
                'trend_change': trend_change,
                'strength_analysis': self._analyze_strength(fi_short_ema, raw_force_index),
                'recent_data': self._build_recent_data(
                    klines, 
                    raw_force_index, 
                    fi_short_ema, 
                    fi_long_ema
                )
            }
            
            # 7. 存储到数据库缓存（如果是日线数据）
            logger.info(f"Checking if should save cache: period={period}, should_save={period == 'day'}")
            if period == "day":
                logger.info(f"Attempting to save Force Index cache for {stock_code}...")
                try:
                    await self._save_to_cache(
                        db, stock_code, stock_name, result, period, ema_short, ema_long
                    )
                except Exception as save_error:
                    logger.error(f"Exception during cache save: {str(save_error)}", exc_info=True)
            else:
                logger.info(f"Skipping cache save for period={period}")
            
            logger.info(f"Force Index calculation complete: {stock_code}, signal: {signals['current_signal']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate Force Index for {stock_code}: {str(e)}", exc_info=True)
            return None
    
    async def _get_klines_data(
        self, 
        db: AsyncSession, 
        stock_code: str, 
        period: str, 
        count: int,
        local_only: bool = False
    ) -> List:
        """
        获取K线数据（优先本地数据库，不足则从API获取）
        
        Args:
            db: 数据库会话
            stock_code: 股票代码
            period: K线周期
            count: 需要的数量
            
        Returns:
            K线数据列表
        """
        try:
            # 优先从本地数据库获取
            klines = await stock_data_service.get_kline_from_db(db, stock_code, period, count)
            
            # 如果数据不足，根据策略决定是否从网络API获取
            if len(klines) < count and not local_only:
                logger.info(f"Local data insufficient ({len(klines)}/{count}), fetching from API")
                klines = await stock_data_service.stock_service.get_kline(stock_code, period, count)
            
            return klines
            
        except Exception as e:
            logger.error(f"Failed to fetch K-line data: {str(e)}")
            return []
    
    def _calculate_raw_force_index(self, klines: List) -> np.ndarray:
        """
        计算原始Force Index
        
        Force Index = (Close_t - Close_{t-1}) * Volume_t
        
        Args:
            klines: K线数据列表
            
        Returns:
            Force Index数组
        """
        force_index = np.zeros(len(klines))
        
        for i in range(1, len(klines)):
            price_change = float(klines[i].close) - float(klines[i-1].close)
            volume = float(klines[i].volume) if klines[i].volume else 0
            force_index[i] = price_change * volume
        
        return force_index
    
    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        计算指数移动平均(EMA)
        
        EMA_t = Price_t * k + EMA_{t-1} * (1-k)
        k = 2 / (period + 1)
        
        Args:
            data: 数据数组
            period: EMA周期
            
        Returns:
            EMA数组
        """
        ema = np.zeros(len(data))
        k = 2 / (period + 1)
        
        # 第一个EMA值使用SMA
        if len(data) >= period:
            ema[period-1] = np.mean(data[:period])
            
            # 后续使用EMA公式
            for i in range(period, len(data)):
                ema[i] = data[i] * k + ema[i-1] * (1 - k)
        
        return ema
    
    def _analyze_trend_change(
        self, 
        fi_short: np.ndarray, 
        fi_long: np.ndarray,
        raw_fi: np.ndarray
    ) -> Dict:
        """
        分析最近5天的趋势变化
        
        Returns:
            {
                'trend_type': '上涨趋势'/'下跌趋势'/'趋势转折',
                'fi2_trend': FI2变化趋势,
                'fi13_trend': FI13变化趋势,
                'trend_strength_change': '增强'/'减弱',
                'trend_days': 趋势持续天数,
                'description': 趋势描述
            }
        """
        analysis = {
            'trend_type': '横盘',
            'fi2_trend': '平稳',
            'fi13_trend': '平稳',
            'trend_strength_change': '无变化',
            'trend_days': 0,
            'description': ''
        }
        
        # 需要至少5天数据
        if len(fi_short) < 5 or len(fi_long) < 5:
            analysis['description'] = '数据不足，无法分析趋势'
            return analysis
        
        # 分析FI2(短期)趋势 - 最近5天
        fi2_recent = fi_short[-5:]
        fi2_positive_days = sum(1 for fi in fi2_recent if fi > 0)
        fi2_trend_slope = fi2_recent[-1] - fi2_recent[0]  # 变化方向
        
        if fi2_positive_days >= 4:
            analysis['fi2_trend'] = '持续为正'
        elif fi2_positive_days <= 1:
            analysis['fi2_trend'] = '持续为负'
        elif fi2_trend_slope > 0:
            analysis['fi2_trend'] = '上升中'
        elif fi2_trend_slope < 0:
            analysis['fi2_trend'] = '下降中'
        
        # 分析FI13(长期)趋势 - 最近5天
        fi13_recent = fi_long[-5:]
        fi13_positive_days = sum(1 for fi in fi13_recent if fi > 0)
        fi13_trend_slope = fi13_recent[-1] - fi13_recent[0]
        
        if fi13_positive_days >= 4:
            analysis['fi13_trend'] = '持续为正'
        elif fi13_positive_days <= 1:
            analysis['fi13_trend'] = '持续为负'
        elif fi13_trend_slope > 0:
            analysis['fi13_trend'] = '上升中'
        elif fi13_trend_slope < 0:
            analysis['fi13_trend'] = '下降中'
        
        # 判断趋势类型
        current_fi13 = fi_long[-1]
        
        # 上涨趋势: FI13为正且最近3天FI2多为正
        if current_fi13 > 0 and fi2_positive_days >= 3:
            analysis['trend_type'] = '上涨趋势'
            analysis['trend_days'] = fi2_positive_days
            
            # 判断趋势强度变化
            if fi13_trend_slope > 0:
                analysis['trend_strength_change'] = '增强'
            elif fi13_trend_slope < 0:
                analysis['trend_strength_change'] = '减弱'
            
            analysis['description'] = f"上涨趋势中，已持续{fi2_positive_days}天买入力量占优"
            
        # 下跌趋势: FI13为负且最近3天FI2多为负
        elif current_fi13 < 0 and fi2_positive_days <= 2:
            analysis['trend_type'] = '下跌趋势'
            analysis['trend_days'] = 5 - fi2_positive_days
            
            # 判断趋势强度变化
            if fi13_trend_slope < 0:
                analysis['trend_strength_change'] = '增强'
            elif fi13_trend_slope > 0:
                analysis['trend_strength_change'] = '减弱'
            
            analysis['description'] = f"下跌趋势中，已持续{5-fi2_positive_days}天卖出力量占优"
            
        # 趋势转折: FI13从负转正或从正转负
        elif len(fi_long) >= 2:
            if fi_long[-2] <= 0 and fi_long[-1] > 0:
                analysis['trend_type'] = '趋势转折'
                analysis['description'] = 'FI13从负转正，可能开启上涨趋势'
            elif fi_long[-2] >= 0 and fi_long[-1] < 0:
                analysis['trend_type'] = '趋势转折'
                analysis['description'] = 'FI13从正转负，可能开启下跌趋势'
            else:
                analysis['trend_type'] = '横盘震荡'
                analysis['description'] = '趋势不明确，建议观望'
        
        return analysis
    
    def _generate_signals_with_trend(
        self, 
        raw_fi: np.ndarray,
        fi_short: np.ndarray, 
        fi_long: np.ndarray,
        klines: List,
        trend_change: Dict
    ) -> Dict:
        """
        根据趋势生成买卖信号
        
        不同趋势下采用不同的分析策略:
        - 上涨趋势: 关注FI2变化，寻找加仓机会
        - 下跌趋势: 关注反弹，寻找减仓机会
        - 趋势转折: 谨慎操作，等待确认
        """
        signals = {
            'current_signal': '中性',
            'signal_strength': 0,
            'buy_signals': [],
            'sell_signals': [],
            'trend_based_strategy': ''  # 新增：基于趋势的策略建议
        }
        
        trend_type = trend_change['trend_type']
        
        # ========== 上涨趋势中的分析 ==========
        if trend_type == '上涨趋势':
            # FI2 > 0: 买入信号增强
            if fi_short[-1] > 0:
                signals['buy_signals'].append('上涨趋势中，FI2为正，买入力量强劲')
                signals['signal_strength'] += 3
            # FI2 < 0: 短期回调，可能是加仓机会
            else:
                signals['buy_signals'].append('上涨趋势中的短期回调，可能是加仓良机')
                signals['signal_strength'] += 1
            
            # FI13持续增强
            if trend_change['trend_strength_change'] == '增强':
                signals['buy_signals'].append('长期趋势持续增强')
                signals['signal_strength'] += 2
            
            # FI2穿越零轴向上
            if len(fi_short) >= 2 and fi_short[-2] < 0 and fi_short[-1] > 0:
                signals['buy_signals'].append('FI2从负转正，上涨动能恢复')
                signals['signal_strength'] += 2
            
            signals['trend_based_strategy'] = '上涨趋势，建议持股或逢低加仓'
        
        # ========== 下跌趋势中的分析 ==========
        elif trend_type == '下跌趋势':
            # FI2 < 0: 卖出信号增强
            if fi_short[-1] < 0:
                signals['sell_signals'].append('下跌趋势中，FI2为负，卖出力量强劲')
                signals['signal_strength'] -= 3
            # FI2 > 0: 短期反弹，可能是减仓机会
            else:
                signals['sell_signals'].append('下跌趋势中的短期反弹，建议减仓')
                signals['signal_strength'] -= 1
            
            # FI13持续增强(负方向)
            if trend_change['trend_strength_change'] == '增强':
                signals['sell_signals'].append('长期下跌趋势加剧')
                signals['signal_strength'] -= 2
            
            # FI2穿越零轴向下
            if len(fi_short) >= 2 and fi_short[-2] > 0 and fi_short[-1] < 0:
                signals['sell_signals'].append('FI2从正转负，下跌动能增强')
                signals['signal_strength'] -= 2
            
            signals['trend_based_strategy'] = '下跌趋势，建议减仓或观望'
        
        # ========== 趋势转折中的分析 ==========
        elif trend_type == '趋势转折':
            # FI13从负转正
            if fi_long[-1] > 0:
                signals['buy_signals'].append('FI13从负转正，可能开启上涨趋势')
                signals['signal_strength'] += 2
                # 但需要FI2确认
                if fi_short[-1] > 0:
                    signals['buy_signals'].append('FI2同步转正，转折信号确认')
                    signals['signal_strength'] += 2
                else:
                    signals['buy_signals'].append('但FI2仍为负，建议等待确认')
                    signals['signal_strength'] -= 1
            # FI13从正转负
            else:
                signals['sell_signals'].append('FI13从正转负，可能开启下跌趋势')
                signals['signal_strength'] -= 2
                # 检查FI2确认
                if fi_short[-1] < 0:
                    signals['sell_signals'].append('FI2同步转负，转折信号确认')
                    signals['signal_strength'] -= 2
                else:
                    signals['sell_signals'].append('但FI2仍为正，建议等待确认')
                    signals['signal_strength'] += 1
            
            signals['trend_based_strategy'] = '趋势转折，建议谨慎操作，等待确认信号'
        
        # ========== 横盘震荡中的分析 ==========
        else:
            # 检查FI2穿越零轴
            if len(fi_short) >= 2:
                if fi_short[-2] < 0 and fi_short[-1] > 0:
                    signals['buy_signals'].append('FI2从负转正')
                    signals['signal_strength'] += 1
                elif fi_short[-2] > 0 and fi_short[-1] < 0:
                    signals['sell_signals'].append('FI2从正转负')
                    signals['signal_strength'] -= 1
            
            signals['trend_based_strategy'] = '横盘震荡，建议观望'
        
        # 确定当前信号
        signal_strength = signals['signal_strength']
        
        if signal_strength >= 7:
            signals['current_signal'] = '强烈买入'
        elif signal_strength >= 4:
            signals['current_signal'] = '买入'
        elif signal_strength >= 1:
            signals['current_signal'] = '偏强'
        elif signal_strength <= -7:
            signals['current_signal'] = '强烈卖出'
        elif signal_strength <= -4:
            signals['current_signal'] = '卖出'
        elif signal_strength <= -1:
            signals['current_signal'] = '偏弱'
        else:
            signals['current_signal'] = '中性'
        
        return signals
    
    def _analyze_trend(self, fi_short: np.ndarray, fi_long: np.ndarray) -> Dict:
        """
        分析趋势方向和强度
        """
        analysis = {
            'trend_direction': '横盘',
            'trend_strength': '弱',
            'description': ''
        }
        
        # 判断趋势方向
        if fi_long[-1] > 0:
            analysis['trend_direction'] = '上涨'
        elif fi_long[-1] < 0:
            analysis['trend_direction'] = '下跌'
        else:
            analysis['trend_direction'] = '横盘'
        
        # 判断趋势强度（基于长期EMA的绝对值和变化率）
        avg_volume = np.mean(np.abs(fi_long[-20:])) if len(fi_long) >= 20 else abs(fi_long[-1])
        
        if avg_volume > 10000000:
            analysis['trend_strength'] = '很强'
        elif avg_volume > 5000000:
            analysis['trend_strength'] = '强'
        elif avg_volume > 1000000:
            analysis['trend_strength'] = '中等'
        else:
            analysis['trend_strength'] = '弱'
        
        # 生成描述
        if analysis['trend_direction'] == '上涨':
            analysis['description'] = f"当前处于{analysis['trend_strength']}上涨趋势，买入力量占优"
        elif analysis['trend_direction'] == '下跌':
            analysis['description'] = f"当前处于{analysis['trend_strength']}下跌趋势，卖出力量占优"
        else:
            analysis['description'] = "当前趋势不明朗，建议观望"
        
        return analysis
    
    def _analyze_strength(self, fi_short: np.ndarray, raw_fi: np.ndarray) -> Dict:
        """
        分析买卖力量强度
        """
        analysis = {
            'buying_power': 0,
            'selling_power': 0,
            'power_balance': '',
            'divergence': False
        }
        
        # 计算买卖力量（最近5日）
        recent_fi = raw_fi[-5:]
        buying_days = sum(1 for fi in recent_fi if fi > 0)
        selling_days = 5 - buying_days
        
        analysis['buying_power'] = buying_days * 20  # 转换为百分比
        analysis['selling_power'] = selling_days * 20
        
        # 力量平衡判断
        if buying_days >= 4:
            analysis['power_balance'] = '强烈买入主导'
        elif buying_days >= 3:
            analysis['power_balance'] = '买入主导'
        elif buying_days <= 1:
            analysis['power_balance'] = '强烈卖出主导'
        elif buying_days <= 2:
            analysis['power_balance'] = '卖出主导'
        else:
            analysis['power_balance'] = '买卖平衡'
        
        # 检测背离（价格创新高但Force Index未创新高）
        # 简化版本：检查最近趋势
        if len(raw_fi) >= 10:
            recent_max = max(raw_fi[-10:])
            if fi_short[-1] < recent_max * 0.5:
                analysis['divergence'] = True
        
        return analysis
    
    def _build_recent_data(
        self, 
        klines: List, 
        raw_fi: np.ndarray, 
        fi_short: np.ndarray, 
        fi_long: np.ndarray
    ) -> List[Dict]:
        """
        构建最近N天的详细数据
        """
        recent_data = []
        
        for i in range(len(klines)):
            recent_data.append({
                'date': klines[i].date,
                'close': float(klines[i].close),
                'volume': int(klines[i].volume) if klines[i].volume else 0,
                'raw_force_index': round(raw_fi[i], 2),
                'fi_short_ema': round(fi_short[i], 2),
                'fi_long_ema': round(fi_long[i], 2),
                'signal': '买入' if raw_fi[i] > 0 else '卖出'
            })
        
        return recent_data
    
    async def _get_cached_result(
        self,
        db: AsyncSession,
        stock_code: str,
        period: str,
        ema_short: int,
        ema_long: int
    ) -> Optional[Dict]:
        """
        从数据库获取缓存的Force Index结果
        
        只返回今天的缓存结果（交易日有效）
        """
        try:
            return await get_force_index_cache(db, stock_code, period, ema_short, ema_long)
        except Exception as e:
            logger.warning(f"Failed to get cached Force Index for {stock_code}: {str(e)}")
            return None
    
    async def _save_to_cache(
        self,
        db: AsyncSession,
        stock_code: str,
        stock_name: str,
        result: Dict,
        period: str,
        ema_short: int,
        ema_long: int
    ) -> None:
        """
        保存Force Index结果到数据库缓存
        
        注意：使用独立的数据库session来避免事务冲突
        """
        from database.session import async_session_maker
        
        try:
            logger.info(f"Saving Force Index cache for {stock_code}...")
            
            # 使用独立的session来保存，避免与外部session的事务冲突
            async with async_session_maker() as save_db:
                success = await save_force_index_cache(
                    save_db, stock_code, stock_name, result, period, ema_short, ema_long
                )
                if success:
                    logger.info(f"Force Index cache saved successfully for {stock_code}")
                else:
                    logger.error(f"Failed to save Force Index cache for {stock_code}")
            
        except Exception as e:
            logger.error(f"Failed to save Force Index cache for {stock_code}: {str(e)}", exc_info=True)


# 单例实例
force_index_calculator = ForceIndexCalculator()
