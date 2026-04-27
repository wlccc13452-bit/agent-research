"""
Feishu Chat Router - API for retrieving Feishu bot chat history
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from database.operations import (
    get_chat_history as db_get_chat_history,
    count_chat_messages,
    clear_all_chat_messages,
    check_message_exists,
    save_chat_message,
)
from services.bot_chat_logger import bot_chat_logger
from services.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feishu-chat", tags=["feishu-chat"])


class ChatMessage(BaseModel):
    """Chat message response model"""
    id: int
    message_id: str
    sender_id: Optional[str]
    sender_name: Optional[str]
    sender_type: str
    message_type: str
    content: str
    send_time: datetime
    reply_to_id: Optional[str]

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Chat history response model"""
    messages: list[ChatMessage]
    total: int
    has_more: bool


class IngestChatMessageRequest(BaseModel):
    chat_id: str
    message_id: str
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    sender_type: str
    message_type: str = "text"
    content: str
    send_time: datetime
    reply_to_id: Optional[str] = None


def _load_recent_messages_from_logs(limit: int) -> list[ChatMessage]:
    log_dir = Path(bot_chat_logger.log_dir)
    if not log_dir.exists():
        return []
    json_files = sorted(log_dir.glob("chat-*.json"), key=lambda p: p.name, reverse=True)
    messages: list[ChatMessage] = []
    local_id = 1
    for json_file in json_files:
        if len(messages) >= limit:
            break
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            continue
        for line in reversed(lines):
            if len(messages) >= limit:
                break
            try:
                item = json.loads(line.strip())
                send_time_raw = item.get("timestamp")
                send_time = datetime.fromisoformat(send_time_raw) if send_time_raw else datetime.now()
                messages.append(
                    ChatMessage(
                        id=local_id,
                        message_id=item.get("message_id", f"log_{local_id}"),
                        sender_id=item.get("sender_id"),
                        sender_name=item.get("sender_id"),
                        sender_type=item.get("sender_type", "user"),
                        message_type="text",
                        content=item.get("content", ""),
                        send_time=send_time,
                        reply_to_id=None,
                    )
                )
                local_id += 1
            except Exception:
                continue
    return messages


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    chat_id: Optional[str] = Query(None, description="Feishu chat ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> ChatHistoryResponse:
    """
    Get Feishu chat message history

    Args:
        chat_id: Optional chat ID filter
        limit: Number of messages to return
        offset: Offset for pagination
        db: Database session

    Returns:
        ChatHistoryResponse with messages and pagination info
    """
    try:
        # Get total count
        total = await count_chat_messages(db, chat_id)
        
        # Get messages using ops layer
        messages = await db_get_chat_history(
            db,
            chat_id=chat_id,
            limit=limit,
            offset=offset
        )

        # Convert to response model
        chat_messages = [
            ChatMessage(
                id=msg.id,
                message_id=msg.message_id,
                sender_id=msg.sender_id,
                sender_name=msg.sender_name,
                sender_type=msg.sender_type or "user",
                message_type=msg.message_type or "text",
                content=msg.content,
                send_time=msg.send_time,
                reply_to_id=msg.reply_to_id,
            )
            for msg in messages
        ]

        return ChatHistoryResponse(
            messages=chat_messages,
            total=total,
            has_more=(offset + limit) < total,
        )

    except Exception as e:
        logger.error(f"Error getting chat history: {e}", exc_info=True)
        return ChatHistoryResponse(messages=[], total=0, has_more=False)


@router.get("/recent", response_model=list[ChatMessage])
async def get_recent_messages(
    limit: int = Query(20, ge=1, le=100, description="Number of recent messages"),
    db: AsyncSession = Depends(get_db),
) -> list[ChatMessage]:
    """
    Get most recent chat messages across all chats

    Args:
        limit: Number of messages to return
        db: Database session

    Returns:
        List of recent ChatMessage
    """
    try:
        # Get messages using ops layer
        messages = await db_get_chat_history(db, limit=limit)
        
        # If database has messages, return them
        if messages:
            return [
                ChatMessage(
                    id=msg.id,
                    message_id=msg.message_id,
                    sender_id=msg.sender_id,
                    sender_name=msg.sender_name,
                    sender_type=msg.sender_type or "user",
                    message_type=msg.message_type or "text",
                    content=msg.content,
                    send_time=msg.send_time,
                    reply_to_id=msg.reply_to_id,
                )
                for msg in messages
            ]
        
        # Fallback to log files only if database is empty
        log_messages = _load_recent_messages_from_logs(limit)
        return log_messages

    except Exception as e:
        logger.error(f"Error getting recent messages: {e}", exc_info=True)
        return []


@router.post("/clear")
async def clear_chat_history(
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        # Clear all messages using ops layer
        deleted_rows = await clear_all_chat_messages(db)

        log_dir = Path(bot_chat_logger.log_dir)
        deleted_files = 0
        if log_dir.exists():
            for file_path in log_dir.glob("chat-*.*"):
                if file_path.suffix in {".json", ".log"}:
                    try:
                        file_path.unlink(missing_ok=True)
                        deleted_files += 1
                    except PermissionError:
                        # Windows: 文件可能被日志系统占用，跳过
                        logger.warning(f"无法删除日志文件（可能被占用）: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"删除日志文件失败 {file_path.name}: {e}")

        await manager.broadcast(
            {
                "type": "feishu-chat-cleared",
                "data": {
                    "deleted_rows": deleted_rows,
                    "deleted_files": deleted_files,
                },
            }
        )
        return {
            "status": "ok",
            "deleted_rows": deleted_rows,
            "deleted_files": deleted_files,
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error clearing chat history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="clear_failed")


@router.post("/ingest")
async def ingest_chat_message(
    payload: IngestChatMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        # Check if message exists using ops layer
        exists = await check_message_exists(db, payload.message_id)

        if not exists:
            # Save message using ops layer
            await save_chat_message(
                db,
                chat_id=payload.chat_id,
                message_id=payload.message_id,
                sender_id=payload.sender_id,
                sender_name=payload.sender_name,
                sender_type=payload.sender_type,
                message_type=payload.message_type,
                content=payload.content,
                send_time=payload.send_time,
                reply_to_id=payload.reply_to_id,
            )
            bot_chat_logger.log_message(
                message_id=payload.message_id,
                sender_type=payload.sender_type,
                sender_id=payload.sender_id,
                content=payload.content,
                chat_id=payload.chat_id,
            )

        await manager.broadcast(
            {
                "type": "feishu-chat-message",
                "data": {
                    "chat_id": payload.chat_id,
                    "message_id": payload.message_id,
                    "sender_id": payload.sender_id,
                    "sender_name": payload.sender_name,
                    "sender_type": payload.sender_type,
                    "message_type": payload.message_type,
                    "content": payload.content,
                    "send_time": payload.send_time.isoformat(),
                    "reply_to_id": payload.reply_to_id,
                },
            }
        )

        return {
            "status": "ok",
            "saved": not exists,
            "message_id": payload.message_id,
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error ingesting chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="ingest_failed")
