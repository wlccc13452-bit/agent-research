"""Quote Operations - 行情数据操作

提供行情数据相关的数据库操作：
- 查询行情数据
- 保存行情数据
- 检查更新必要性
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import StockRealtimeQuote

logger = logging.getLogger(__name__)


def _normalize_code(stock_code: str) -> str:
    """
    标准化股票代码
    
    - 如果包含 .SH 或 .SZ，保留完整代码（指数专用）
    - 如果以 sh 或 sz 开头，去掉前缀但保留纯代码
    - 否则保持原样
    """
    if '.' in stock_code:
        return stock_code
    return stock_code.replace('sh', '').replace('sz', '').replace('SH', '').replace('SZ', '')


async def get_quote(
    db: AsyncSession,
    stock_code: str
) -> Optional[StockRealtimeQuote]:
    """
    获取行情数据
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        
    Returns:
        行情数据，如果不存在则返回None
    """
    try:
        normalized_code = _normalize_code(stock_code)
        
        query = select(StockRealtimeQuote).where(
            StockRealtimeQuote.stock_code == normalized_code
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"获取行情数据失败 {stock_code}: {str(e)}")
        return None


async def save_quote(
    db: AsyncSession,
    quote_data: dict,
    data_source: str = 'api'
) -> bool:
    """
    保存行情数据
    
    Args:
        db: 数据库会话
        quote_data: 行情数据字典
        data_source: 数据来源
        
    Returns:
        是否保存成功
    """
    try:
        stock_code = _normalize_code(quote_data.get('code', ''))
        
        # 查询是否已存在
        query = select(StockRealtimeQuote).where(
            StockRealtimeQuote.stock_code == stock_code
        )
        result = await db.execute(query)
        existing_quote = result.scalar_one_or_none()
        
        now = datetime.now()
        
        if existing_quote:
            # 更新现有记录
            existing_quote.stock_name = quote_data.get('name', '')
            existing_quote.price = quote_data.get('price')
            existing_quote.change = quote_data.get('change')
            existing_quote.change_pct = quote_data.get('change_pct')
            existing_quote.open = quote_data.get('open')
            existing_quote.high = quote_data.get('high')
            existing_quote.low = quote_data.get('low')
            existing_quote.volume = quote_data.get('volume')
            existing_quote.amount = quote_data.get('amount')
            existing_quote.trade_time = now
            existing_quote.updated_at = now
            existing_quote.data_source = data_source
            
            logger.info(f"[OK] 更新行情数据: {stock_code}")
        else:
            # 创建新记录
            new_quote = StockRealtimeQuote(
                stock_code=stock_code,
                stock_name=quote_data.get('name', ''),
                price=quote_data.get('price'),
                change=quote_data.get('change'),
                change_pct=quote_data.get('change_pct'),
                open=quote_data.get('open'),
                high=quote_data.get('high'),
                low=quote_data.get('low'),
                volume=quote_data.get('volume'),
                amount=quote_data.get('amount'),
                trade_time=now,
                data_source=data_source
            )
            db.add(new_quote)
            logger.info(f"💾 保存新行情数据: {stock_code}")
        
        await db.commit()
        return True
        
    except Exception as e:
        logger.error(f"保存行情数据失败: {str(e)}")
        await db.rollback()
        return False


async def check_update_necessity(
    db: AsyncSession,
    stock_code: str,
    max_age_seconds: int = 60
) -> Dict:
    """
    检查行情数据是否需要更新
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        max_age_seconds: 最大允许的数据年龄（秒）
        
    Returns:
        {
            'needs_update': bool,
            'reason': str,
            'last_update': datetime or None
        }
    """
    try:
        normalized_code = _normalize_code(stock_code)
        
        query = select(StockRealtimeQuote).where(
            StockRealtimeQuote.stock_code == normalized_code
        )
        result = await db.execute(query)
        quote_data = result.scalar_one_or_none()
        
        if not quote_data:
            return {
                'needs_update': True,
                'reason': '数据库中无数据',
                'last_update': None
            }
        
        # 检查数据年龄
        time_since_update = datetime.now() - quote_data.updated_at
        if time_since_update.total_seconds() > max_age_seconds:
            return {
                'needs_update': True,
                'reason': f'数据已过期 ({time_since_update.total_seconds():.0f}秒前更新)',
                'last_update': quote_data.updated_at
            }
        
        return {
            'needs_update': False,
            'reason': '数据仍在有效期内',
            'last_update': quote_data.updated_at
        }
        
    except Exception as e:
        logger.error(f"检查行情更新必要性失败 {stock_code}: {str(e)}")
        return {
            'needs_update': True,
            'reason': f'检查失败: {str(e)}',
            'last_update': None
        }


async def get_quotes_batch(
    db: AsyncSession,
    stock_codes: List[str]
) -> List[StockRealtimeQuote]:
    """
    批量获取行情数据
    
    Args:
        db: 数据库会话
        stock_codes: 股票代码列表
        
    Returns:
        行情数据列表
    """
    try:
        normalized_codes = [_normalize_code(code) for code in stock_codes]
        
        query = select(StockRealtimeQuote).where(
            StockRealtimeQuote.stock_code.in_(normalized_codes)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    except Exception as e:
        logger.error(f"批量获取行情数据失败: {str(e)}")
        return []


async def get_all_quotes(db: AsyncSession) -> List[StockRealtimeQuote]:
    """
    获取所有行情数据
    
    Args:
        db: 数据库会话
        
    Returns:
        行情数据列表
    """
    try:
        query = select(StockRealtimeQuote).order_by(StockRealtimeQuote.stock_code)
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"获取所有行情数据失败: {str(e)}")
        return []


__all__ = [
    'get_quote',
    'save_quote',
    'check_update_necessity',
    'get_all_quotes',
]
