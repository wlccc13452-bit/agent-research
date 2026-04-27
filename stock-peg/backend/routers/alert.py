"""预警管理路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from services.realtime_pusher import realtime_pusher

logger = logging.getLogger(__name__)

router = APIRouter()


class SetAlertRequest(BaseModel):
    """设置预警请求"""
    stock_code: str
    threshold: float = 5.0  # 涨跌幅阈值（百分比）
    alert_type: str = 'both'  # up/down/both


@router.post("/set")
async def set_alert(request: SetAlertRequest):
    """设置预警"""
    try:
        realtime_pusher.set_alert(
            request.stock_code,
            request.threshold,
            request.alert_type
        )
        return {
            "message": f"成功设置预警",
            "stock_code": request.stock_code,
            "threshold": request.threshold,
            "alert_type": request.alert_type
        }
    except Exception as e:
        logger.error(f"设置预警失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{stock_code}")
async def remove_alert(stock_code: str):
    """移除预警"""
    try:
        realtime_pusher.remove_alert(stock_code)
        return {"message": f"成功移除预警 {stock_code}"}
    except Exception as e:
        logger.error(f"移除预警失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def get_alerts():
    """获取所有预警配置"""
    try:
        alerts = realtime_pusher.get_alerts()
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"获取预警列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
