#!/usr/bin/env python3
"""测试API路由是否正确响应"""
import asyncio
import httpx
import time

async def test_routes():
    """测试关键API路由"""
    base_url = "http://localhost:8000"
    
    tests = [
        ("/api/holdings/", "自持股票"),
        ("/api/daily-watchlist/summary?limit=10", "热点关注"),
        ("/api/stocks/indices/quotes", "指数行情"),
    ]
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for endpoint, name in tests:
            try:
                start = time.time()
                response = await client.get(f"{base_url}{endpoint}")
                elapsed = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[OK] {name}: {response.status_code} ({elapsed:.0f}ms)")
                    if endpoint == "/api/holdings/":
                        sectors = data.get('sectors', [])
                        print(f"   - 板块数: {len(sectors)}")
                        total_stocks = sum(len(s.get('stocks', [])) for s in sectors)
                        print(f"   - 股票数: {total_stocks}")
                    elif endpoint == "/api/daily-watchlist/summary":
                        dates = data.get('dates', [])
                        print(f"   - 日期数: {len(dates)}")
                else:
                    print(f"[ERROR] {name}: {response.status_code} - {response.text[:100]}")
            except httpx.ConnectError:
                print(f"[ERROR] {name}: 服务器未启动 (Connection refused)")
                break
            except Exception as e:
                print(f"[ERROR] {name}: {type(e).__name__} - {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("API 路由测试")
    print("=" * 60)
    asyncio.run(test_routes())
