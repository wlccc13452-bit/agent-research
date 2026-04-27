"""
Price Alert Manager - Monitor stock prices and send alerts via Feishu
Supports simultaneous monitoring of target price and change percentages
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import PriceAlert
from database.operations import (
    create_price_alert,
    get_alerts,
    get_alert_by_id,
    get_active_alerts,
    update_alert_price,
    trigger_alert,
    delete_alert,
    deactivate_alert,
)
from services.stock_service import stock_service
from services.feishu_bot import FeishuBotService

logger = logging.getLogger(__name__)


class PriceAlertManager:
    """Price alert management service with Feishu notification"""
    
    def __init__(self) -> None:
        """Initialize manager"""
        self.bot_service = FeishuBotService()
    
    async def create_alert(
        self,
        db: AsyncSession,
        stock_code: str,
        target_price: Optional[float] = None,
        change_up_pct: Optional[float] = None,
        change_down_pct: Optional[float] = None,
        feishu_chat_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> PriceAlert:
        """
        Create a new price alert with target price and/or change percentages
        
        Args:
            db: Database session
            stock_code: Stock code
            target_price: Target price (optional)
            change_up_pct: Price up percentage (optional)
            change_down_pct: Price down percentage (optional)
            feishu_chat_id: Feishu chat ID for notifications
            notes: Additional notes
            
        Returns:
            Created alert
            
        Raises:
            ValueError: If no monitoring condition is specified
        """
        # Validate at least one condition is set
        if target_price is None and change_up_pct is None and change_down_pct is None:
            raise ValueError("至少需要设置一个监控条件（目标价格、上涨幅度或下跌幅度）")
        
        # Get current stock quote
        quote = await stock_service.get_realtime_quote(stock_code)
        if not quote:
            raise ValueError(f"未找到股票: {stock_code}")
        
        current_price = Decimal(str(quote.get("price", 0)))
        current_change_pct = Decimal(str(quote.get("change_pct", 0)))
        stock_name = quote.get("name", stock_code)
        
        # Use ops function to create alert
        alert = await create_price_alert(
            db=db,
            stock_code=stock_code,
            stock_name=stock_name,
            base_price=current_price,
            current_price=current_price,
            current_change_pct=current_change_pct,
            feishu_chat_id=feishu_chat_id or "",
            target_price=Decimal(str(target_price)) if target_price else None,
            change_up_pct=Decimal(str(change_up_pct)) if change_up_pct else None,
            change_down_pct=Decimal(str(change_down_pct)) if change_down_pct else None,
            notes=notes
        )
        
        # Build alert description
        conditions = []
        if target_price:
            conditions.append(f"目标价 {target_price:.2f}元")
        if change_up_pct:
            conditions.append(f"涨幅超 {change_up_pct:+.2f}%")
        if change_down_pct:
            conditions.append(f"跌幅超 {change_down_pct:+.2f}%")
        
        logger.info(f"Created price alert: {stock_name} ({stock_code}) - {', '.join(conditions)}")
        return alert
    
    async def get_alerts(
        self,
        db: AsyncSession,
        active_only: bool = True,
        stock_code: Optional[str] = None
    ) -> List[PriceAlert]:
        """
        Get all price alerts
        
        Args:
            db: Database session
            active_only: Only return active alerts
            stock_code: Filter by stock code
            
        Returns:
            List of alerts
        """
        return await get_alerts(db, active_only=active_only, stock_code=stock_code)
    
    async def check_alerts(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Check all active alerts and trigger notifications
        
        Args:
            db: Database session
            
        Returns:
            List of triggered alerts
        """
        # Get all active, non-triggered alerts using ops
        alerts = await get_active_alerts(db)
        
        triggered_alerts = []
        
        for alert in alerts:
            try:
                # Get current price
                quote = await stock_service.get_realtime_quote(alert.stock_code)
                if not quote:
                    continue
                
                current_price = Decimal(str(quote.get("price", 0)))
                current_change_pct = Decimal(str(quote.get("change_pct", 0)))
                
                # Update current values using ops
                await update_alert_price(db, alert.id, current_price, current_change_pct)
                
                # Check trigger conditions
                trigger_reason = None
                
                # Check target price
                if alert.target_price is not None:
                    if current_price >= alert.target_price:
                        trigger_reason = "target_price"
                    elif current_price <= alert.target_price:
                        # Check if target is below current (downside target)
                        if alert.base_price > alert.target_price:
                            trigger_reason = "target_price"
                
                # Check change up percentage
                if alert.change_up_pct is not None and trigger_reason is None:
                    if current_change_pct >= alert.change_up_pct:
                        trigger_reason = "change_up"
                
                # Check change down percentage
                if alert.change_down_pct is not None and trigger_reason is None:
                    if current_change_pct <= alert.change_down_pct:
                        trigger_reason = "change_down"
                
                # Trigger alert
                if trigger_reason:
                    # Mark as triggered using ops
                    await trigger_alert(
                        db, 
                        alert.id, 
                        trigger_reason,
                        current_price=current_price,
                        current_change_pct=current_change_pct
                    )
                    
                    # Send Feishu notification
                    if alert.feishu_chat_id:
                        await self._send_alert_notification(alert, quote, trigger_reason)
                    
                    triggered_alerts.append({
                        "alert_id": alert.id,
                        "stock_code": alert.stock_code,
                        "stock_name": alert.stock_name,
                        "trigger_reason": trigger_reason,
                        "target_price": float(alert.target_price) if alert.target_price else None,
                        "change_up_pct": float(alert.change_up_pct) if alert.change_up_pct else None,
                        "change_down_pct": float(alert.change_down_pct) if alert.change_down_pct else None,
                        "current_price": float(current_price),
                        "current_change_pct": float(current_change_pct),
                        "base_price": float(alert.base_price)
                    })
                    
                    logger.info(f"Alert triggered: {alert.stock_name} ({trigger_reason})")
                
            except Exception as e:
                logger.error(f"Error checking alert {alert.id}: {e}")
        
        await db.commit()
        return triggered_alerts
    
    async def _send_alert_notification(
        self,
        alert: PriceAlert,
        quote: Dict[str, Any],
        trigger_reason: str
    ) -> bool:
        """
        Send alert notification via Feishu
        
        Args:
            alert: Alert object
            quote: Current stock quote
            trigger_reason: Trigger reason (target_price/change_up/change_down)
            
        Returns:
            True if sent successfully
        """
        try:
            # Build trigger message
            if trigger_reason == "target_price":
                trigger_emoji = "[TARGET]"
                trigger_text = f"达到目标价 {float(alert.target_price):.2f}元"
            elif trigger_reason == "change_up":
                trigger_emoji = "📈"
                trigger_text = f"涨幅超过 {float(alert.change_up_pct):+.2f}%"
            elif trigger_reason == "change_down":
                trigger_emoji = "📉"
                trigger_text = f"跌幅超过 {float(alert.change_down_pct):+.2f}%"
            else:
                trigger_emoji = "🔔"
                trigger_text = "触发提醒"
            
            # Build monitoring conditions text
            conditions = []
            if alert.target_price:
                conditions.append(f"目标价: {float(alert.target_price):.2f}元")
            if alert.change_up_pct:
                conditions.append(f"涨幅监控: {float(alert.change_up_pct):+.2f}%")
            if alert.change_down_pct:
                conditions.append(f"跌幅监控: {float(alert.change_down_pct):+.2f}%")
            
            message = f"""{trigger_emoji} **价格提醒触发**

**股票**: {alert.stock_name} ({alert.stock_code})
**触发条件**: {trigger_text}
**当前状态**: {float(quote.get('price', 0)):.2f}元 ({float(quote.get('change_pct', 0)):+.2f}%)
**基准价格**: {float(alert.base_price):.2f}元

**监控设置**:
{chr(10).join(f"• {c}" for c in conditions)}

**触发时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            if alert.notes:
                message += f"\n**备注**: {alert.notes}"
            
            # Send message
            success = await self.bot_service.send_message(
                alert.feishu_chat_id,
                message,
                msg_type="text"
            )
            
            if success:
                logger.info(f"Alert notification sent to {alert.feishu_chat_id}")
                return True
            else:
                logger.error(f"Failed to send alert notification")
                return False
                
        except Exception as e:
            logger.error(f"Error sending alert notification: {e}", exc_info=True)
            return False
    
    async def delete_alert(
        self,
        db: AsyncSession,
        alert_id: int
    ) -> bool:
        """
        Delete a price alert
        
        Args:
            db: Database session
            alert_id: Alert ID
            
        Returns:
            True if deleted successfully
        """
        # Get alert info for logging before deletion
        alert = await get_alert_by_id(db, alert_id)
        if not alert:
            return False
        
        stock_name = alert.stock_name
        
        # Use ops function to delete
        success = await delete_alert(db, alert_id)
        
        if success:
            logger.info(f"Deleted price alert: {stock_name} (ID: {alert_id})")
        return success
    
    async def deactivate_alert_by_id(
        self,
        db: AsyncSession,
        alert_id: int
    ) -> bool:
        """
        Deactivate a price alert
        
        Args:
            db: Database session
            alert_id: Alert ID
            
        Returns:
            True if deactivated successfully
        """
        # Get alert info for logging before deactivation
        alert = await get_alert_by_id(db, alert_id)
        if not alert:
            return False
        
        stock_name = alert.stock_name
        
        # Use ops function to deactivate
        success = await deactivate_alert(db, alert_id)
        
        if success:
            logger.info(f"Deactivated price alert: {stock_name} (ID: {alert_id})")
        return success


# Global service instance
price_alert_manager = PriceAlertManager()
