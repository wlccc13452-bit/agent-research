"""
Price Alert Monitor Service - Monitor stock prices and trigger alerts
"""
import asyncio
import logging
from datetime import datetime, time
from typing import Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from database.operations import (
    get_active_alerts,
    update_alert_price,
    trigger_alert,
)
from services.stock_service import stock_service
from services.feishu_bot import FeishuBotService, FeishuCardService

logger = logging.getLogger(__name__)


class PriceAlertMonitorService:
    """Price alert monitoring service"""
    
    def __init__(self):
        self.bot_service = FeishuBotService()
        self.card_service = FeishuCardService()
    
    async def check_all_alerts(self) -> dict:
        """Check all active price alerts and trigger notifications
        
        Returns:
            Summary dict with triggered alerts count
        """
        try:
            logger.info("=" * 60)
            logger.info("🔍 Starting price alert monitoring...")
            start_time = datetime.now()
            
            # Check if within trading hours (A股: 9:30-11:30, 13:00-15:00)
            if not self._is_trading_hours():
                logger.info("⏸️ Outside trading hours, skipping monitoring")
                return {
                    "status": "skipped",
                    "reason": "outside_trading_hours",
                    "triggered_count": 0
                }
            
            # Get all active alerts
            async for db in get_db():
                try:
                    alerts = await self._get_active_alerts(db)
                    
                    if not alerts:
                        logger.info("No active price alerts found")
                        return {
                            "status": "success",
                            "triggered_count": 0,
                            "total_alerts": 0
                        }
                    
                    logger.info(f"[CHART] Found {len(alerts)} active alerts to check")
                    
                    # Check each alert
                    triggered_count = 0
                    for alert in alerts:
                        try:
                            is_triggered = await self._check_single_alert(db, alert)
                            if is_triggered:
                                triggered_count += 1
                        except Exception as e:
                            logger.error(f"Error checking alert {alert.id}: {e}")
                    
                    await db.commit()
                    
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"[OK] Monitoring complete: {triggered_count}/{len(alerts)} alerts triggered in {elapsed:.2f}s")
                    logger.info("=" * 60)
                    
                    return {
                        "status": "success",
                        "triggered_count": triggered_count,
                        "total_alerts": len(alerts),
                        "elapsed_seconds": elapsed
                    }
                    
                finally:
                    await db.close()
                    break
                    
        except Exception as e:
            logger.error(f"Error in price alert monitoring: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "triggered_count": 0
            }
    
    async def _get_active_alerts(self, db: AsyncSession) -> list[PriceAlert]:
        """Get all active price alerts - 使用 ops 层
        
        Args:
            db: Database session
            
        Returns:
            List of active PriceAlert objects
        """
        return await get_active_alerts(db)
    
    async def _check_single_alert(self, db: AsyncSession, alert: PriceAlert) -> bool:
        """Check a single price alert and trigger notification if conditions met
        
        Args:
            db: Database session
            alert: PriceAlert object to check
            
        Returns:
            True if alert was triggered, False otherwise
        """
        try:
            # Get current stock price
            stock_code = alert.stock_code
            quote = await stock_service.get_quote(stock_code, use_cache=False)
            
            if not quote:
                logger.warning(f"Failed to get quote for {stock_code}, skipping alert {alert.id}")
                return False
            
            current_price = Decimal(str(quote.price))
            current_change_pct = Decimal(str(quote.change_pct))
            
            # Update current price in alert using ops
            await update_alert_price(db, alert.id, current_price, current_change_pct)
            
            logger.info(f"📈 {alert.stock_name} ({stock_code}): ¥{current_price} ({current_change_pct:+.2f}%)")
            
            # Check trigger conditions
            trigger_reason = None
            
            # 1. Check target price
            if alert.target_price:
                target = Decimal(str(alert.target_price))
                if current_price >= target:
                    trigger_reason = "target_price"
                    logger.info(f"[TARGET] Target price triggered: {current_price} >= {target}")
            
            # 2. Check change up percentage
            if not trigger_reason and alert.change_up_pct:
                change_up = Decimal(str(alert.change_up_pct))
                if current_change_pct >= change_up:
                    trigger_reason = "change_up"
                    logger.info(f"📈 Change up triggered: {current_change_pct}% >= {change_up}%")
            
            # 3. Check change down percentage
            if not trigger_reason and alert.change_down_pct:
                change_down = Decimal(str(alert.change_down_pct))
                # Note: change_down_pct should be negative (e.g., -3.0)
                if current_change_pct <= change_down:
                    trigger_reason = "change_down"
                    logger.info(f"📉 Change down triggered: {current_change_pct}% <= {change_down}%")
            
            # Trigger notification if conditions met
            if trigger_reason:
                await self._trigger_alert_notification(db, alert, trigger_reason, quote)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking alert {alert.id}: {e}", exc_info=True)
            return False
    
    async def _trigger_alert_notification(
        self, 
        db: AsyncSession, 
        alert: PriceAlert, 
        trigger_reason: str,
        quote: dict
    ) -> None:
        """Trigger alert notification and update alert status - 使用 ops 层
        
        Args:
            db: Database session
            alert: PriceAlert object
            trigger_reason: Reason for triggering (target_price/change_up/change_down)
            quote: Current stock quote data
        """
        try:
            logger.info(f"🔔 Triggering alert notification for {alert.stock_name} ({trigger_reason})")
            
            # Update alert status using ops
            await trigger_alert(db, alert.id, trigger_reason)
            
            # Send notification card
            feishu_notified = 0
            if alert.feishu_chat_id:
                success = await self._send_alert_notification_card(alert, trigger_reason, quote)
                
                if success:
                    logger.info(f"[OK] Notification sent to chat {alert.feishu_chat_id}")
                    feishu_notified = 1
                else:
                    logger.warning(f"Failed to send notification to chat {alert.feishu_chat_id}")
            
            # Note: trigger_alert() already commits
            # If we need to update feishu_notified, we would need additional ops function
            
        except Exception as e:
            logger.error(f"Error triggering alert notification: {e}", exc_info=True)
    
    async def _send_alert_notification_card(
        self, 
        alert: PriceAlert, 
        trigger_reason: str,
        quote: dict
    ) -> bool:
        """Send alert notification card to Feishu
        
        Args:
            alert: PriceAlert object
            trigger_reason: Trigger reason
            quote: Current stock quote
            
        Returns:
            True if sent successfully
        """
        try:
            # Create notification card
            card = self._create_alert_notification_card(alert, trigger_reason, quote)
            
            # Send card via FeishuCardService
            success = await self.card_service._send_card_message(alert.feishu_chat_id, card)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending alert notification card: {e}", exc_info=True)
            return False
    
    def _create_alert_notification_card(
        self, 
        alert: PriceAlert, 
        trigger_reason: str,
        quote: dict
    ) -> dict:
        """Create alert notification card with enhanced price comparison
        
        增强版预警卡片，包含：
        - 参考价 vs 实际价对比
        - 动态颜色（上涨=red，下跌=green）
        - 详细的价格变化信息
        
        Args:
            alert: PriceAlert object
            trigger_reason: Trigger reason
            quote: Current stock quote
            
        Returns:
            Card JSON structure
        """
        # Calculate price change
        price_change = float(alert.current_price) - float(alert.base_price)
        price_change_pct = (price_change / float(alert.base_price) * 100) if float(alert.base_price) > 0 else 0
        
        # Determine dynamic color based on trigger reason
        if trigger_reason == "change_up":
            header_color = "red"  # 上涨用红色
            emoji = "📈"
            title = "涨幅预警"
            trigger_text = f"涨幅已达到 {float(alert.change_up_pct):+.2f}%"
        elif trigger_reason == "change_down":
            header_color = "green"  # 下跌用绿色
            emoji = "📉"
            title = "跌幅预警"
            trigger_text = f"跌幅已达到 {float(alert.change_down_pct):+.2f}%"
        elif trigger_reason == "target_price":
            # Target price reached - color based on price direction
            if alert.target_price > alert.base_price:
                header_color = "red"  # Target is above base (upside)
                emoji = "[TARGET]"
                title = "目标价达成（上涨）"
            else:
                header_color = "green"  # Target is below base (downside)
                emoji = "[TARGET]"
                title = "目标价达成（下跌）"
            trigger_text = f"股价已达到目标价 ¥{alert.target_price}"
        else:
            header_color = "blue"
            emoji = "🔔"
            title = "价格提醒"
            trigger_text = "监控条件已触发"
        
        # Determine price change indicator
        if price_change > 0:
            change_emoji = "📈"
            change_color = "red"
        elif price_change < 0:
            change_emoji = "📉"
            change_color = "green"
        else:
            change_emoji = "➡️"
            change_color = "grey"
        
        # Build card
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": header_color,
                "title": {
                    "tag": "plain_text",
                    "content": f"{emoji} {title}"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{alert.stock_name}** ({alert.stock_code})"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**[CHART] 价格对比**: [基准价: ¥{alert.base_price}] → [实际价: ¥{alert.current_price}] | 变化: {change_emoji} {price_change:+.2f}元 ({price_change_pct:+.2f}%)"
                    }
                },
                {"tag": "hr"}
            ]
        }
        
        # Add reference price if available (for user-set reference price)
        if alert.target_price and trigger_reason != "target_price":
            ref_price_diff = float(alert.current_price) - float(alert.target_price)
            ref_price_diff_pct = (ref_price_diff / float(alert.target_price) * 100) if float(alert.target_price) > 0 else 0
            
            ref_element = {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**[TARGET] 参考价格**: ¥{alert.target_price} (偏差: {ref_price_diff:+.2f}元 / {ref_price_diff_pct:+.2f}%)"
                }
            }
            card["elements"].insert(3, ref_element)
        
        # Add current status
        status_element = {
            "tag": "column_set",
            "columns": [
                {
                    "tag": "column",
                    "width": "weighted",
                    "weight": 1,
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": f"**当前涨跌幅**\n{emoji} {float(alert.current_change_pct):+.2f}%"
                            }
                        }
                    ]
                },
                {
                    "tag": "column",
                    "width": "weighted",
                    "weight": 1,
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": f"**触发条件**\n{trigger_text}"
                            }
                        }
                    ]
                }
            ]
        }
        card["elements"].append(status_element)
        
        # Add monitoring thresholds
        thresholds = []
        if alert.change_up_pct:
            thresholds.append(f"📈 上涨预警: +{float(alert.change_up_pct):.2f}%")
        if alert.change_down_pct:
            thresholds.append(f"📉 下跌预警: {float(alert.change_down_pct):.2f}%")
        
        if thresholds:
            thresholds_element = {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**监控阈值**: {' | '.join(thresholds)}"
                }
            }
            card["elements"].append(thresholds_element)
        
        # Add notes if available
        if alert.notes:
            notes_element = {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**备注**: {alert.notes}"
                }
            }
            card["elements"].append(notes_element)
        
        # Add timestamp
        note_element = {
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": f"🕐 触发时间: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        }
        card["elements"].append(note_element)
        
        # Add interactive buttons for alert management
        action_element = {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "⏸️ 停止监控"},
                    "type": "default",
                    "value": {
                        "action": "stop_alert_monitoring",
                        "alert_id": alert.id
                    }
                },
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "[FIX] 修改阈值"},
                    "type": "primary",
                    "value": {
                        "action": "modify_alert_threshold",
                        "alert_id": alert.id,
                        "stock_code": alert.stock_code
                    }
                }
            ]
        }
        card["elements"].append(action_element)
        
        return card
    
    def _is_trading_hours(self) -> bool:
        """Check if current time is within trading hours
        
        Uses dynamic configuration from settings (trading_hours.ini)
        
        Returns:
            True if within trading hours
        """
        from config.settings import settings
        
        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday() + 1  # Python weekday: 0=Monday, convert to 1=Monday
        
        # Check if today is a trading day
        if current_weekday not in settings.trading_days_list:
            logger.debug(f"Today is not a trading day (weekday={current_weekday})")
            return False
        
        # Parse morning session times
        try:
            morning_start_parts = settings.morning_session_start.split(':')
            morning_end_parts = settings.morning_session_end.split(':')
            morning_start = time(int(morning_start_parts[0]), int(morning_start_parts[1]))
            morning_end = time(int(morning_end_parts[0]), int(morning_end_parts[1]))
            
            # Parse afternoon session times
            afternoon_start_parts = settings.afternoon_session_start.split(':')
            afternoon_end_parts = settings.afternoon_session_end.split(':')
            afternoon_start = time(int(afternoon_start_parts[0]), int(afternoon_start_parts[1]))
            afternoon_end = time(int(afternoon_end_parts[0]), int(afternoon_end_parts[1]))
        except Exception as e:
            logger.error(f"Error parsing trading hours config: {e}, using defaults")
            # Fallback to default A-share hours
            morning_start = time(9, 30)
            morning_end = time(11, 30)
            afternoon_start = time(13, 0)
            afternoon_end = time(15, 0)
        
        is_morning = morning_start <= current_time <= morning_end
        is_afternoon = afternoon_start <= current_time <= afternoon_end
        
        logger.debug(
            f"Trading hours check: "
            f"morning={morning_start}-{morning_end}, "
            f"afternoon={afternoon_start}-{afternoon_end}, "
            f"current={current_time}, "
            f"in_morning={is_morning}, in_afternoon={is_afternoon}"
        )
        
        return is_morning or is_afternoon


# Global service instance
price_alert_monitor_service = PriceAlertMonitorService()
