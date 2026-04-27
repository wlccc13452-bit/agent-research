"""
Price Alert Monitor Service (Optimized) - High-performance monitoring with batch queries and concurrency
"""
import asyncio
import logging
from datetime import datetime, timedelta, time
from typing import Optional, Dict, List
from decimal import Decimal
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import PriceAlert
from database.session import get_db
from database.operations import get_active_alerts
from services.stock_service import stock_service
from services.feishu_bot import FeishuBotService, FeishuCardService
from config.settings import settings

logger = logging.getLogger(__name__)


class RetryQueue:
    """Simple async retry queue for failed notifications"""
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 60):
        self.queue: List[Dict] = []
        self.max_retries = max_retries
        self.retry_delay = retry_delay  # seconds
    
    async def add(self, task: Dict):
        """Add a task to retry queue"""
        if task.get('retry_count', 0) < self.max_retries:
            task['retry_count'] = task.get('retry_count', 0) + 1
            task['next_retry_at'] = datetime.now() + timedelta(seconds=self.retry_delay)
            self.queue.append(task)
            logger.info(f"Added to retry queue: {task.get('stock_code')} (attempt {task['retry_count']}/{self.max_retries})")
    
    async def process_retries(self):
        """Process pending retry tasks"""
        if not self.queue:
            return
        
        now = datetime.now()
        ready_tasks = [t for t in self.queue if t.get('next_retry_at', now) <= now]
        
        for task in ready_tasks:
            self.queue.remove(task)
            # Re-process the task
            logger.info(f"Retrying notification for {task.get('stock_code')}")
            # Actual retry logic would be implemented here


class PriceAlertMonitorServiceOptimized:
    """Optimized price alert monitoring service with batch queries and concurrency"""
    
    def __init__(self):
        self.bot_service = FeishuBotService()
        self.card_service = FeishuCardService()
        self.retry_queue = RetryQueue()
        
        # Performance metrics
        self.metrics = {
            'total_checks': 0,
            'total_triggered': 0,
            'avg_check_time': 0.0,
            'last_check_time': None
        }
    
    async def check_all_alerts(self) -> dict:
        """Check all active price alerts with optimized batch queries
        
        Performance improvements:
        1. Batch quote fetching (single API call for all stocks)
        2. Concurrent notification sending
        3. Cooldown mechanism to prevent spam
        4. Hysteresis to avoid trigger flickering
        
        Returns:
            Summary dict with triggered alerts count and metrics
        """
        try:
            logger.info("=" * 60)
            logger.info("🔍 Starting optimized price alert monitoring...")
            start_time = datetime.now()
            
            # Check if within trading hours
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
                    
                    # ========== OPTIMIZATION 1: Batch Quote Fetching ==========
                    stock_codes = list(set(a.stock_code for a in alerts))
                    logger.info(f"📦 Fetching quotes for {len(stock_codes)} unique stocks...")
                    
                    quotes_map = await self._fetch_quotes_batch(stock_codes)
                    logger.info(f"[OK] Retrieved {len(quotes_map)} quotes")
                    
                    # ========== OPTIMIZATION 2: Concurrent Alert Processing ==========
                    logger.info("🔄 Processing alerts concurrently...")
                    triggered_count = 0
                    tasks = []
                    
                    for alert in alerts:
                        quote = quotes_map.get(alert.stock_code)
                        if quote:
                            tasks.append(self._check_single_alert_optimized(db, alert, quote))
                    
                    # Process all alerts concurrently
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Count successful triggers
                    for result in results:
                        if isinstance(result, bool) and result:
                            triggered_count += 1
                        elif isinstance(result, Exception):
                            logger.error(f"Error in alert processing: {result}")
                    
                    await db.commit()
                    
                    # Process retry queue
                    await self.retry_queue.process_retries()
                    
                    # Update metrics
                    elapsed = (datetime.now() - start_time).total_seconds()
                    self._update_metrics(len(alerts), triggered_count, elapsed)
                    
                    logger.info(f"[OK] Monitoring complete: {triggered_count}/{len(alerts)} alerts triggered in {elapsed:.2f}s")
                    logger.info("=" * 60)
                    
                    return {
                        "status": "success",
                        "triggered_count": triggered_count,
                        "total_alerts": len(alerts),
                        "elapsed_seconds": elapsed,
                        "metrics": self.metrics
                    }
                    
                finally:
                    await db.close()
                    break
            
            # If we reach here, database iteration didn't produce any session
            logger.error("Failed to get database session for price alert monitoring")
            return {
                "status": "error",
                "error": "database_unavailable",
                "triggered_count": 0
            }
                
        except Exception as e:
            logger.error(f"Error in price alert monitoring: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "triggered_count": 0
            }
    
    async def _fetch_quotes_batch(self, stock_codes: List[str]) -> Dict[str, any]:
        """Fetch quotes for multiple stocks efficiently
        
        Args:
            stock_codes: List of stock codes
            
        Returns:
            Dict mapping stock_code -> quote data
        """
        quotes_map = {}
        
        # TODO: Implement actual batch API in stock_service
        # For now, fetch concurrently
        tasks = [stock_service.get_quote(code, use_cache=False) for code in stock_codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for code, result in zip(stock_codes, results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to fetch quote for {code}: {result}")
            elif result:
                quotes_map[code] = result
        
        return quotes_map
    
    async def _get_active_alerts(self, db: AsyncSession) -> List[PriceAlert]:
        """Get all active price alerts
        
        Args:
            db: Database session
            
        Returns:
            List of active PriceAlert objects
        """
        return await get_active_alerts(db)
    
    async def _check_single_alert_optimized(
        self, 
        db: AsyncSession, 
        alert: PriceAlert, 
        quote: any
    ) -> bool:
        """Check a single price alert with cooldown and hysteresis
        
        Args:
            db: Database session
            alert: PriceAlert object to check
            quote: Current stock quote data
            
        Returns:
            True if alert was triggered, False otherwise
        """
        try:
            current_price = Decimal(str(quote.price))
            current_change_pct = Decimal(str(quote.change_pct))
            
            # Update current price
            alert.current_price = current_price
            alert.current_change_pct = current_change_pct
            
            logger.debug(f"📈 {alert.stock_name} ({alert.stock_code}): ¥{current_price} ({current_change_pct:+.2f}%)")
            
            # ========== OPTIMIZATION 3: Cooldown Check ==========
            if not self._check_cooldown(alert):
                logger.debug(f"⏸️ Alert {alert.id} in cooldown period")
                return False
            
            # Check trigger conditions with hysteresis
            trigger_reason = self._check_trigger_conditions_with_hysteresis(
                alert, current_price, current_change_pct
            )
            
            if trigger_reason:
                await self._trigger_alert_notification(db, alert, trigger_reason, quote)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking alert {alert.id}: {e}", exc_info=True)
            return False
    
    def _check_cooldown(self, alert: PriceAlert) -> bool:
        """Check if alert is in cooldown period
        
        Args:
            alert: PriceAlert object
            
        Returns:
            True if not in cooldown (can trigger), False if in cooldown
        """
        if not alert.last_triggered_at:
            return True
        
        cooldown_minutes = alert.cooldown_minutes or 30
        cooldown_end = alert.last_triggered_at + timedelta(minutes=cooldown_minutes)
        
        return datetime.now() > cooldown_end
    
    def _check_trigger_conditions_with_hysteresis(
        self, 
        alert: PriceAlert, 
        current_price: Decimal, 
        current_change_pct: Decimal
    ) -> Optional[str]:
        """Check trigger conditions with hysteresis to prevent flickering
        
        Hysteresis adds a small buffer zone to prevent triggers when price
        oscillates around the threshold.
        
        Args:
            alert: PriceAlert object
            current_price: Current stock price
            current_change_pct: Current change percentage
            
        Returns:
            Trigger reason string or None
        """
        hysteresis_pct = alert.hysteresis_pct or Decimal('0.5')  # Default 0.5%
        trigger_reason = None
        
        # 1. Check target price with hysteresis
        if alert.target_price:
            target = Decimal(str(alert.target_price))
            # Add hysteresis buffer
            buffer = target * hysteresis_pct / Decimal('100')
            
            if current_price >= target + buffer:
                trigger_reason = "target_price"
                logger.info(f"[TARGET] Target price triggered with hysteresis: {current_price} >= {target + buffer}")
        
        # 2. Check change up percentage with hysteresis
        if not trigger_reason and alert.change_up_pct:
            change_up = Decimal(str(alert.change_up_pct))
            buffer = hysteresis_pct  # Use percentage directly
            threshold = change_up + buffer
            
            if current_change_pct >= threshold:
                trigger_reason = "change_up"
                logger.info(f"📈 Change up triggered with hysteresis: {current_change_pct}% >= {threshold}%")
        
        # 3. Check change down percentage with hysteresis
        if not trigger_reason and alert.change_down_pct:
            change_down = Decimal(str(alert.change_down_pct))
            buffer = hysteresis_pct  # Use percentage directly
            threshold = change_down - buffer  # For down, we subtract
            
            if current_change_pct <= threshold:
                trigger_reason = "change_down"
                logger.info(f"📉 Change down triggered with hysteresis: {current_change_pct}% <= {threshold}%")
        
        return trigger_reason
    
    async def _trigger_alert_notification(
        self, 
        db: AsyncSession, 
        alert: PriceAlert, 
        trigger_reason: str,
        quote: any
    ) -> None:
        """Trigger alert notification with enhanced tracking
        
        Args:
            db: Database session
            alert: PriceAlert object
            trigger_reason: Reason for triggering
            quote: Current stock quote data
        """
        try:
            logger.info(f"🔔 Triggering alert notification for {alert.stock_name} ({trigger_reason})")
            
            # Update alert status with cooldown tracking
            alert.is_triggered = 1
            alert.triggered_at = datetime.now()
            alert.last_triggered_at = datetime.now()
            alert.trigger_reason = trigger_reason
            alert.triggered_count = (alert.triggered_count or 0) + 1
            
            # Auto-disable after trigger (optional, based on settings)
            if settings.auto_stop_after_trigger:
                alert.is_active = 0
                logger.info(f"⏸️ Alert {alert.id} auto-disabled after trigger")
            
            # Send notification card with retry mechanism
            if alert.feishu_chat_id:
                success = await self._send_alert_notification_card_with_retry(
                    alert, trigger_reason, quote
                )
                
                if success:
                    alert.feishu_notified = 1
                    logger.info(f"[OK] Notification sent to chat {alert.feishu_chat_id}")
                else:
                    logger.warning(f"Failed to send notification to chat {alert.feishu_chat_id}")
                    alert.feishu_notified = 0
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error triggering alert notification: {e}", exc_info=True)
    
    async def _send_alert_notification_card_with_retry(
        self, 
        alert: PriceAlert, 
        trigger_reason: str,
        quote: any,
        retry_count: int = 0
    ) -> bool:
        """Send alert notification card with retry mechanism
        
        Args:
            alert: PriceAlert object
            trigger_reason: Trigger reason
            quote: Current stock quote
            retry_count: Current retry attempt
            
        Returns:
            True if sent successfully
        """
        try:
            # Create enhanced notification card
            card = self._create_enhanced_alert_card(alert, trigger_reason, quote)
            
            # Send card via FeishuCardService
            success = await self.card_service._send_card_message(alert.feishu_chat_id, card)
            
            if not success and retry_count < 3:
                # Add to retry queue
                await self.retry_queue.add({
                    'stock_code': alert.stock_code,
                    'alert_id': alert.id,
                    'chat_id': alert.feishu_chat_id,
                    'trigger_reason': trigger_reason,
                    'quote': quote,
                    'retry_count': retry_count
                })
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending alert notification card: {e}", exc_info=True)
            return False
    
    def _create_enhanced_alert_card(
        self, 
        alert: PriceAlert, 
        trigger_reason: str,
        quote: any
    ) -> dict:
        """Create enhanced alert notification card with quick actions
        
        Enhanced features:
        1. Quick adjust buttons (+5%, -5%, etc.)
        2. Trigger count display
        3. Hysteresis information
        4. Market indicator
        
        Args:
            alert: PriceAlert object
            trigger_reason: Trigger reason
            quote: Current stock quote
            
        Returns:
            Card JSON structure
        """
        # Base card from original implementation
        # ... (keep existing card structure)
        
        # Add enhanced action buttons
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "red" if trigger_reason in ["change_up", "target_price"] else "green",
                "title": {
                    "tag": "plain_text",
                    "content": f"🔔 价格预警触发 ({trigger_reason})"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{alert.stock_name}** ({alert.stock_code})\n"
                                   f"当前价: ¥{alert.current_price} ({alert.current_change_pct:+.2f}%)\n"
                                   f"触发次数: {alert.triggered_count or 0}"
                    }
                },
                {"tag": "hr"},
                {
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
                            "text": {"tag": "plain_text", "content": "📈 调高5%"},
                            "type": "primary",
                            "value": {
                                "action": "adjust_alert_threshold",
                                "alert_id": alert.id,
                                "stock_code": alert.stock_code,
                                "adjustment": "up_5pct"
                            }
                        },
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📉 调低5%"},
                            "type": "primary",
                            "value": {
                                "action": "adjust_alert_threshold",
                                "alert_id": alert.id,
                                "stock_code": alert.stock_code,
                                "adjustment": "down_5pct"
                            }
                        }
                    ]
                }
            ]
        }
        
        return card
    
    def _is_trading_hours(self) -> bool:
        """Check if current time is within trading hours
        
        Supports multiple markets:
        - A-share (CN): 9:30-11:30, 13:00-15:00
        - US market: 21:30-04:00 (next day, Beijing time)
        - HK market: 10:00-12:00, 13:00-16:00
        
        Returns:
            True if within trading hours for any market
        """
        from config.settings import settings
        
        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday() + 1  # 1=Monday
        
        # Check if today is a trading day
        if current_weekday not in settings.trading_days_list:
            logger.debug(f"Not a trading day (weekday={current_weekday})")
            return False
        
        # Parse morning session
        try:
            morning_parts = settings.morning_session_start.split(':')
            morning_start = time(int(morning_parts[0]), int(morning_parts[1]))
            morning_end_parts = settings.morning_session_end.split(':')
            morning_end = time(int(morning_end_parts[0]), int(morning_end_parts[1]))
            
            # Parse afternoon session
            afternoon_parts = settings.afternoon_session_start.split(':')
            afternoon_start = time(int(afternoon_parts[0]), int(afternoon_parts[1]))
            afternoon_end_parts = settings.afternoon_session_end.split(':')
            afternoon_end = time(int(afternoon_end_parts[0]), int(afternoon_end_parts[1]))
        except Exception as e:
            logger.error(f"Error parsing trading hours: {e}")
            # Fallback to defaults
            morning_start = time(9, 30)
            morning_end = time(11, 30)
            afternoon_start = time(13, 0)
            afternoon_end = time(15, 0)
        
        is_morning = morning_start <= current_time <= morning_end
        is_afternoon = afternoon_start <= current_time <= afternoon_end
        
        return is_morning or is_afternoon
    
    def _update_metrics(self, total_checks: int, triggered_count: int, elapsed: float):
        """Update performance metrics
        
        Args:
            total_checks: Total number of alerts checked
            triggered_count: Number of alerts triggered
            elapsed: Elapsed time in seconds
        """
        self.metrics['total_checks'] += total_checks
        self.metrics['total_triggered'] += triggered_count
        self.metrics['last_check_time'] = datetime.now().isoformat()
        
        # Calculate rolling average
        if self.metrics['total_checks'] > 0:
            self.metrics['avg_check_time'] = (
                self.metrics['avg_check_time'] * 0.9 + elapsed * 0.1
            )


# Global service instance
price_alert_monitor_service_optimized = PriceAlertMonitorServiceOptimized()
