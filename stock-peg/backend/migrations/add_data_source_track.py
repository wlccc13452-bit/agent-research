"""
添加数据来源追踪表的迁移脚本

运行方式:
    python migrations/add_data_source_track.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config.settings import settings
from database.base import Base
from database.models import DataSourceTrack
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """执行数据库迁移"""
    try:
        # 创建引擎
        engine = create_async_engine(settings.database_url, echo=True)
        
        # 创建表
        async with engine.begin() as conn:
            # 只创建DataSourceTrack表
            await conn.run_sync(DataSourceTrack.__table__.create, checkfirst=True)
            logger.info("[OK] 数据来源追踪表创建成功")
        
        # 关闭引擎
        await engine.dispose()
        
        logger.info("[OK] 迁移完成!")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] 迁移失败: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(migrate())
    sys.exit(0 if success else 1)
