"""
技术指标计算 - 多进程版本

用于 ProcessPoolExecutor 执行 CPU 密集型计算，避免阻塞主事件循环
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def calculate_pmr_mp(klines_data: List[Dict]) -> Optional[Dict]:
    """
    计算 PMR 指标（多进程版本）
    
    Args:
        klines_data: K线数据列表，格式: [{'close': float, 'high': float, 'low': float, 'volume': int, ...}, ...]
        
    Returns:
        PMR 数据字典
    """
    try:
        if not klines_data or len(klines_data) < 120:
            return None
        
        # 提取价格和成交量数据
        closes = np.array([float(k['close']) for k in klines_data])
        highs = np.array([float(k['high']) for k in klines_data])
        lows = np.array([float(k['low']) for k in klines_data])
        volumes = np.array([int(k.get('volume', 0)) for k in klines_data])
        
        # 计算 MA
        ma5 = _calculate_ma(closes, 5)
        ma10 = _calculate_ma(closes, 10)
        ma20 = _calculate_ma(closes, 20)
        ma60 = _calculate_ma(closes, 60)
        ma120 = _calculate_ma(closes, 120)
        
        # 计算 EMA
        ema20 = _calculate_ema(closes, 20)
        
        # 计算 PMR (Price Moving Ratio)
        pmr = (closes - ma20) / ma20 * 100
        
        # 构建返回结果
        result = {
            'dates': [k.get('trade_date', k.get('date')) for k in klines_data],
            'closes': closes.tolist(),
            'highs': highs.tolist(),
            'lows': lows.tolist(),
            'volumes': volumes.tolist(),
            'ma5': ma5.tolist(),
            'ma10': ma10.tolist(),
            'ma20': ma20.tolist(),
            'ma60': ma60.tolist(),
            'ma120': ma120.tolist(),
            'ema20': ema20.tolist(),
            'pmr': pmr.tolist()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"PMR calculation failed: {str(e)}")
        return None


def calculate_force_index_mp(klines_data: List[Dict], ema_short: int = 2, ema_long: int = 13) -> Optional[Dict]:
    """
    计算 Force Index 指标（多进程版本）
    
    Args:
        klines_data: K线数据列表
        ema_short: 短期 EMA 周期
        ema_long: 长期 EMA 周期
        
    Returns:
        Force Index 分析结果
    """
    try:
        if not klines_data or len(klines_data) < ema_long + 5:
            return None
        
        # 提取价格和成交量数据
        closes = np.array([float(k['close']) for k in klines_data])
        volumes = np.array([int(k.get('volume', 0)) for k in klines_data])
        
        # 计算原始 Force Index
        raw_force_index = np.zeros(len(klines_data))
        for i in range(1, len(klines_data)):
            price_change = closes[i] - closes[i-1]
            volume = volumes[i]
            raw_force_index[i] = price_change * volume
        
        # 计算 EMA 平滑
        fi_short_ema = _calculate_ema(raw_force_index, ema_short)
        fi_long_ema = _calculate_ema(raw_force_index, ema_long)
        
        # 分析趋势
        trend_analysis = _analyze_trend(fi_short_ema, fi_long_ema)
        
        # 生成信号
        signals = _generate_signals(raw_force_index, fi_short_ema, fi_long_ema, closes)
        
        result = {
            'current_values': {
                'raw_force_index': round(float(raw_force_index[-1]), 2),
                'fi_short_ema': round(float(fi_short_ema[-1]), 2),
                'fi_long_ema': round(float(fi_long_ema[-1]), 2),
                'price_change': round(float(closes[-1] - closes[-2]), 2),
                'volume': int(volumes[-1])
            },
            'signals': signals,
            'trend_analysis': trend_analysis
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Force Index calculation failed: {str(e)}")
        return None


def _calculate_ma(data: np.ndarray, period: int) -> np.ndarray:
    """计算移动平均"""
    ma = np.zeros(len(data))
    for i in range(period - 1, len(data)):
        ma[i] = np.mean(data[i-period+1:i+1])
    return ma


def _calculate_ema(data: np.ndarray, period: int) -> np.ndarray:
    """计算指数移动平均"""
    ema = np.zeros(len(data))
    k = 2 / (period + 1)
    
    if len(data) >= period:
        ema[period-1] = np.mean(data[:period])
        for i in range(period, len(data)):
            ema[i] = data[i] * k + ema[i-1] * (1 - k)
    
    return ema


def _analyze_trend(fi_short: np.ndarray, fi_long: np.ndarray) -> Dict:
    """分析趋势"""
    try:
        current_fi13 = fi_long[-1]
        
        # 分析 FI2 趋势（最近 5 天）
        fi2_recent = fi_short[-5:]
        fi2_positive_days = sum(1 for fi in fi2_recent if fi > 0)
        
        # 判断趋势方向
        if current_fi13 > 0 and fi2_positive_days >= 3:
            trend_direction = '上涨趋势'
            trend_strength = 'strong' if fi2_positive_days >= 4 else 'moderate'
        elif current_fi13 < 0 and fi2_positive_days <= 2:
            trend_direction = '下跌趋势'
            trend_strength = 'strong' if fi2_positive_days <= 1 else 'moderate'
        else:
            trend_direction = '横盘震荡'
            trend_strength = 'weak'
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'fi13_positive': current_fi13 > 0,
            'fi2_positive_days': fi2_positive_days
        }
        
    except Exception as e:
        logger.error(f"Trend analysis failed: {str(e)}")
        return {
            'trend_direction': '未知',
            'trend_strength': 'weak'
        }


def _generate_signals(
    raw_fi: np.ndarray, 
    fi_short: np.ndarray, 
    fi_long: np.ndarray,
    closes: np.ndarray
) -> Dict:
    """生成买卖信号"""
    try:
        current_fi2 = fi_short[-1]
        current_fi13 = fi_long[-1]
        
        # 基本信号判断
        if current_fi2 > 0 and current_fi13 > 0:
            signal = '买入'
            strength = 'strong' if current_fi2 > fi_short[-2] else 'moderate'
        elif current_fi2 < 0 and current_fi13 < 0:
            signal = '卖出'
            strength = 'strong' if current_fi2 < fi_short[-2] else 'moderate'
        else:
            signal = '观望'
            strength = 'weak'
        
        return {
            'current_signal': signal,
            'signal_strength': strength,
            'fi2_positive': current_fi2 > 0,
            'fi13_positive': current_fi13 > 0
        }
        
    except Exception as e:
        logger.error(f"Signal generation failed: {str(e)}")
        return {
            'current_signal': '未知',
            'signal_strength': 'weak'
        }


def batch_calculate_indicators_mp(args_list: List[Tuple]) -> List[Dict]:
    """
    批量计算技术指标（多进程版本）
    
    Args:
        args_list: 参数列表，每个元素是 (stock_code, klines_data, pmr_days, force_index_params)
        
    Returns:
        计算结果列表
    """
    results = []
    
    for args in args_list:
        try:
            stock_code, klines_data, pmr_days, force_index_params = args
            
            result = {
                'stock_code': stock_code,
                'pmr': None,
                'force_index': None
            }
            
            # 计算 PMR
            if klines_data and len(klines_data) >= pmr_days:
                result['pmr'] = calculate_pmr_mp(klines_data)
            
            # 计算 Force Index
            if klines_data and len(klines_data) >= 18:  # 至少需要 13 + 5 条数据
                result['force_index'] = calculate_force_index_mp(
                    klines_data, 
                    force_index_params.get('ema_short', 2),
                    force_index_params.get('ema_long', 13)
                )
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Batch calculation failed for {args[0]}: {str(e)}")
            results.append({
                'stock_code': args[0],
                'pmr': None,
                'force_index': None,
                'error': str(e)
            })
    
    return results
