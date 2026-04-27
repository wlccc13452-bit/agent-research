"""持仓管理相关模型"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class StockInfo(BaseModel):
    """股票基本信息"""
    code: str
    name: str
    sector: str
    holding_quantity: int = 0
    cost_price: float = 0.0
    target_price: Optional[float] = None  # 目标价格
    change_up_pct: Optional[float] = None  # 上涨控制比例%
    change_down_pct: Optional[float] = None  # 下跌控制比例%


class SectorInfo(BaseModel):
    """板块信息"""
    name: str
    stocks: List[StockInfo]


class Holdings(BaseModel):
    """持仓数据模型"""
    sectors: List[SectorInfo]
    last_updated: datetime


class AddStockRequest(BaseModel):
    """添加股票请求"""
    sector_name: str
    stock_name: str
    stock_code: Optional[str] = None


class RemoveStockRequest(BaseModel):
    """删除股票请求"""
    sector_name: str
    stock_name: str


class UpdateStockRequest(BaseModel):
    """更新股票请求"""
    sector_name: str
    old_name: str
    new_name: Optional[str] = None
    new_code: Optional[str] = None
    new_sector: Optional[str] = None


class UpdateStockTargetRequest(BaseModel):
    """更新股票目标价请求"""
    sector_name: str
    stock_name: str
    target_price: Optional[float] = None
    change_up_pct: Optional[float] = None
    change_down_pct: Optional[float] = None


class AddSectorRequest(BaseModel):
    """添加板块请求"""
    sector_name: str


class RenameSectorRequest(BaseModel):
    """重命名板块请求"""
    old_name: str
    new_name: str
