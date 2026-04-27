
import sys
import asyncio
from pathlib import Path
from sqlalchemy import select
from datetime import datetime

# 添加 backend 到 Python 路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from database.session import async_session_maker
from database.models import StockRealtimeQuote, USDailyData
from routers.stock import CN_INDICES

async def check_indices():
    print("=" * 80)
    print("检查指数数据")
    print("=" * 80)
    
    async with async_session_maker() as db:
        # 1. 检查 A 股指数
        print("\n[A股指数]")
        print("-" * 40)
        cn_index_codes = list(CN_INDICES.keys())
        print(f"配置的 A 股指数: {cn_index_codes}")
        
        # 查询所有行情数据，看看存储格式
        query = select(StockRealtimeQuote)
        result = await db.execute(query)
        quotes = result.scalars().all()
        
        print(f"数据库中共有 {len(quotes)} 条行情记录")
        
        found_indices = []
        for q in quotes:
            # 检查是否匹配配置的指数
            match = False
            if q.stock_code in cn_index_codes:
                match = True
            else:
                # 尝试带后缀匹配
                for code in cn_index_codes:
                    if code.startswith(q.stock_code) or q.stock_code.startswith(code.split('.')[0]):
                        match = True
                        break
            
            if match:
                found_indices.append(q)
                print(f"找到指数记录: code={q.stock_code}, name={q.stock_name}, price={q.price}, updated_at={q.updated_at}")
        
        # 精确匹配
        exact_found_codes = {q.stock_code for q in found_indices}
        missing = [code for code in cn_index_codes if code not in exact_found_codes]
        if missing:
            print(f"❌ 缺失的 A 股指数: {missing}")
            # 看看是否是因为格式问题（比如存储的是 000001 而不是 000001.SH）
            for code in missing:
                pure_code = code.split('.')[0]
                if pure_code in exact_found_codes:
                    print(f"  ⚠️ 发现相似代码 {pure_code}，可能存储格式不匹配 (期望 {code})")
        else:
            print("✅ 所有 A 股指数在数据库中都有记录")

        # 2. 检查美股指数
        print("\n[美股指数]")
        print("-" * 40)
        us_indices = ['^GSPC', '^IXIC', '^DJI', '^VIX']
        print(f"配置的美股指数: {us_indices}")
        
        # 美股指数通常存储在 USDailyData 表中
        try:
            query = select(USDailyData).where(USDailyData.us_stock_code.in_(us_indices))
            result = await db.execute(query)
            us_quotes = result.scalars().all()
            
            print(f"找到 {len(us_quotes)} 条美股指数记录")
            for q in us_quotes:
                print(f"找到美股指数: code={q.us_stock_code}, price={q.close_price}, date={q.trade_date}")
            
            found_us_codes = {q.us_stock_code for q in us_quotes}
            missing_us = [code for code in us_indices if code not in found_us_codes]
            if missing_us:
                print(f"❌ 缺失的美股指数: {missing_us}")
            else:
                print("✅ 所有美股指数在数据库中都有记录")
        except Exception as e:
            print(f"❌ 检查美股指数失败: {e}")

if __name__ == "__main__":
    asyncio.run(check_indices())
