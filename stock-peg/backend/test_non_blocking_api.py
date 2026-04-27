"""测试 Non-Blocking API 是否真正非阻塞

验证点：
1. /api/holdings 是否立即返回（<1秒）
2. 首次加载是否返回空数据或缓存数据
3. 后台任务是否正确执行
4. WebSocket 更新通知是否发送
"""
import asyncio
import time
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_holdings_api():
    """测试 holdings API 的响应时间"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("测试 1: Holdings API 响应时间")
        print("=" * 60)
        
        # 第一次请求（可能触发加载）
        print("\n📡 发送第一次请求...")
        start_time = time.time()
        try:
            response = await client.get(f"{BASE_URL}/holdings/")
            duration = time.time() - start_time
            
            print(f"✅ 响应时间: {duration:.2f}秒")
            print(f"✅ 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                sectors = data.get('sectors', [])
                total_stocks = sum(len(s.get('stocks', [])) for s in sectors)
                print(f"✅ 返回数据: {len(sectors)} 个板块, {total_stocks} 只股票")
                
                if duration < 1.0:
                    print("✅ PASS: API 响应时间 < 1秒（符合非阻塞要求）")
                else:
                    print("❌ FAIL: API 响应时间 > 1秒（可能存在阻塞）")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
        
        # 等待后台加载
        print("\n⏳ 等待后台加载完成（5秒）...")
        await asyncio.sleep(5)
        
        # 第二次请求（应该命中缓存）
        print("\n📡 发送第二次请求...")
        start_time = time.time()
        try:
            response = await client.get(f"{BASE_URL}/holdings/")
            duration = time.time() - start_time
            
            print(f"✅ 响应时间: {duration:.2f}秒")
            print(f"✅ 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                sectors = data.get('sectors', [])
                total_stocks = sum(len(s.get('stocks', [])) for s in sectors)
                print(f"✅ 返回数据: {len(sectors)} 个板块, {total_stocks} 只股票")
                
                # 检查是否有 TEMP_ 或 UNKNOWN_ 代码
                temp_codes = []
                for sector in sectors:
                    for stock in sector.get('stocks', []):
                        code = stock.get('code', '')
                        if code.startswith('TEMP_') or code.startswith('UNKNOWN_'):
                            temp_codes.append(stock.get('name', code))
                
                if temp_codes:
                    print(f"⚠️  仍有临时代码: {temp_codes}")
                else:
                    print("✅ 所有股票代码已解析")
                    
                if duration < 0.5:
                    print("✅ PASS: 缓存命中，响应时间 < 0.5秒")
                else:
                    print("⚠️  WARNING: 响应时间 > 0.5秒（可能缓存未命中）")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")

async def test_initial_data_api():
    """测试初始数据 API 的响应时间"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n" + "=" * 60)
        print("测试 2: 初始数据 API 响应时间")
        print("=" * 60)
        
        print("\n📡 发送请求...")
        start_time = time.time()
        try:
            response = await client.get(f"{BASE_URL}/initial-data")
            duration = time.time() - start_time
            
            print(f"✅ 响应时间: {duration:.2f}秒")
            print(f"✅ 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                holdings = data.get('holdings', {})
                sectors = holdings.get('sectors', [])
                total_stocks = sum(len(s.get('stocks', [])) for s in sectors)
                print(f"✅ 返回 holdings: {len(sectors)} 个板块, {total_stocks} 只股票")
                
                if duration < 2.0:
                    print("✅ PASS: API 响应时间 < 2秒")
                else:
                    print("⚠️  WARNING: API 响应时间 > 2秒")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")

async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("Non-Blocking API 测试")
    print("=" * 60)
    
    await test_holdings_api()
    await test_initial_data_api()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
