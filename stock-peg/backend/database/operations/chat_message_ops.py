"""Chat Message Operations - 聊天消息数据操作

提供聊天消息相关的数据库操作：
- 保存消息
- 查询消息历史
"""

import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import FeishuChatMessage

logger = logging.getLogger(__name__)


async def save_chat_message(
    db: AsyncSession,
    chat_id: str,
    message_id: str,
    sender_id: Optional[str],
    sender_name: Optional[str],
    sender_type: str,
    content: str,
    send_time: datetime,
    message_type: str = "text",
    reply_to_id: Optional[str] = None,
) -> bool:
    """
    保存聊天消息到数据库
    
    Args:
        db: 数据库会话
        chat_id: 飞书聊天ID
        message_id: 飞书消息ID
        sender_id: 发送者ID
        sender_name: 发送者名称
        sender_type: 发送者类型 ('user' 或 'bot')
        content: 消息内容
        send_time: 发送时间
        message_type: 消息类型
        reply_to_id: 回复的消息ID
        
    Returns:
        True 如果保存成功，False 如果消息已存在或出错
    """
    try:
        # 检查消息是否已存在（避免重复保存）
        stmt = select(FeishuChatMessage).where(FeishuChatMessage.message_id == message_id)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.debug(f"消息 {message_id[:16]}... 已存在，跳过重复保存")
            return False
        
        # 创建新消息记录
        message = FeishuChatMessage(
            chat_id=chat_id,
            message_id=message_id,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_type=sender_type,
            message_type=message_type,
            content=content,
            send_time=send_time,
            reply_to_id=reply_to_id,
        )
        
        db.add(message)
        await db.commit()
        return True
        
    except Exception as e:
        await db.rollback()
        logger.error(f"保存聊天消息失败: {e}", exc_info=True)
        return False


async def get_chat_history(
    db: AsyncSession,
    chat_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[FeishuChatMessage]:
    """
    获取聊天历史记录
    
    Args:
        db: 数据库会话
        chat_id: 聊天ID（可选，不指定则返回所有聊天的消息）
        limit: 返回记录数
        offset: 偏移量
        
    Returns:
        消息列表
    """
    stmt = select(FeishuChatMessage)
    
    if chat_id:
        stmt = stmt.where(FeishuChatMessage.chat_id == chat_id)
    
    stmt = stmt.order_by(FeishuChatMessage.send_time.desc()) \
        .limit(limit) \
        .offset(offset)
    
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_recent_messages(
    db: AsyncSession,
    chat_id: str,
    since: datetime
) -> List[FeishuChatMessage]:
    """
    获取指定时间后的消息
    
    Args:
        db: 数据库会话
        chat_id: 聊天ID
        since: 起始时间
        
    Returns:
        消息列表
    """
    stmt = select(FeishuChatMessage) \
        .where(FeishuChatMessage.chat_id == chat_id) \
        .where(FeishuChatMessage.send_time >= since) \
        .order_by(FeishuChatMessage.send_time.asc())
    
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_latest_chat_id(db: AsyncSession) -> Optional[str]:
    """
    获取最新的聊天ID
    
    Args:
        db: 数据库会话
        
    Returns:
        最新的聊天ID，如果没有消息则返回None
    """
    from sqlalchemy import desc
    
    stmt = select(FeishuChatMessage.chat_id) \
        .order_by(desc(FeishuChatMessage.send_time)) \
        .limit(1)
    
    result = await db.execute(stmt)
    chat_id = result.scalar_one_or_none()
    return chat_id


async def get_messages_in_time_range(
    db: AsyncSession,
    start_time: datetime,
    end_time: datetime,
    limit: int = 100
) -> List[FeishuChatMessage]:
    """
    获取时间范围内的消息
    
    Args:
        db: 数据库会话
        start_time: 开始时间
        end_time: 结束时间
        limit: 返回记录数限制
        
    Returns:
        消息列表
    """
    from sqlalchemy import desc, and_
    
    stmt = select(FeishuChatMessage) \
        .where(and_(
            FeishuChatMessage.send_time >= start_time,
            FeishuChatMessage.send_time <= end_time
        )) \
        .order_by(desc(FeishuChatMessage.send_time)) \
        .limit(limit)
    
    result = await db.execute(stmt)
    return result.scalars().all()


async def clear_all_chat_messages(db: AsyncSession) -> int:
    """
    清空所有聊天消息
    
    Args:
        db: 数据库会话
        
    Returns:
        删除的记录数
    """
    from sqlalchemy import delete
    
    result = await db.execute(delete(FeishuChatMessage))
    await db.commit()
    return result.rowcount


async def check_message_exists(db: AsyncSession, message_id: str) -> bool:
    """
    检查消息是否存在
    
    Args:
        db: 数据库会话
        message_id: 消息ID
        
    Returns:
        是否存在
    """
    stmt = select(FeishuChatMessage.id).where(
        FeishuChatMessage.message_id == message_id
    ).limit(1)
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def count_chat_messages(
    db: AsyncSession,
    chat_id: Optional[str] = None
) -> int:
    """
    统计消息数量
    
    Args:
        db: 数据库会话
        chat_id: 聊天ID（可选，不指定则统计所有）
        
    Returns:
        消息数量
    """
    from sqlalchemy import func
    
    stmt = select(func.count()).select_from(FeishuChatMessage)
    if chat_id:
        stmt = stmt.where(FeishuChatMessage.chat_id == chat_id)
    
    result = await db.execute(stmt)
    return result.scalar_one() or 0


__all__ = [
    'save_chat_message',
    'get_chat_history',
    'get_recent_messages',
    'get_latest_chat_id',
    'get_messages_in_time_range',
    'clear_all_chat_messages',
    'check_message_exists',
    'count_chat_messages',
]
