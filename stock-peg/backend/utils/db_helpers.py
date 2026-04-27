"""
Database Helpers - 数据库操作辅助工具

提供简化的数据库会话管理和常用操作。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, TypeVar, Callable, Any
from database.session import get_db

logger = __import__('logging').getLogger(__name__)

T = TypeVar('T')


@asynccontextmanager
async def get_db_session():
    """
    简化的数据库会话上下文管理器
    
    自动处理会话的获取和关闭。
    
    Yields:
        AsyncSession: 数据库会话对象
        
    Example:
        async with get_db_session() as db:
            result = await db.execute(query)
            await db.commit()
    """
    async for db in get_db():
        try:
            yield db
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            await db.close()
            break


async def with_database(func: Callable[..., T], *args, **kwargs) -> T:
    """
    在数据库会话中执行函数
    
    Args:
        func: 要执行的异步函数（第一个参数应该是 db session）
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        函数返回值
        
    Example:
        async def my_query(db, user_id):
            return await db.execute(select(User).where(User.id == user_id))
            
        result = await with_database(my_query, user_id=123)
    """
    async with get_db_session() as db:
        return await func(db, *args, **kwargs)


async def execute_query(query: Any, commit: bool = True) -> Any:
    """
    执行数据库查询的快捷方法
    
    Args:
        query: SQLAlchemy 查询对象
        commit: 是否提交事务
        
    Returns:
        查询结果
        
    Example:
        from sqlalchemy import select
        from database.models import User
        
        result = await execute_query(select(User).where(User.id == 1))
    """
    async with get_db_session() as db:
        result = await db.execute(query)
        if commit:
            await db.commit()
        return result


async def execute_update(update_stmt: Any) -> bool:
    """
    执行更新操作的快捷方法
    
    Args:
        update_stmt: SQLAlchemy update 语句
        
    Returns:
        是否成功
        
    Example:
        from sqlalchemy import update
        from database.models import User
        
        success = await execute_update(
            update(User).where(User.id == 1).values(name="New Name")
        )
    """
    try:
        async with get_db_session() as db:
            await db.execute(update_stmt)
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Update failed: {e}", exc_info=True)
        return False


async def get_model_by_id(model_class: type, record_id: int) -> Any | None:
    """
    根据ID获取模型实例
    
    Args:
        model_class: 模型类
        record_id: 记录ID
        
    Returns:
        模型实例或None
        
    Example:
        from database.models import PriceAlert
        
        alert = await get_model_by_id(PriceAlert, 123)
    """
    from sqlalchemy import select
    
    async with get_db_session() as db:
        stmt = select(model_class).where(model_class.id == record_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
