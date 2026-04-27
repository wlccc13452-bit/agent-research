"""WebSocket路由"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json
from datetime import datetime

from services.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    await manager.connect(websocket)
    
    try:
        while True:
            # 接收消息
            try:
                data = await websocket.receive_text()
            except RuntimeError as e:
                # WebSocket连接已断开
                if "not connected" in str(e).lower():
                    logger.info("WebSocket连接已断开，退出接收循环")
                    break
                raise

            try:
                message = json.loads(data)
                action = message.get('action')
                stock_code = message.get('stock_code')

                # 处理订阅
                if action == 'subscribe' and stock_code:
                    await manager.subscribe_stock(websocket, stock_code)

                # 处理取消订阅
                elif action == 'unsubscribe' and stock_code:
                    await manager.unsubscribe_stock(websocket, stock_code)

                # 处理心跳
                elif action == 'ping':
                    await manager.send_personal_message(websocket, {
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    })

                # 处理客户端日志
                elif action == 'client_log':
                    logs = message.get('logs', [])
                    if logs:
                        await manager.client_log_handler.handle_client_logs(logs)

                else:
                    logger.warning(f"未知的WebSocket消息类型: {action}")

            except json.JSONDecodeError:
                logger.error(f"无效的JSON格式: {data}")

    except WebSocketDisconnect:
        pass  # 正常断开
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
    finally:
        manager.disconnect(websocket)
        logger.info("WebSocket连接已清理")


@router.get("/ws/connections")
async def get_websocket_connections():
    """获取WebSocket连接统计"""
    return {
        "total_connections": manager.get_connection_count(),
        "stock_subscriptions": {
            stock_code: manager.get_subscription_count(stock_code)
            for stock_code in manager.stock_subscriptions.keys()
        }
    }
