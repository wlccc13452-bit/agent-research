"""预测相关模型"""
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class PredictionResult(BaseModel):
    """预测结果"""
    stock_code: str
    stock_name: str
    prediction_date: str
    direction: str  # 上涨/下跌/震荡
    probability: float
    target_price_range: List[float]  # [low, high]
    confidence: str  # 低/中/高
    risk_level: str  # 低/中/高
    key_factors: List[Dict[str, float]]  # [{factor: weight}]
    timestamp: datetime


class SectorRotationAnalysis(BaseModel):
    """板块轮动分析"""
    date: str
    hotspot_sectors: List[str]  # 当前热点板块
    hotspot_changes: Dict[str, int]  # 板块排名变化
    money_flow: Dict[str, float]  # 板块资金流向
    next_hotspot_prediction: Optional[str]  # 预测下一个热点板块
    timestamp: datetime


class InternationalMarketAnalysis(BaseModel):
    """国际市场分析"""
    date: str
    us_market: Dict  # 美股数据
    hk_market: Dict  # 港股数据
    commodity_prices: Dict  # 大宗商品价格
    correlation: Dict[str, float]  # 相关性系数
    impact_weight: Dict[str, float]  # 影响权重
    timestamp: datetime


class ComprehensivePrediction(BaseModel):
    """综合预测"""
    stock_code: str
    stock_name: str
    prediction_date: str
    prediction: PredictionResult
    sector_rotation: Optional[SectorRotationAnalysis] = None
    international: Optional[InternationalMarketAnalysis] = None
    technical_score: float
    fundamental_score: float
    overall_score: float
    timestamp: datetime
