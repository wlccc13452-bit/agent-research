"""
Feishu Bot Router - Handle Feishu webhook events
"""
import json
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from config.constants import (
    CardAction,
    CARD_QUERY_ACTIONS,
    CARD_FORM_ACTIONS,
    CARD_DELETE_ACTIONS,
    CARD_MENU_ACTION_TO_METHOD,
    CARD_ACTION_RUNTIME_MAP,
    validate_card_action_payload,
)
from database.session import get_db
from database.operations import (
    get_latest_chat_id,
    get_messages_in_time_range,
)
from services.bot_chat_logger import bot_chat_logger
from services.feishu_bot import FeishuBotService
from services.feishu_bot.feishu_bot_dependency_setup import get_injector
from services.websocket_manager import manager
from feishu_sdk.state.card_utils import build_action_fingerprint, is_duplicate_action_persistent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feishu", tags=["feishu"])

# Global bot service instance
_bot_service: FeishuBotService | None = None


def get_bot_service() -> Any:
    """Get or create FeishuBotService instance with SDK client injected"""
    global _bot_service
    if _bot_service is None:
        _bot_service = FeishuBotService()
        
        # Inject SDK client from long connection service
        from feishu_sdk.config.config import FeishuConfig
        from feishu_sdk.core.client import FeishuClient
        
        # Create config and client
        config = FeishuConfig(
            app_id=settings.feishu_app_id or "",
            app_secret=settings.feishu_app_secret or ""
        )
        client = FeishuClient(config)
        
        # Inject into bot service
        _bot_service.set_sdk_client(client)
        logger.info("[ROUTER] SDK client injected into FeishuBotService")
        
    return _bot_service


def get_card_service() -> Any:
    """Get card service from dependency injection"""
    return get_injector().card_service


class FeishuEvent(BaseModel):
    """Feishu event model"""
    schema_version: str = "2.0"
    header: dict[str, Any]
    event: dict[str, Any]


class FeishuChallenge(BaseModel):
    """Feishu URL verification challenge"""
    challenge: str
    token: str
    type: str


class SendRecentChatRequest(BaseModel):
    message: str


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    bot_service: Any = Depends(get_bot_service),
    x_lark_request_timestamp: str = Header(None, alias="X-Lark-Request-Timestamp"),
    x_lark_request_nonce: str = Header(None, alias="X-Lark-Request-Nonce"),
    x_lark_signature: str = Header(None, alias="X-Lark-Signature"),
) -> dict[str, str]:
    """
    Handle Feishu webhook events

    Args:
        request: FastAPI request
        background_tasks: Background tasks
        bot_service: Feishu bot service
        x_lark_request_timestamp: Request timestamp
        x_lark_request_nonce: Request nonce
        x_lark_signature: Request signature

    Returns:
        Response dict
    """
    # Get request body
    body = await request.body()
    body_str = body.decode("utf-8")

    # Verify signature (MANDATORY for security)
    if not (x_lark_signature and x_lark_request_timestamp and x_lark_request_nonce):
        logger.error("Missing required signature headers")
        raise HTTPException(status_code=401, detail="Missing signature headers")
    
    if not bot_service.verify_signature(
        x_lark_request_timestamp, x_lark_request_nonce, body_str, x_lark_signature
    ):
        logger.warning("Invalid webhook signature - potential security threat")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse event
    try:
        event_data = json.loads(body_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Handle URL verification challenge
    if event_data.get("type") == "url_verification":
        challenge = event_data.get("challenge", "")
        logger.info(f"URL verification challenge: {challenge}")
        return {"challenge": challenge}

    # Handle message event
    event_type = event_data.get("header", {}).get("event_type")
    
    logger.info(f"[WEBHOOK] Received event type: {event_type}")

    if event_type == "im.message.receive_v1":
        # Process message directly (not in background to ensure it runs)
        logger.info("[WEBHOOK] Processing message event...")
        try:
            await process_message_event(bot_service, event_data)
            logger.info("[WEBHOOK] Message processed successfully")
        except Exception as e:
            logger.error(f"[WEBHOOK] Error processing message: {e}", exc_info=True)
        return {"status": "ok"}
    
    # Handle card callback event
    elif event_type == "card.callback.trigger":
        logger.info("[WEBHOOK] Processing card callback event...")
        try:
            await process_card_callback_event(event_data)
            logger.info("[WEBHOOK] Card callback processed successfully")
        except Exception as e:
            logger.error(f"[WEBHOOK] Error processing card callback: {e}", exc_info=True)
        return {"status": "ok"}

    logger.warning(f"Unknown event type: {event_type}")
    return {"status": "ignored"}


async def process_message_event(bot_service: Any, event_data: dict[str, Any]) -> None:
    """
    Process received message event

    Args:
        bot_service: Feishu bot service
        event_data: Event data dict
    """
    logger.info("[PROCESS] process_message_event STARTED")
    
    try:
        from services.feishu_bot import save_chat_message
        from services.bot_chat_logger import bot_chat_logger
        from datetime import datetime
        
        logger.info("[PROCESS] Parsing event data...")
        event = event_data.get("event", {})
        message = event.get("message", {})
        content = json.loads(message.get("content", "{}"))
        sender = event.get("sender", {})
        sender_id = sender.get("sender_id", {}).get("user_id", "")

        # Get message text
        text = content.get("text", "").strip()
        chat_id = message.get("chat_id", "")
        message_id = message.get("message_id", "")
        create_time_str = message.get("create_time", "0")
        
        logger.info(f"[PROCESS] Message parsed: sender={sender_id}, text={text}, chat_id={chat_id}")
        
        # Convert timestamp to datetime (handle string type from Feishu)
        try:
            create_time = int(create_time_str) if create_time_str else 0
            send_time = datetime.fromtimestamp(create_time / 1000) if create_time else datetime.now()
        except (ValueError, TypeError):
            logger.warning(f"[PROCESS] Invalid create_time: {create_time_str}, using current time")
            send_time = datetime.now()

        logger.info("[PROCESS] Saving user message to database...")
        
        # Log user message to file
        bot_chat_logger.log_message(
            message_id=message_id,
            sender_type="user",
            sender_id=sender_id,
            content=text,
            chat_id=chat_id
        )
        
        # Save user message to database
        save_chat_message(
            chat_id=chat_id,
            message_id=message_id,
            sender_id=sender_id,
            sender_name=sender.get("sender_id", {}).get("open_id", sender_id),
            sender_type="user",
            content=text,
            send_time=send_time,
            message_type=message.get("message_type", "text"),
        )
        
        logger.info("[PROCESS] User message saved to database")
        
        # Check for activation command (hello/hi)
        if text.lower() in ["hello", "hi"]:
            logger.info(f"[PROCESS] Activation command detected: {text}")
            try:
                # Send STOCK_RESEARCH_START card
                card_service = get_card_service()
                success = await card_service.send_stock_research_start_card(chat_id)
                if success:
                    logger.info(f"[PROCESS] STOCK_RESEARCH_START card sent successfully to chat_id: {chat_id}")
                else:
                    logger.warning(f"[PROCESS] Failed to send STOCK_RESEARCH_START card to chat_id: {chat_id}")
            except Exception as card_error:
                logger.error(f"[PROCESS] Error sending STOCK_RESEARCH_START card: {card_error}", exc_info=True)
            return  # Exit early after sending activation card
        
        # Broadcast user message via WebSocket
        connection_count = manager.get_connection_count()
        logger.info(f"[WEBSOCKET] Broadcasting user message to {connection_count} connections")
        
        broadcast_data = {
            "type": "feishu-chat-message",
            "data": {
                "chat_id": chat_id,
                "message_id": message_id,
                "sender_id": sender_id,
                "sender_type": "user",
                "content": text,
                "send_time": send_time.isoformat()
            }
        }
        
        try:
            await manager.broadcast(broadcast_data)
            logger.info(f"[WEBSOCKET] User message broadcast complete to {connection_count} connections")
        except Exception as broadcast_error:
            logger.error(f"[WEBSOCKET] Broadcast failed: {broadcast_error}", exc_info=True)

        # Parse command
        logger.info(f"[PROCESS] Parsing command: {text}")
        command = bot_service.parse_command(text)

        if not command:
            # Not a command, ignore
            logger.info("[PROCESS] Not a command, returning early")
            return

        logger.info(f"[PROCESS] Command parsed: {command}")
        
        # Handle command
        response = await bot_service.handle_command(command, sender_id)
        logger.info(f"[PROCESS] Command handled, response: {response[:50]}...")

        # Send response and log
        success = await bot_service.send_message(chat_id, response)
        logger.info(f"[PROCESS] Bot message sent: success={success}")
        
        # Log bot response
        if success:
            from services.bot_chat_logger import bot_chat_logger
            bot_chat_logger.log_message(
                message_id=f"bot_{message_id}",
                sender_type="bot",
                sender_id="bot",
                content=response,
                chat_id=chat_id
            )
            bot_chat_logger.log_command(
                command=text,
                result="success",
                sender_id=sender_id
            )
            logger.info("[PROCESS] Bot response logged")

    except Exception as e:
        logger.error(f"[ERROR] Error processing message event: {e}", exc_info=True)
        
        # Log error
        from services.bot_chat_logger import bot_chat_logger
        bot_chat_logger.log_error(
            error_msg=str(e),
            context={"event_data": event_data}
        )
    
    logger.info("[PROCESS] process_message_event COMPLETED")


async def process_card_callback_event(event_data: dict[str, Any]) -> None:
    """
    Process card callback event
    
    Args:
        event_data: Event data dict
    """
    logger.info("[CARD] Processing card callback event...")
    injector = get_injector()
    card_service = injector.card_service
    business_service = injector.business_service
    try:
        event = event_data.get("event", {})
        action = event.get("action", {}) if isinstance(event.get("action", {}), dict) else {}
        action_value = action.get("value", {}) if isinstance(action.get("value", {}), dict) else {}
        form_data = action.get("form_data", {}) if isinstance(action.get("form_data", {}), dict) else {}
        if not form_data:
            form_data = action.get("form_value", {}) if isinstance(action.get("form_value", {}), dict) else {}
        context = event.get("context", {}) if isinstance(event.get("context", {}), dict) else {}
        operator = event.get("operator", {}) if isinstance(event.get("operator", {}), dict) else {}
        chat_id = context.get("open_chat_id") or context.get("chat_id") or event.get("chat_id", "")
        user_id = context.get("open_id") or operator.get("open_id") or operator.get("user_id", "")
        message_id = context.get("open_message_id") or context.get("message_id")
        action_type = str(action_value.get("action") or CardAction.QUERY_STOCK)
        if "," in action_type:
            action_type = action_type.split(",")[0].strip()
        action_type = CARD_ACTION_RUNTIME_MAP.get(action_type, action_type)
        if action_type == CardAction.QUERY_STOCK_FROM_SELECT and not form_data.get("selected_stock"):
            selected_stock = action_value.get("selected_stock")
            if isinstance(selected_stock, str):
                form_data["selected_stock"] = selected_stock
            else:
                option = action.get("option", {}) if isinstance(action.get("option", {}), dict) else {}
                option_value = option.get("value")
                if isinstance(option_value, str):
                    form_data["selected_stock"] = option_value
                elif isinstance(option_value, dict):
                    selected_value = option_value.get("value") or option_value.get("key")
                    if isinstance(selected_value, str):
                        form_data["selected_stock"] = selected_value
        if action_type == CardAction.QUERY_PRICE:
            has_stock_code = bool(
                str(form_data.get("stock_code", "")).strip()
                or str(action_value.get("stock_code", "")).strip()
            )
            if not has_stock_code:
                action_type = CardAction.PRICE_QUERY_MENU
        logger.info(f"[CARD] Callback: action={action_type}, chat_id={chat_id}, user={user_id}")
        is_valid, validation_error = validate_card_action_payload(action_type, action_value, form_data)
        if not is_valid:
            logger.info(f"[CARD_AUDIT] action={action_type} valid=false duplicate=false reason={validation_error}")
            logger.warning(f"[CARD] Invalid callback payload: {validation_error}")
            await card_service.send_action_error_card(chat_id, action_type, validation_error)
            return
        fingerprint = build_action_fingerprint(chat_id, user_id, action_type, action_value, form_data)
        duplicate = is_duplicate_action_persistent(fingerprint, window_seconds=3.0)
        logger.info(f"[CARD_AUDIT] action={action_type} valid=true duplicate={str(duplicate).lower()}")
        if duplicate:
            await card_service.send_action_error_card(chat_id, action_type, "检测到重复提交，请稍后再试")
            return
        
        if action_type in CARD_QUERY_ACTIONS:
            stock_code = ""
            if action_type == CardAction.QUERY_STOCK_FROM_SELECT:
                selected_stock = form_data.get("selected_stock", "")
                if selected_stock and "|" in selected_stock:
                    stock_code = selected_stock.split("|")[0]
            else:
                stock_code = form_data.get("stock_code", "") or action_value.get("stock_code", "")
            await card_service.handle_card_callback(
                chat_id=chat_id,
                user_id=user_id,
                action=action_type,
                stock_code=stock_code
            )
            return
        
        if action_type in CARD_FORM_ACTIONS:
            await business_service.handle_form_submission(
                chat_id=chat_id,
                user_id=user_id,
                action=action_type,
                form_data=form_data,
                message_id=message_id
            )
            return
        
        if action_type in CARD_DELETE_ACTIONS:
            await business_service.handle_delete_action(action_type, chat_id, action_value)
            return
        
        method_name = CARD_MENU_ACTION_TO_METHOD.get(action_type)
        if method_name and hasattr(card_service, method_name):
            method = getattr(card_service, method_name)
            await method(chat_id)
            return
        
        logger.warning(f"[CARD] Unknown action type: {action_type}")
        await card_service.send_main_menu_card(chat_id)
    except Exception as e:
        logger.error(f"[CARD] Error processing card callback: {e}", exc_info=True)


@router.get("/test")
async def test_feishu_connection(
    bot_service: Any = Depends(get_bot_service),
) -> dict[str, str]:
    """
    Test Feishu bot connection

    Returns:
        Connection status
    """
    try:
        # Test bot service initialization
        if bot_service.client:
            return {
                "status": "ok",
                "message": "Feishu bot initialized successfully",
                "app_id": str(getattr(getattr(bot_service.client, "config", None), "app_id", ""))[:10] + "...",
            }
        else:
            return {"status": "error", "message": "Feishu bot not initialized"}
    except Exception as e:
        logger.error(f"Error testing Feishu connection: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/sdk-status")
async def get_sdk_status(
    bot_service: Any = Depends(get_bot_service)
) -> dict:
    """
    检查SDK客户端状态
    """
    has_sdk_client = hasattr(bot_service, '_sdk_client') and bot_service._sdk_client is not None
    has_config = hasattr(bot_service, '_sdk_client') and hasattr(bot_service._sdk_client, 'config') if has_sdk_client else False
    is_configured = bot_service._sdk_client.config.is_configured if has_config else False
    
    return {
        "has_sdk_client": has_sdk_client,
        "has_config": has_config,
        "is_configured": is_configured,
        "app_id": settings.feishu_app_id[:20] + "..." if settings.feishu_app_id else None,
        "app_secret_set": bool(settings.feishu_app_secret),
    }


@router.get("/websocket-status")
async def get_websocket_status() -> dict:
    """
    Get WebSocket connection status
    
    Returns:
        WebSocket connection info
    """
    return {
        "active_connections": manager.get_connection_count(),
        "stock_subscriptions": len(manager.stock_subscriptions),
        "status": "ok"
    }


@router.get("/feishu-diagnosis")
async def feishu_diagnosis(
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    飞书配置诊断接口
    
    Returns:
        飞书配置状态和诊断信息
    """
    from database.operations import get_latest_chat_id
    
    # 检查配置
    app_id_configured = bool(settings.feishu_app_id)
    app_secret_configured = bool(settings.feishu_app_secret)
    
    # 检查chat_id
    latest_chat_id = await get_latest_chat_id(db)
    
    # 检查chat_id类型
    chat_id_type = "unknown"
    if latest_chat_id:
        if latest_chat_id.startswith("ou_"):
            chat_id_type = "open_id (用户ID，不是chat_id)"
        elif latest_chat_id.startswith("oc_"):
            chat_id_type = "chat_id (正确)"
        elif latest_chat_id.startswith("on_"):
            chat_id_type = "union_id"
    
    # 检查recent logs
    recent_logs = bot_chat_logger.get_recent_logs(limit=5)
    
    suggestions = []
    if not (app_id_configured and app_secret_configured):
        suggestions.append("配置缺失")
        suggestions.append("请确保飞书应用已创建并获取app_id和app_secret")
    elif not latest_chat_id:
        suggestions.append("无可用会话")
        suggestions.append("请在飞书中给机器人发送一条消息")
    elif chat_id_type == "open_id (用户ID，不是chat_id)":
        suggestions.append("⚠️ 检测到错误：数据库中存储的是用户open_id而不是chat_id")
        suggestions.append("解决方法：")
        suggestions.append("1. 访问 /api/feishu-chat/clear 清除旧的错误数据")
        suggestions.append("2. 在飞书App中给机器人发送一条消息（如'测试'）")
        suggestions.append("3. 这会创建正确的chat_id（oc_开头）")
    
    return {
        "status": "ok",
        "config": {
            "app_id": settings.feishu_app_id[:20] + "..." if settings.feishu_app_id else None,
            "app_id_configured": app_id_configured,
            "app_secret_configured": app_secret_configured,
        },
        "chat": {
            "latest_chat_id": latest_chat_id,
            "chat_id_type": chat_id_type,
            "has_valid_chat": bool(latest_chat_id) and latest_chat_id.startswith("oc_"),
        },
        "logs": {
            "recent_count": len(recent_logs),
            "recent_chat_ids": [log.get("chat_id") for log in recent_logs[:3] if log.get("chat_id")]
        },
        "suggestions": suggestions
    }


@router.get("/long-connection-status")
async def get_long_connection_status() -> dict:
    """
    Get Feishu long connection service status
    
    Returns:
        Long connection service info
    """
    from services.feishu_bot import feishu_long_connection_service
    from feishu_sdk.connection.websocket_service import LARK_AVAILABLE
    
    return {
        "lark_sdk_available": LARK_AVAILABLE,
        "enabled": getattr(feishu_long_connection_service, "_running", False),
        "running": getattr(feishu_long_connection_service, "_running", False),
        "loop_set": getattr(feishu_long_connection_service, "_main_loop", None) is not None,
        "thread_alive": bool(
            getattr(feishu_long_connection_service, "_ws_thread", None)
            and getattr(feishu_long_connection_service, "_ws_thread").is_alive()
        ),
        "app_id_configured": bool(settings.feishu_app_id) if hasattr(settings, 'feishu_app_id') else False,
    }


@router.get("/message-stats")
async def get_message_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get Feishu message statistics
    
    Returns:
        Message stats including recent real vs test messages
    """
    from datetime import datetime, timedelta
    
    # Get messages from last hour using ops layer
    one_hour_ago = datetime.now() - timedelta(hours=1)
    now = datetime.now()
    
    messages = await get_messages_in_time_range(db, one_hour_ago, now, limit=100)
    
    # Separate real vs test messages
    real_messages = [m for m in messages if not m.message_id.startswith(('test_', 'diag_', 'e2e_', 'verify_', 'check_', 'realtime_'))]
    test_messages = [m for m in messages if m.message_id.startswith(('test_', 'diag_', 'e2e_', 'verify_', 'check_', 'realtime_'))]
    
    return {
        "total_last_hour": len(messages),
        "real_messages": len(real_messages),
        "test_messages": len(test_messages),
        "latest_real": {
            "message_id": real_messages[0].message_id if real_messages else None,
            "content": real_messages[0].content[:50] if real_messages else None,
            "time": real_messages[0].send_time.isoformat() if real_messages else None,
        } if real_messages else None,
        "websocket_connections": manager.get_connection_count(),
        "long_connection_running": get_injector().long_connection_service._running,
    }


@router.post("/test-broadcast")
async def test_broadcast() -> dict:
    """
    Test WebSocket broadcast manually
    
    Returns:
        Broadcast status
    """
    try:
        logger.info(f"[TEST] Broadcasting test message to {manager.get_connection_count()} connections")
        
        from datetime import datetime
        await manager.broadcast({
            "type": "feishu-chat-message",
            "data": {
                "chat_id": "test_chat_id",
                "message_id": "test_message_id",
                "sender_id": "test_sender",
                "sender_type": "user",
                "content": "Test broadcast message",
                "send_time": datetime.now().isoformat()
            }
        })
        
        logger.info("[TEST] Broadcast complete")
        
        return {
            "status": "ok",
            "message": f"Broadcast sent to {manager.get_connection_count()} connections",
            "active_connections": manager.get_connection_count()
        }
    except Exception as e:
        logger.error(f"[TEST] Broadcast failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "active_connections": manager.get_connection_count()
        }


@router.post("/test-send-message")
async def test_send_message(
    payload: SendRecentChatRequest,
    bot_service: Any = Depends(get_bot_service),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    测试发送消息（带详细诊断信息）
    
    Args:
        payload: 消息内容
        bot_service: 飞书机器人服务
        db: 数据库会话
        
    Returns:
        详细的发送结果和诊断信息
    """
    try:
        # 获取chat_id
        chat_id = await get_latest_chat_id(db)
        
        diagnosis = {
            "step": "get_chat_id",
            "chat_id": chat_id,
            "chat_id_type": "unknown"
        }
        
        if chat_id:
            if chat_id.startswith("ou_"):
                diagnosis["chat_id_type"] = "open_id"
            elif chat_id.startswith("oc_"):
                diagnosis["chat_id_type"] = "chat_id"
            elif chat_id.startswith("on_"):
                diagnosis["chat_id_type"] = "union_id"
        
        if not chat_id:
            return {
                "success": False,
                "error": "no_chat_id",
                "diagnosis": diagnosis,
                "message": "暂无可用飞书会话"
            }
        
        # 尝试发送
        logger.info(f"[TEST] Attempting to send message to {chat_id} (type: {diagnosis['chat_id_type']})")
        
        success = await bot_service.send_message(chat_id, payload.message)
        
        # 获取详细错误信息
        last_error = getattr(bot_service, "last_send_error", None)
        
        diagnosis["send_result"] = "success" if success else "failed"
        diagnosis["last_error"] = last_error
        
        if success:
            return {
                "success": True,
                "diagnosis": diagnosis,
                "message": "Message sent successfully",
                "chat_id": chat_id
            }
        else:
            return {
                "success": False,
                "error": "send_failed",
                "diagnosis": diagnosis,
                "message": last_error or "飞书发送失败"
            }
            
    except Exception as e:
        logger.error(f"[TEST] Error in test_send_message: {e}", exc_info=True)
        return {
            "success": False,
            "error": "exception",
            "diagnosis": diagnosis if 'diagnosis' in locals() else {},
            "message": str(e)
        }


@router.post("/send-message")
async def send_test_message(
    chat_id: str,
    message: str,
    bot_service: Any = Depends(get_bot_service),
) -> dict[str, str]:
    """
    Send test message to Feishu chat

    Args:
        chat_id: Feishu chat ID
        message: Message content
        bot_service: Feishu bot service

    Returns:
        Send status
    """
    success = await bot_service.send_message(chat_id, message)

    if success:
        return {"status": "ok", "message": "Message sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send message")


@router.post("/send-to-recent-chat")
async def send_to_recent_chat(
    payload: SendRecentChatRequest,
    bot_service: Any = Depends(get_bot_service),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Send message to most recent chat (for frontend user interaction)

    Args:
        message: Message content
        bot_service: Feishu bot service
        db: Database session

    Returns:
        Send status
    """
    try:
        # Get most recent chat_id using ops layer
        chat_id = await get_latest_chat_id(db)

        if not chat_id:
            recent_logs = bot_chat_logger.get_recent_logs(limit=200)
            for item in recent_logs:
                value = item.get("chat_id")
                if value and value != "unknown":
                    chat_id = value
                    break
        
        if not chat_id:
            raise HTTPException(status_code=404, detail="暂无可用飞书会话，请先在飞书给机器人发送一条消息")
        
        # Send message
        success = await bot_service.send_message(chat_id, payload.message)
        
        if success:
            return {
                "status": "ok",
                "message": "Message sent successfully",
                "chat_id": chat_id
            }
        else:
            # 获取详细错误信息
            error_detail = getattr(bot_service, "last_send_error", None)
            
            # 如果bot_service有错误，使用它
            if error_detail:
                detail = error_detail
            # 否则提供诊断建议
            else:
                detail = "飞书发送失败。可能原因：\n1. 飞书应用未获得发送消息权限\n2. 会话已失效，请在飞书中重新给机器人发送消息\n3. chat_id无效"
            
            logger.error(f"Send message failed: {detail}, chat_id={chat_id}")
            raise HTTPException(status_code=502, detail=detail)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending to recent chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-stock-query-card")
async def send_stock_query_card(
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Send stock query interactive card to most recent chat
    
    Args:
        db: Database session
        
    Returns:
        Send status
    """
    try:
        # Get most recent chat_id using ops layer
        chat_id = await get_latest_chat_id(db)
        
        if not chat_id:
            raise HTTPException(status_code=404, detail="暂无可用飞书会话，请先在飞书给机器人发送一条消息")
        
        # Send stock query card
        card_service = get_card_service()
        success = await card_service.send_stock_query_card(chat_id)
        
        if success:
            return {
                "status": "ok",
                "message": "Stock query card sent successfully",
                "chat_id": chat_id
            }
        else:
            raise HTTPException(status_code=500, detail="发送股票查询卡片失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending stock query card: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-main-menu-card")
async def send_main_menu_card(
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Send main menu interactive card to most recent chat
    
    Args:
        db: Database session
        
    Returns:
        Send status
    """
    try:
        # Get most recent chat_id using ops layer
        chat_id = await get_latest_chat_id(db)
        
        if not chat_id:
            raise HTTPException(status_code=404, detail="暂无可用飞书会话，请先在飞书给机器人发送一条消息")
        
        # Send main menu card
        card_service = get_card_service()
        success = await card_service.send_main_menu_card(chat_id)
        
        if success:
            return {
                "status": "ok",
                "message": "Main menu card sent successfully",
                "chat_id": chat_id
            }
        else:
            raise HTTPException(status_code=500, detail="发送主菜单卡片失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending main menu card: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/push-event/{event_id}")
async def push_event_card(
    event_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Push event card by event ID
    
    Args:
        event_id: Event ID (e.g., STOCK_RESEARCH_START)
        db: Database session
        
    Returns:
        Send status
    """
    try:
        # Get most recent chat_id using ops layer
        chat_id = await get_latest_chat_id(db)
        
        if not chat_id:
            raise HTTPException(status_code=404, detail="暂无可用飞书会话，请先在飞书给机器人发送一条消息")
        
        # Send event card based on event_id
        card_service = get_card_service()
        success = False
        if event_id == "STOCK_RESEARCH_START":
            success = await card_service.send_stock_research_start_card(chat_id)
        else:
            raise HTTPException(status_code=400, detail=f"未知事件ID: {event_id}")
        
        if success:
            return {
                "status": "ok",
                "message": f"Event card {event_id} sent successfully",
                "event_id": event_id,
                "chat_id": chat_id
            }
        else:
            raise HTTPException(status_code=500, detail=f"发送事件卡片失败: {event_id}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pushing event card {event_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/card-json/{event_id}")
async def debug_card_json(
    event_id: str,
) -> dict[str, Any]:
    """
    Debug: Get the JSON structure of an event card
    
    Use this to verify the card JSON before sending
    """
    try:
        # Get card service
        card_service = get_card_service()
        
        # Create the card
        if event_id == "STOCK_RESEARCH_START":
            card = card_service._create_stock_research_start_card()
        else:
            raise HTTPException(status_code=400, detail=f"未知事件ID: {event_id}")
        
        # Ensure button names
        card = card_service._ensure_button_names(card)
        
        return {
            "status": "ok",
            "event_id": event_id,
            "card_json": card,
            "card_string": json.dumps(card, ensure_ascii=False),
            "validation": {
                "has_type": "type" in card,
                "has_data": "data" in card,
                "has_config": "config" in card,
                "has_elements": "elements" in card,
                "elements_count": len(card.get("elements", [])),
                "buttons_info": [
                    {
                        "index": i,
                        "has_name": "name" in action,
                        "name": action.get("name"),
                        "has_value": "value" in action,
                        "value_type": type(action.get("value")).__name__ if "value" in action else None,
                        "value_empty": len(action.get("value", {})) == 0 if "value" in action else None
                    }
                    for i, element in enumerate(card.get("elements", []))
                    if element.get("tag") == "action"
                    for j, action in enumerate(element.get("actions", []))
                    if action.get("tag") == "button"
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error debugging card JSON {event_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
