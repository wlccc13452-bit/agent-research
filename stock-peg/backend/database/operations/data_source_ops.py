"""Data Source Operations - 数据来源追踪操作

提供数据来源追踪相关的数据库操作：
- 记录数据读取
- 查询追踪记录
- 获取数据状态
"""

import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import DataSourceTrack

logger = logging.getLogger(__name__)


# 数据来源位置映射
SOURCE_LOCATIONS = {
    'kline': {
        'db': 'stock_kline_data表 (Tushare)',
        'api': 'Tushare API (实时)'
    },
    'financial': {
        'db': 'financial_history表 (Tushare)',
        'api': 'Tushare API (实时)'
    },
    'us_index': {
        'db': 'us_daily_data表 (Yahoo Finance)',
        'api': 'Yahoo Finance API (实时)'
    },
    'cn_index': {
        'db': 'stock_kline_data表 (Akshare)',
        'api': 'Akshare API (实时)'
    },
    'sector_index': {
        'db': 'stock_kline_data表 (Akshare)',
        'api': 'Akshare API (实时)'
    }
}

# 数据类型友好名称
DATA_TYPE_NAMES = {
    'kline': 'K线数据',
    'financial': '财务数据',
    'us_index': '美股指数',
    'cn_index': 'A股指数',
    'sector_index': '行业指数'
}


async def track_data_read(
    db: AsyncSession,
    data_type: str,
    stock_code: Optional[str],
    data_source: str,
    last_update_time: Optional[datetime] = None,
    is_updating: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> DataSourceTrack:
    """
    记录数据读取
    
    Args:
        db: 数据库会话
        data_type: 数据类型 (kline/financial/us_index/cn_index/sector_index)
        stock_code: 股票代码或指数代码
        data_source: 数据来源 (db/cache/api)
        last_update_time: 数据最后更新时间
        is_updating: 是否正在后台更新
        metadata: 额外的元数据
        
    Returns:
        DataSourceTrack记录
    """
    try:
        # 获取来源位置
        source_location = SOURCE_LOCATIONS.get(data_type, {}).get(data_source, data_source)
        
        track = DataSourceTrack(
            data_type=data_type,
            stock_code=stock_code,
            data_source=data_source,
            last_update_time=last_update_time,
            source_location=source_location,
            is_updating=1 if is_updating else 0,
            metadata_json=json.dumps(metadata) if metadata else None
        )
        
        db.add(track)
        await db.commit()
        await db.refresh(track)
        
        logger.debug(f"记录数据读取: {data_type}/{stock_code} from {data_source}")
        return track
        
    except Exception as e:
        logger.error(f"记录数据读取失败: {e}")
        await db.rollback()
        raise


async def get_latest_tracks(
    db: AsyncSession,
    data_type: Optional[str] = None,
    stock_code: Optional[str] = None,
    limit: int = 50
) -> List[DataSourceTrack]:
    """
    获取最新的数据读取记录
    
    Args:
        db: 数据库会话
        data_type: 筛选数据类型
        stock_code: 筛选股票代码
        limit: 返回数量限制
        
    Returns:
        DataSourceTrack列表
    """
    try:
        query = select(DataSourceTrack).order_by(desc(DataSourceTrack.read_time))
        
        if data_type:
            query = query.where(DataSourceTrack.data_type == data_type)
        
        if stock_code:
            query = query.where(DataSourceTrack.stock_code == stock_code)
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
        
    except Exception as e:
        logger.error(f"获取数据读取记录失败: {e}")
        return []


async def get_current_data_status(
    db: AsyncSession
) -> Dict[str, Any]:
    """
    获取当前系统所有数据的状态概览
    
    Returns:
        各数据类型的最新状态
    """
    try:
        # 获取每种数据类型的最新读取记录
        data_types = ['kline', 'financial', 'us_index', 'cn_index', 'sector_index']
        status = {}
        
        for dt in data_types:
            query = select(DataSourceTrack).where(
                DataSourceTrack.data_type == dt
            ).order_by(desc(DataSourceTrack.read_time)).limit(1)
            
            result = await db.execute(query)
            track = result.scalar_one_or_none()
            
            if track:
                status[dt] = {
                    'data_type': track.data_type,
                    'data_type_name': DATA_TYPE_NAMES.get(track.data_type, track.data_type),
                    'stock_code': track.stock_code,
                    'data_source': track.data_source,
                    'read_time': track.read_time.isoformat() if track.read_time else None,
                    'last_update_time': track.last_update_time.isoformat() if track.last_update_time else None,
                    'source_location': track.source_location,
                    'is_updating': bool(track.is_updating)
                }
            else:
                status[dt] = {
                    'data_type': dt,
                    'data_type_name': DATA_TYPE_NAMES.get(dt, dt),
                    'stock_code': None,
                    'data_source': None,
                    'read_time': None,
                    'last_update_time': None,
                    'source_location': None,
                    'is_updating': False
                }
        
        return status
        
    except Exception as e:
        logger.error(f"获取数据状态概览失败: {e}")
        return {}


def build_metadata_response(
    data: Any,
    data_type: str,
    stock_code: Optional[str],
    data_source: str,
    last_update: Optional[datetime] = None,
    is_updating: bool = False,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    构建带metadata的API响应
    
    Args:
        data: 实际数据
        data_type: 数据类型
        stock_code: 股票代码
        data_source: 数据来源
        last_update: 最后更新时间
        is_updating: 是否正在更新
        extra_metadata: 额外的元数据
        
    Returns:
        标准化的API响应
    """
    source_location = SOURCE_LOCATIONS.get(data_type, {}).get(data_source, data_source)
    
    metadata = {
        'data_type': data_type,
        'data_type_name': DATA_TYPE_NAMES.get(data_type, data_type),
        'stock_code': stock_code,
        'data_source': data_source,
        'read_time': datetime.now().isoformat(),
        'last_update': last_update.isoformat() if last_update else None,
        'source_location': source_location,
        'is_updating': is_updating
    }
    
    if extra_metadata:
        metadata.update(extra_metadata)
    
    return {
        'data': data,
        'metadata': metadata
    }


__all__ = [
    'track_data_read',
    'get_latest_tracks',
    'get_current_data_status',
    'build_metadata_response',
]
