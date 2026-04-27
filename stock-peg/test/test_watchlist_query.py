#!/usr/bin/env python3
"""测试get_watchlist_by_stock方法"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from database.session import async_session_maker
from database.operations.watchlist_ops import get_watchlist_by_stock


async def test_query():
    """测试查询watchlist"""
    print("=" * 100)
    print("Testing get_watchlist_by_stock() method")
    print("=" * 100)
    
    # 测试不同的股票代码格式
    test_codes = [
        "600219",      # 纯代码
        "sh600219",    # 带交易所前缀
        "SH600219",    # 大写
        "300378",      # 数据库中存在的股票
    ]
    
    async with async_session_maker() as db:
        for code in test_codes:
            print(f"\n[Testing] stock_code = '{code}'")
            records = await get_watchlist_by_stock(db, code)
            print(f"  Result: Found {len(records)} records")
            
            if records:
                for record in records:
                    print(f"    - ID: {record.id}")
                    print(f"      Stock code: {record.stock_code}")
                    print(f"      Stock name: {record.stock_name}")
                    print(f"      Target price: {record.target_price}")
                    print(f"      Change up pct: {record.change_up_pct}")
                    print(f"      Change down pct: {record.change_down_pct}")
    
    print("\n" + "=" * 100)
    print("Test completed")
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(test_query())
