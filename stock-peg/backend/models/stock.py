"""股票数据相关模型"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StockQuote(BaseModel):
    """股票实时行情"""
    code: str
    name: str
    price: float
    change: float
    change_pct: float
    open: float
    high: float
    low: float
    volume: int
    amount: float
    turnover_rate: Optional[float] = None
    timestamp: datetime


class StockKLine(BaseModel):
    """K线数据"""
    code: str
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: int
    amount: float
    change_pct: Optional[float] = None
    turnover_rate: Optional[float] = None


class TechnicalIndicators(BaseModel):
    """技术指标"""
    code: str
    date: str
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    rsi: Optional[float] = None
    kdj_k: Optional[float] = None
    kdj_d: Optional[float] = None
    kdj_j: Optional[float] = None


class StockInfoResponse(BaseModel):
    """股票基本信息响应"""
    code: str
    name: str
    industry: Optional[str] = None
    sector: Optional[str] = None
    market_cap: Optional[float] = None
    total_shares: Optional[int] = None
    float_shares: Optional[int] = None
