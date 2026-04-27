"""测试 Holdings API 响应时间"""
import asyncio
import time
from services.holding_manager import HoldingManager

async def test_load_holdings():
    manager = HoldingManager()
    
    # 测试首次加载
    print("测试首次加载...")
    start = time.time()
    holdings = await manager.load_holdings()
    elapsed = time.time() - start
    print(f"首次加载耗时: {elapsed:.3f}秒")
    print(f"返回数据: {len(holdings.sectors)} 个板块")
    
    # 测试第二次加载（应该使用缓存）
    print("\n测试第二次加载...")
    start = time.time()
    holdings2 = await manager.load_holdings()
    elapsed2 = time.time() - start
    print(f"第二次加载耗时: {elapsed2:.3f}秒")
    print(f"返回数据: {len(holdings2.sectors)} 个板块")
    
    # 等待后台加载完成
    print("\n等待后台加载完成（5秒）...")
    await asyncio.sleep(5)
    
    # 测试第三次加载（应该使用后台加载的结果）
    print("\n测试第三次加载...")
    start = time.time()
    holdings3 = await manager.load_holdings()
    elapsed3 = time.time() - start
    print(f"第三次加载耗时: {elapsed3:.3f}秒")
    print(f"返回数据: {len(holdings3.sectors)} 个板块, {sum(len(s.stocks) for s in holdings3.sectors)} 只股票")

if __name__ == "__main__":
    asyncio.run(test_load_holdings())
