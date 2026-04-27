
import sys
import asyncio
from pathlib import Path

# 添加 backend 到 Python 路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from services.stock_service import StockService
from database.session import async_session_maker
from services.quote_data_service import quote_data_service
from routers.stock import CN_INDICES

async def update_indices():
    print("=" * 80)
    print("手动更新指数数据")
    print("=" * 80)
    
    stock_service = StockService()
    
    async with async_session_maker() as db:
        for full_code, name in CN_INDICES.items():
            print(f"\n更新 {name} ({full_code})...")
            # 强制从网络获取
            quote = await stock_service.get_quote(full_code, use_cache=False)
            if quote:
                print(f"  ✅ 获取成功: {quote.name}, 价格: {quote.price}")
                # 保存到数据库
                success = await quote_data_service.save_quote_to_db(db, quote)
                if success:
                    print(f"  ✅ 已保存到数据库: {quote.code}")
                else:
                    print(f"  ❌ 保存失败: {quote.code}")
            else:
                print(f"  ❌ 获取失败: {full_code}")
        
        await db.commit()

if __name__ == "__main__":
    asyncio.run(update_indices())
