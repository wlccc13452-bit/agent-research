"""测试初始数据API的响应时间

验证点：
1. /api/holdings 是否立即返回（<1秒）
2. /api/indices/quotes 是否立即返回（<1秒）
3. /api/daily-watchlist/summary 是否立即返回（<1秒）
4. 整体 initial-data 加载时间是否合理（<3秒）
"""
import asyncio
import time
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_api_response_time(url: str, name: str, timeout: float = 1.0):
    """测试单个API的响应时间"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"\n📡 测试 {name}...")
        start_time = time.time()
        try:
            response = await client.get(url)
            duration = time.time() - start_time
            
            print(f"✅ 响应时间: {duration:.2f}秒")
            print(f"✅ 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                data_size = len(json.dumps(data))
                print(f"✅ 数据大小: {data_size} 字节")
                
                if duration < timeout:
                    print(f"✅ PASS: API 响应时间 < {timeout}秒")
                    return True, duration
                else:
                    print(f"❌ FAIL: API 响应时间 > {timeout}秒")
                    return False, duration
            else:
                print(f"❌ 请求失败: {response.status_code}")
                return False, duration
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            return False, 999

async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("初始数据API性能测试")
    print("=" * 60)
    
    # 测试各个API的响应时间
    results = []
    
    # 1. Holdings API
    success, duration = await test_api_response_time(
        f"{BASE_URL}/holdings/",
        "Holdings API",
        timeout=1.0
    )
    results.append(('Holdings', success, duration))
    
    # 等待一下，让后台任务执行
    await asyncio.sleep(1)
    
    # 2. Indices Quotes API
    success, duration = await test_api_response_time(
        f"{BASE_URL}/stocks/indices/quotes",
        "Indices Quotes API",
        timeout=1.0
    )
    results.append(('Indices Quotes', success, duration))
    
    # 3. Watchlist Summary API
    success, duration = await test_api_response_time(
        f"{BASE_URL}/daily-watchlist/summary?include_archived=false&limit=10",
        "Watchlist Summary API",
        timeout=1.0
    )
    results.append(('Watchlist Summary', success, duration))
    
    # 4. 整体 initial-data 加载测试
    print("\n" + "=" * 60)
    print("测试整体 initial-data 加载")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n📡 并行加载所有初始数据...")
        start_time = time.time()
        
        try:
            # 并行请求所有API
            holdings_task = client.get(f"{BASE_URL}/holdings/")
            indices_task = client.get(f"{BASE_URL}/stocks/indices/quotes")
            watchlist_task = client.get(f"{BASE_URL}/daily-watchlist/summary?include_archived=false&limit=10")
            
            responses = await asyncio.gather(
                holdings_task,
                indices_task,
                watchlist_task,
                return_exceptions=True
            )
            
            total_duration = time.time() - start_time
            print(f"\n✅ 整体加载时间: {total_duration:.2f}秒")
            
            # 检查各个响应
            holdings_ok = isinstance(responses[0], httpx.Response) and responses[0].status_code == 200
            indices_ok = isinstance(responses[1], httpx.Response) and responses[1].status_code == 200
            watchlist_ok = isinstance(responses[2], httpx.Response) and responses[2].status_code == 200
            
            print(f"Holdings: {'✅ 成功' if holdings_ok else '❌ 失败'}")
            print(f"Indices: {'✅ 成功' if indices_ok else '❌ 失败'}")
            print(f"Watchlist: {'✅ 成功' if watchlist_ok else '❌ 失败'}")
            
            if total_duration < 3.0:
                print(f"\n✅ PASS: 整体加载时间 < 3秒")
            else:
                print(f"\n⚠️  WARNING: 整体加载时间 > 3秒")
                
        except Exception as e:
            print(f"❌ 加载异常: {str(e)}")
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    all_passed = all(success for _, success, _ in results)
    
    print("\nAPI响应时间:")
    for name, success, duration in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {name}: {status} ({duration:.2f}秒)")
    
    if all_passed:
        print("\n✅ 所有API都通过了非阻塞测试！")
    else:
        print("\n⚠️  部分API未能通过非阻塞测试，需要进一步优化")

if __name__ == "__main__":
    asyncio.run(main())
