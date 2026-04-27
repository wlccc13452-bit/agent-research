"""
Price Alert Routes - RESTful API endpoints
Supports simultaneous monitoring of target price and change percentages
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator
from datetime import datetime

from database import get_db
from services.price_alert_manager import price_alert_manager

router = APIRouter()


# Pydantic models
class PriceAlertCreate(BaseModel):
    """Price alert creation request"""
    stock_code: str = Field(..., description="股票代码")
    target_price: Optional[float] = Field(None, description="目标价格（可选）")
    change_up_pct: Optional[float] = Field(None, description="上涨幅度%（可选）")
    change_down_pct: Optional[float] = Field(None, description="下跌幅度%（可选）")
    feishu_chat_id: Optional[str] = Field(None, description="飞书会话ID（用于推送通知）")
    notes: Optional[str] = Field(None, description="备注")
    
    @validator('change_up_pct', 'change_down_pct')
    def validate_percentage(cls, v):
        """Validate percentage values"""
        if v is not None and (v < -100 or v > 100):
            raise ValueError('涨跌幅必须在 -100 到 100 之间')
        return v
    
    @validator('target_price')
    def validate_target_price(cls, v):
        """Validate target price"""
        if v is not None and v <= 0:
            raise ValueError('目标价格必须大于0')
        return v
    
    @validator('notes')
    def validate_at_least_one_condition(cls, v, values):
        """Validate at least one monitoring condition is set"""
        target_price = values.get('target_price')
        change_up_pct = values.get('change_up_pct')
        change_down_pct = values.get('change_down_pct')
        
        if target_price is None and change_up_pct is None and change_down_pct is None:
            raise ValueError('至少需要设置一个监控条件（目标价格、上涨幅度或下跌幅度）')
        
        return v


class PriceAlertResponse(BaseModel):
    """Price alert response"""
    id: int
    stock_code: str
    stock_name: str
    base_price: float  # 基准价格
    target_price: Optional[float]  # 目标价格
    change_up_pct: Optional[float]  # 上涨幅度%
    change_down_pct: Optional[float]  # 下跌幅度%
    current_price: float  # 当前价格
    current_change_pct: float  # 当前涨跌幅
    is_active: int  # 是否激活
    is_triggered: int  # 是否已触发
    triggered_at: Optional[datetime]  # 触发时间
    trigger_reason: Optional[str]  # 触发原因
    feishu_chat_id: Optional[str]  # 飞书会话ID
    notes: Optional[str]  # 备注
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# API endpoints
@router.get("", response_model=List[PriceAlertResponse])
async def get_alerts(
    active_only: bool = Query(True, description="仅返回激活的提醒"),
    stock_code: Optional[str] = Query(None, description="按股票代码过滤"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有价格提醒
    
    返回价格提醒列表，支持可选过滤条件。
    """
    try:
        alerts = await price_alert_manager.get_alerts(
            db,
            active_only=active_only,
            stock_code=stock_code
        )
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=PriceAlertResponse)
async def create_alert(
    alert_data: PriceAlertCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新的价格提醒
    
    同时支持目标价格和涨跌幅监控，至少需要设置一个条件。
    
    **示例**:
    ```json
    {
      "stock_code": "000001",
      "target_price": 15.0,
      "change_up_pct": 5.0,
      "change_down_pct": -3.0,
      "notes": "突破阻力位"
    }
    ```
    
    **触发逻辑**:
    - 目标价格：当前价 >= 目标价 或 当前价 <= 目标价（看跌）
    - 上涨幅度：当前涨幅 >= 设定涨幅
    - 下跌幅度：当前跌幅 >= 设定跌幅（负值）
    
    **注意**: 满足任一条件即触发提醒
    """
    try:
        alert = await price_alert_manager.create_alert(
            db,
            stock_code=alert_data.stock_code,
            target_price=alert_data.target_price,
            change_up_pct=alert_data.change_up_pct,
            change_down_pct=alert_data.change_down_pct,
            feishu_chat_id=alert_data.feishu_chat_id,
            notes=alert_data.notes
        )
        
        return alert
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check")
async def check_alerts(db: AsyncSession = Depends(get_db)):
    """
    手动触发提醒检查
    
    检查所有激活的提醒，对触发的提醒发送通知。
    """
    try:
        triggered = await price_alert_manager.check_alerts(db)
        return {
            "status": "ok",
            "triggered_count": len(triggered),
            "triggered_alerts": triggered
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除价格提醒
    
    永久删除价格提醒记录。
    """
    try:
        success = await price_alert_manager.delete_alert(db, alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="提醒不存在")
        
        return {"status": "ok", "message": f"已删除提醒 {alert_id}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{alert_id}/deactivate")
async def deactivate_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    停用价格提醒
    
    停用提醒但不删除记录，可以后续重新激活。
    """
    try:
        success = await price_alert_manager.deactivate_alert(db, alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="提醒不存在")
        
        return {"status": "ok", "message": f"已停用提醒 {alert_id}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
