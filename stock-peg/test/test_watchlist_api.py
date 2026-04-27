"""测试动态关注API"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from database.session import async_session_maker
from services.daily_watchlist_manager import daily_watchlist_manager
from sqlalchemy import select
from database import DailyWatchlist


async def test_watchlist_data():
    """测试动态关注数据"""
    print("\n=== 测试动态关注数据 ===\n")
    
    async with async_session_maker() as db:
        # 1. 检查数据库中是否有数据
        result = await db.execute(select(DailyWatchlist))
        all_stocks = result.scalars().all()
        
        print(f"数据库中总共有 {len(all_stocks)} 条动态关注记录")
        
        if all_stocks:
            print("\n前5条记录:")
            for stock in all_stocks[:5]:
                print(f"  - {stock.watch_date} | {stock.stock_name} ({stock.stock_code}) | 是否归档: {stock.is_archived}")
        
        # 2. 测试 API 返回
        print("\n\n=== 测试 API get_summary() ===\n")
        
        summary = await daily_watchlist_manager.get_summary(db, include_archived=False, limit=10)
        
        print(f"API 返回:")
        print(f"  总日期数: {summary.total_dates}")
        print(f"  总股票数: {summary.total_stocks}")
        
        if summary.dates:
            print(f"\n  日期列表:")
            for date_group in summary.dates[:5]:
                print(f"    - {date_group.watch_date}: {date_group.total_count} 只股票")
        else:
            print("  ⚠️ 没有返回任何日期数据")


if __name__ == "__main__":
    asyncio.run(test_watchlist_data())
