"""
快速验证修复 - 测试 StockQuote 模型
"""
import sys
import asyncio
from pathlib import Path

# 添加backend路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from database.session import async_session_maker
from services.quote_data_service import QuoteDataService
from models import StockQuote
from datetime import datetime


async def test_quote_model():
    """测试 StockQuote 模型"""
    print("=" * 60)
    print("验证 StockQuote 模型修复")
    print("=" * 60)
    
    # 测试1: 创建 StockQuote 对象
    print("\n测试1: 创建 StockQuote 对象（带 timestamp）")
    try:
        quote = StockQuote(
            code="000657",
            name="中钨高新",
            price=10.5,
            change=0.5,
            change_pct=5.0,
            open=10.0,
            high=10.8,
            low=9.9,
            volume=1000000,
            amount=10500000.0,
            timestamp=datetime.now()
        )
        print(f"[OK] 成功创建 StockQuote 对象")
        print(f"   代码: {quote.code}, 价格: {quote.price}, 时间戳: {quote.timestamp}")
    except Exception as e:
        print(f"[ERROR] 创建失败: {e}")
        return False
    
    # 测试2: 从数据库读取
    print("\n测试2: 从数据库读取行情数据")
    try:
        async with async_session_maker() as db:
            service = QuoteDataService()
            quote = await service.get_quote_from_db(db, "000657")
            
            if quote:
                print(f"[OK] 成功从数据库读取")
                print(f"   代码: {quote.code}")
                print(f"   名称: {quote.name}")
                print(f"   价格: {quote.price}")
                print(f"   时间戳: {quote.timestamp}")
                return True
            else:
                print(f"[WARN] 数据库中未找到该股票")
                return False
    except Exception as e:
        print(f"[ERROR] 读取失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    success = await test_quote_model()
    
    print("\n" + "=" * 60)
    if success:
        print("[OK] 验证成功！StockQuote 模型已修复")
    else:
        print("[WARN] 验证完成，但可能需要检查数据库数据")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
