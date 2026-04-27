
import sys
import asyncio
from pathlib import Path
from sqlalchemy import select, delete, update
from datetime import datetime

# 添加 backend 到 Python 路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from database.session import async_session_maker
from database.models import StockRealtimeQuote
from routers.stock import CN_INDICES

async def fix_indices_data():
    print("=" * 80)
    print("修复数据库中的指数数据格式")
    print("=" * 80)
    
    async with async_session_maker() as db:
        # 1. 识别并重命名/清理
        for full_code, index_name in CN_INDICES.items():
            pure_code = full_code.split('.')[0]
            print(f"\n处理指数: {index_name} ({full_code})")
            
            # 查找是否存在旧格式 (pure_code)
            query = select(StockRealtimeQuote).where(StockRealtimeQuote.stock_code == pure_code)
            result = await db.execute(query)
            old_quote = result.scalar_one_or_none()
            
            if old_quote:
                # 检查是否真的是指数 (根据名称判断)
                if old_quote.stock_name == index_name:
                    print(f"  ✅ 发现匹配的旧格式数据: {pure_code} -> {index_name}")
                    
                    # 检查是否已经存在新格式数据
                    query_new = select(StockRealtimeQuote).where(StockRealtimeQuote.stock_code == full_code)
                    result_new = await db.execute(query_new)
                    new_quote = result_new.scalar_one_or_none()
                    
                    if new_quote:
                        print(f"  ⚠️ 新格式数据 {full_code} 已存在，删除旧格式数据 {pure_code}")
                        await db.execute(delete(StockRealtimeQuote).where(StockRealtimeQuote.stock_code == pure_code))
                    else:
                        print(f"  🔄 将 {pure_code} 重命名为 {full_code}")
                        old_quote.stock_code = full_code
                else:
                    print(f"  ⚠️ 发现代码冲突: {pure_code} 是 {old_quote.stock_name}，而不是 {index_name}。跳过重命名。")
            else:
                print(f"  ℹ️ 未发现旧格式数据: {pure_code}")
        
        await db.commit()
        print("\n✅ 数据库修复完成")

if __name__ == "__main__":
    asyncio.run(fix_indices_data())
