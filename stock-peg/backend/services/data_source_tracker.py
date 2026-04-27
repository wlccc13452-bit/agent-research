"""数据来源追踪服务"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database.operations import (
    track_data_read as ops_track_data_read,
    get_latest_tracks as ops_get_latest_tracks,
    get_current_data_status as ops_get_current_data_status,
    build_metadata_response as ops_build_metadata_response,
)
from database.models import DataSourceTrack

logger = logging.getLogger(__name__)


class DataSourceTracker:
    """数据来源追踪器 - ops层包装器"""
    
    # 数据来源位置映射（保留供外部引用）
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
    
    # 数据类型友好名称（保留供外部引用）
    DATA_TYPE_NAMES = {
        'kline': 'K线数据',
        'financial': '财务数据',
        'us_index': '美股指数',
        'cn_index': 'A股指数',
        'sector_index': '行业指数'
    }
    
    @staticmethod
    async def track_data_read(
        db: AsyncSession,
        data_type: str,
        stock_code: Optional[str],
        data_source: str,
        last_update_time: Optional[datetime] = None,
        is_updating: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DataSourceTrack:
        """记录数据读取 - 委托给 ops 层"""
        return await ops_track_data_read(
            db, data_type, stock_code, data_source,
            last_update_time, is_updating, metadata
        )
    
    @staticmethod
    async def get_latest_tracks(
        db: AsyncSession,
        data_type: Optional[str] = None,
        stock_code: Optional[str] = None,
        limit: int = 50
    ) -> list[DataSourceTrack]:
        """获取最新的数据读取记录 - 委托给 ops 层"""
        return await ops_get_latest_tracks(db, data_type, stock_code, limit)
    
    @staticmethod
    async def get_current_data_status(db: AsyncSession) -> Dict[str, Any]:
        """获取当前系统所有数据的状态概览 - 委托给 ops 层"""
        return await ops_get_current_data_status(db)
    
    @staticmethod
    def build_metadata_response(
        data: Any,
        data_type: str,
        stock_code: Optional[str],
        data_source: str,
        last_update: Optional[datetime] = None,
        is_updating: bool = False,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """构建带metadata的API响应 - 委托给 ops 层"""
        return ops_build_metadata_response(
            data, data_type, stock_code, data_source,
            last_update, is_updating, extra_metadata
        )


# 全局实例
data_source_tracker = DataSourceTracker()
