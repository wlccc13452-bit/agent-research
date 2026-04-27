"""WebSocket连接管理器"""
import logging
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
from fastapi import WebSocket
from services.log_service import log_service
from services.client_log_handler import ClientLogHandler
from config.settings import settings
from services.managed_logger import WebSocketLogger

# 使用受管理的日志器(受配置文件控制)
logger = WebSocketLogger('websocket_manager')


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储所有活跃的WebSocket连接
        self.active_connections: List[WebSocket] = []
        # 存储订阅特定股票的连接
        self.stock_subscriptions: Dict[str, Set[WebSocket]] = {}
        # 存储连接的订阅信息
        self.connection_subscriptions: Dict[WebSocket, Set[str]] = {}
        
        # 客户端日志处理器
        backend_root_dir = Path(__file__).resolve().parent.parent
        client_log_dir = backend_root_dir / "logs" / "client-loading"
        self.client_log_handler = ClientLogHandler(client_log_dir)
    
    async def start(self):
        """启动连接管理器"""
        await self.client_log_handler.start()
        logger.info("[OK] WebSocket连接管理器已启动")
    
    async def stop(self):
        """停止连接管理器"""
        await self.client_log_handler.stop()
        logger.info("[OK] WebSocket连接管理器已停止")
    
    async def connect(self, websocket: WebSocket):
        """接受新的WebSocket连接"""
        await websocket.accept()
        if websocket not in self.active_connections:
            self.active_connections.append(websocket)
        self.connection_subscriptions.setdefault(websocket, set())
        
        # 记录连接日志
        client_id = str(id(websocket))
        log_service.log_websocket_message(
            direction="INCOMING",
            message_type="CONNECT",
            client_id=client_id
        )
        
        logger.info(f"新的WebSocket连接，当前连接数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        client_id = str(id(websocket))
        
        # 记录断开连接日志
        log_service.log_websocket_message(
            direction="OUTGOING",
            message_type="DISCONNECT",
            client_id=client_id
        )
        
        # 安全移除连接（避免重复移除）
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # 清理订阅信息
        if websocket in self.connection_subscriptions:
            subscribed_stocks = list(self.connection_subscriptions.pop(websocket))
            for stock_code in subscribed_stocks:
                subscribers = self.stock_subscriptions.get(stock_code)
                if not subscribers:
                    continue
                subscribers.discard(websocket)
                if not subscribers:
                    del self.stock_subscriptions[stock_code]
        
        logger.info(f"WebSocket断开连接，当前连接数: {len(self.active_connections)}")
    
    async def subscribe_stock(self, websocket: WebSocket, stock_code: str):
        """订阅股票行情"""
        client_id = str(id(websocket))
        if websocket not in self.connection_subscriptions:
            self.connection_subscriptions[websocket] = set()
        if websocket not in self.active_connections:
            self.active_connections.append(websocket)
        
        if stock_code not in self.stock_subscriptions:
            self.stock_subscriptions[stock_code] = set()
        
        self.stock_subscriptions[stock_code].add(websocket)
        self.connection_subscriptions[websocket].add(stock_code)
        
        # 记录订阅日志
        log_service.log_websocket_message(
            direction="INCOMING",
            message_type="SUBSCRIBE",
            client_id=client_id,
            stock_code=stock_code
        )
        
        logger.info(f"WebSocket订阅股票: {stock_code}")
        
        # 发送订阅确认
        await self.send_personal_message(websocket, {
            'type': 'subscription',
            'action': 'subscribed',
            'stock_code': stock_code,
            'timestamp': datetime.now().isoformat()
        })
    
    async def unsubscribe_stock(self, websocket: WebSocket, stock_code: str):
        """取消订阅股票"""
        client_id = str(id(websocket))
        
        if stock_code in self.stock_subscriptions:
            self.stock_subscriptions[stock_code].discard(websocket)
            if not self.stock_subscriptions[stock_code]:
                del self.stock_subscriptions[stock_code]
        
        if websocket in self.connection_subscriptions:
            self.connection_subscriptions[websocket].discard(stock_code)
        
        # 记录取消订阅日志
        log_service.log_websocket_message(
            direction="INCOMING",
            message_type="UNSUBSCRIBE",
            client_id=client_id,
            stock_code=stock_code
        )
        
        logger.info(f"WebSocket取消订阅股票: {stock_code}")
        
        await self.send_personal_message(websocket, {
            'type': 'subscription',
            'action': 'unsubscribed',
            'stock_code': stock_code,
            'timestamp': datetime.now().isoformat()
        })
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """发送个人消息"""
        client_id = str(id(websocket))
        
        try:
            await websocket.send_json(message)
            
            # 记录发送消息日志
            log_service.log_websocket_message(
                direction="OUTGOING",
                message_type=message.get('type', 'UNKNOWN'),
                client_id=client_id,
                stock_code=message.get('stock_code'),
                data=message
            )
        except Exception as e:
            # 忽略连接重置错误（Windows常见）
            error_msg = str(e)
            if "10054" in error_msg or "ConnectionReset" in error_msg or "远程主机强迫关闭" in error_msg:
                logger.debug(f"WebSocket连接已重置: {client_id}")
            else:
                logger.error(f"发送消息失败: {error_msg}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                # 忽略连接重置错误
                error_msg = str(e)
                if "10054" in error_msg or "ConnectionReset" in error_msg or "远程主机强迫关闭" in error_msg:
                    logger.debug("广播时连接已重置")
                else:
                    logger.error(f"广播消息失败: {error_msg}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_stock(self, stock_code: str, message: dict):
        """向订阅特定股票的连接广播消息"""
        if stock_code not in self.stock_subscriptions:
            return
        
        # 记录广播消息日志
        log_service.log_websocket_message(
            direction="OUTGOING",
            message_type=message.get('type', 'BROADCAST'),
            stock_code=stock_code,
            data=message
        )
        
        disconnected = []
        for connection in self.stock_subscriptions[stock_code]:
            try:
                await connection.send_json(message)
            except Exception as e:
                # 忽略连接重置错误
                error_msg = str(e)
                if "10054" in error_msg or "ConnectionReset" in error_msg or "远程主机强迫关闭" in error_msg:
                    logger.debug("向股票订阅者广播时连接已重置")
                else:
                    logger.error(f"向股票订阅者广播失败: {error_msg}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_stock_quote(self, stock_code: str, quote_data: dict):
        """发送股票行情更新"""
        message = {
            'type': 'quote',
            'stock_code': stock_code,
            'data': quote_data,
            'timestamp': datetime.now().isoformat()
        }
        await self.broadcast_to_stock(stock_code, message)
    
    async def send_alert(self, stock_code: str, alert_data: dict):
        """发送预警通知"""
        message = {
            'type': 'alert',
            'stock_code': stock_code,
            'data': alert_data,
            'timestamp': datetime.now().isoformat()
        }
        # 预警消息广播给所有订阅该股票的连接
        await self.broadcast_to_stock(stock_code, message)
        # 也广播给所有连接（可选）
        # await self.broadcast(message)
    
    async def send_prediction_update(self, stock_code: str, prediction_data: dict):
        """发送预测更新"""
        message = {
            'type': 'prediction',
            'stock_code': stock_code,
            'data': prediction_data,
            'timestamp': datetime.now().isoformat()
        }
        await self.broadcast_to_stock(stock_code, message)
    
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.active_connections)
    
    def get_subscription_count(self, stock_code: str) -> int:
        """获取特定股票的订阅数"""
        if stock_code in self.stock_subscriptions:
            return len(self.stock_subscriptions[stock_code])
        return 0


# 全局连接管理器实例
manager = ConnectionManager()
