"""市场情绪历史数据回填工具

功能：
1. 从 Tushare API 获取历史市场情绪数据
2. 批量保存到数据库
3. 支持指定回填天数范围
"""
import asyncio
import sys
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Optional, Dict

# 添加 backend 目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import AsyncSession
from database.session import async_session_maker
from database.operations.market_sentiment_ops import save_sentiment, get_sentiment_by_date
from datasource import get_datasource, DataSourceType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_historical_sentiment(trade_date: date) -> Optional[Dict]:
    """获取指定日期的市场情绪数据（通过统一datasource模块）
    
    Args:
        trade_date: 交易日期
        
    Returns:
        市场情绪数据字典，失败返回 None
    """
    try:
        trade_date_str = trade_date.strftime('%Y%m%d')
        logger.info(f"获取 {trade_date_str} 的市场情绪数据...")
        
        # 通过统一datasource模块获取Tushare数据源
        from datasource import get_datasource, DataSourceType
        tushare = get_datasource().get_source(DataSourceType.TUSHARE)
        
        if not tushare or not await tushare.is_available():
            logger.error("Tushare 数据源不可用")
            return None
        
        # 使用 TushareDataSource 的公共方法
        sentiment = await tushare.get_historical_sentiment(trade_date)
        return sentiment

    except Exception as e:
        logger.error(f"获取 {trade_date} 市场情绪数据失败: {str(e)}")
        return None


async def get_sentiment_by_date_from_db(db: AsyncSession, trade_date: date) -> Optional[Dict]:
    """查询指定日期的市场情绪数据（通过ops层）"""
    return await get_sentiment_by_date(db, trade_date)


async def backfill_market_sentiment(
    days: int = 60,
    force: bool = False
) -> None:
    """回填历史市场情绪数据
    
    Args:
        days: 回填最近多少天的数据（默认60天）
        force: 是否强制覆盖已有数据
    """
    logger.info("=" * 80)
    logger.info(f"开始回填市场情绪历史数据（最近 {days} 天）")
    logger.info("=" * 80)
    
    # 获取 Tushare 数据源（通过统一datasource模块）
    from datasource import get_datasource, DataSourceType
    tushare = get_datasource().get_source(DataSourceType.TUSHARE)
    
    if not tushare or not await tushare.is_available():
        logger.error("Tushare 数据源不可用")
        return
    
    # 统计
    success_count = 0
    skip_count = 0
    error_count = 0
    
    # 批量获取并保存数据
    async with async_session_maker() as db:
        for days_back in range(days):
            trade_date = date.today() - timedelta(days=days_back)
            
            # 检查数据库是否已有数据
            existing = await get_sentiment_by_date_from_db(db, trade_date)
            
            if existing and not force:
                logger.info(f"[SKIP] {trade_date} 已有数据，跳过")
                skip_count += 1
                continue
            
            # 获取数据
            sentiment = await get_historical_sentiment(trade_date)
            
            if sentiment is None:
                skip_count += 1
                continue
            
            # 保存到数据库
            try:
                success = await save_sentiment(db, sentiment, trade_date)
                if success:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"保存 {trade_date} 数据失败: {str(e)}")
                error_count += 1
            
            # 避免API调用过快
            await asyncio.sleep(0.5)
    
    # 输出统计
    logger.info("=" * 80)
    logger.info(f"回填完成:")
    logger.info(f"  - 成功: {success_count} 天")
    logger.info(f"  - 跳过: {skip_count} 天")
    logger.info(f"  - 失败: {error_count} 天")
    logger.info("=" * 80)


if __name__ == '__main__':
    import argparse
    import pandas as pd  # 用于 pd.notna
    
    parser = argparse.ArgumentParser(description='市场情绪历史数据回填工具')
    parser.add_argument(
        '--days',
        type=int,
        default=60,
        help='回填最近多少天的数据（默认60天）'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制覆盖已有数据'
    )
    
    args = parser.parse_args()
    
    # 运行回填
    asyncio.run(backfill_market_sentiment(days=args.days, force=args.force))
