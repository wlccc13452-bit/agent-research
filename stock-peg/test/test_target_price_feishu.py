#!/usr/bin/env python3
"""
测试飞书Card基准价信息显示功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from database.session import async_session_maker
from database.operations.watchlist_ops import get_watchlist_by_stock


async def test_get_target_price():
    """测试获取股票基准价信息"""
    print("=" * 80)
    print("测试飞书Card基准价信息获取功能")
    print("=" * 80)
    
    # 测试股票代码
    test_stocks = ["600219", "002497"]  # 南山铝业、雅化集团
    
    async with async_session_maker() as db:
        for stock_code in test_stocks:
            print(f"\n股票代码: {stock_code}")
            print("-" * 40)
            
            try:
                records = await get_watchlist_by_stock(db, stock_code)
                
                if records:
                    record = records[0]
                    print(f"[OK] Found record:")
                    print(f"  Stock name: {record.stock_name}")
                    print(f"  Target price: {record.target_price}")
                    print(f"  Change up pct: {record.change_up_pct}%")
                    print(f"  Change down pct: {record.change_down_pct}%")
                    print(f"  Stop loss price: {record.stop_loss_price}")
                    print(f"  Notes: {record.notes}")
                    
                    # 模拟飞书Card显示
                    if record.target_price:
                        print(f"\n[FEISHU CARD] Display content:")
                        upper = record.target_price * (1 + (record.change_up_pct or 0) / 100)
                        lower = record.target_price * (1 - (record.change_down_pct or 0) / 100)
                        print(f"  Target price: {record.target_price:.2f}  |  Control range: {lower:.2f} ~ {upper:.2f}")
                        print(f"  Control ratio: +{record.change_up_pct or 0}% / -{record.change_down_pct or 0}%")
                        
                        if record.stop_loss_price:
                            print(f"  Stop loss: {record.stop_loss_price:.2f}")
                        
                        if record.notes:
                            print(f"  Notes: {record.notes}")
                else:
                    print(f"[FAIL] No record found")
                    
            except Exception as e:
                print(f"[ERROR] {e}")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_get_target_price())
