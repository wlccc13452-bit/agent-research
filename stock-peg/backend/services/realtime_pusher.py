"""实时行情推送服务"""
import logging
import asyncio
from datetime import datetime, time
from typing import Dict, List, Optional
import json

from services.websocket_manager import manager
from services.stock_service import StockService
from routers.holding import holding_manager  # 使用全局单例
from config.settings import settings

logger = logging.getLogger(__name__)


class RealtimeQuotePusher:
    """实时行情推送服务"""
    
    def __init__(self):
        self.stock_service = StockService()
        # 使用全局单例，而不是创建新实例
        # self.holding_manager = holding_manager  # 已经在导入时使用
        self.is_running = False
        self.push_task = None
        
        # 预警配置
        self.alert_config: Dict[str, Dict] = {}  # {stock_code: {threshold: 5.0, type: 'up'}}
        
        # 上一次的行情数据（用于检测变化）
        self.last_quotes: Dict[str, Dict] = {}
    
    async def start(self):
        """启动实时推送"""
        if self.is_running:
            logger.warning("实时行情推送已在运行")
            return
        
        self.is_running = True
        self.push_task = asyncio.create_task(self._push_loop())
        logger.info("实时行情推送服务已启动")
    
    async def stop(self):
        """停止实时推送"""
        self.is_running = False
        if self.push_task:
            self.push_task.cancel()
            try:
                await self.push_task
            except asyncio.CancelledError:
                pass
        logger.info("实时行情推送服务已停止")
    
    async def _push_loop(self):
        """推送循环"""
        while self.is_running:
            try:
                # 只在交易时间推送（9:30-15:00）
                now = datetime.now()
                current_time = now.time()
                
                # 判断是否在交易时间
                is_trading_time = (
                    (time(9, 30) <= current_time <= time(11, 30)) or
                    (time(13, 0) <= current_time <= time(15, 0))
                )
                
                if is_trading_time and now.weekday() < 5:  # 周一到周五
                    await self._push_quotes()
                
                # 每5秒推送一次
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"推送循环错误: {str(e)}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _push_quotes(self):
        """推送行情数据"""
        try:
            # 加载持仓数据（使用全局单例）
            holdings = await holding_manager.load_holdings()
            
            # 收集所有股票代码
            stock_codes = []
            for sector in holdings.sectors:
                for stock in sector.stocks:
                    stock_codes.append(stock.code)
            
            if not stock_codes:
                return
            
            # 获取实时行情
            quotes = await self.stock_service.get_quotes(stock_codes)
            
            # 推送每只股票的行情
            for quote in quotes:
                quote_data = {
                    'code': quote.code,
                    'name': quote.name,
                    'price': quote.price,
                    'change': quote.change,
                    'change_pct': quote.change_pct,
                    'open': quote.open,
                    'high': quote.high,
                    'low': quote.low,
                    'volume': quote.volume,
                    'amount': quote.amount,
                    'turnover_rate': quote.turnover_rate,
                    'timestamp': quote.timestamp.isoformat()
                }
                
                # 检查预警
                await self._check_alert(quote.code, quote_data)
                
                # 推送行情
                await manager.send_stock_quote(quote.code, quote_data)
                
                # 更新上次行情
                self.last_quotes[quote.code] = quote_data

            timestamp = datetime.now().isoformat()
            await manager.broadcast({
                'type': 'market_data_updated',
                'data': {
                    'quote_count': len(quotes)
                },
                'timestamp': timestamp
            })
            await manager.broadcast({
                'type': 'market_sentiment_updated',
                'data': {
                    'quote_count': len(quotes)
                },
                'timestamp': timestamp
            })
            
            logger.debug(f"已推送 {len(quotes)} 只股票的行情")
            
        except Exception as e:
            logger.error(f"推送行情失败: {str(e)}", exc_info=True)
    
    async def _check_alert(self, stock_code: str, quote_data: Dict):
        """检查预警"""
        if stock_code not in self.alert_config:
            return
        
        config = self.alert_config[stock_code]
        threshold = config.get('threshold', 5.0)
        alert_type = config.get('type', 'both')  # up/down/both
        
        change_pct = quote_data.get('change_pct', 0)
        
        # 检查是否触发预警
        is_alert = False
        alert_message = ""
        
        if alert_type in ['up', 'both'] and change_pct >= threshold:
            is_alert = True
            alert_message = f"股票 {quote_data['name']} 涨幅达到 {change_pct:.2f}%，超过阈值 {threshold}%"
        
        elif alert_type in ['down', 'both'] and change_pct <= -threshold:
            is_alert = True
            alert_message = f"股票 {quote_data['name']} 跌幅达到 {abs(change_pct):.2f}%，超过阈值 {threshold}%"
        
        if is_alert:
            # 发送预警通知
            alert_data = {
                'stock_code': stock_code,
                'stock_name': quote_data['name'],
                'threshold': threshold,
                'alert_type': alert_type,
                'change_pct': change_pct,
                'price': quote_data['price'],
                'message': alert_message,
                'level': 'warning' if abs(change_pct) < threshold * 1.5 else 'danger'
            }
            
            await manager.send_alert(stock_code, alert_data)
            logger.info(f"触发预警: {alert_message}")
    
    def set_alert(self, stock_code: str, threshold: float, alert_type: str = 'both'):
        """设置预警"""
        self.alert_config[stock_code] = {
            'threshold': threshold,
            'type': alert_type
        }
        logger.info(f"设置预警: {stock_code} 阈值 {threshold}% 类型 {alert_type}")
    
    def remove_alert(self, stock_code: str):
        """移除预警"""
        if stock_code in self.alert_config:
            del self.alert_config[stock_code]
            logger.info(f"移除预警: {stock_code}")
    
    def get_alerts(self) -> Dict:
        """获取所有预警配置"""
        return self.alert_config.copy()

    async def broadcast(self, message: Dict):
        """广播消息给所有WebSocket连接"""
        await manager.broadcast(message)


# 全局实时推送实例
realtime_pusher = RealtimeQuotePusher()
