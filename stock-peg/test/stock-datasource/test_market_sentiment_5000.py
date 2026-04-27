"""测试市场情绪API - 验证数据质量要求"""
import asyncio
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, '.')

async def test_api():
    print("=" * 60)
    print("Testing Market Sentiment API (5000+ requirement)")
    print("=" * 60)
    
    from routers.market_data import get_market_sentiment
    from database.session import get_db
    
    print("\nTesting API with insufficient data (< 5000 stocks)...")
    
    async for db in get_db():
        try:
            result = await get_market_sentiment(db)
            # 如果成功返回，检查数据量
            if result.get('total_count', 0) >= 5000:
                print(f"[PASS] API returned valid data: {result['total_count']} stocks")
                print(f"  Data source: {result.get('data_source')}")
            else:
                print(f"[FAIL] API returned insufficient data: {result['total_count']} stocks")
                print(f"  ERROR: Should have returned HTTP 503 instead!")
        except Exception as e:
            error_type = type(e).__name__
            if 'HTTPException' in error_type or '503' in str(e):
                print(f"[PASS] API correctly rejected insufficient data")
                print(f"  Error: {str(e)[:200]}")
            else:
                print(f"[FAIL] Unexpected error: {str(e)}")
        break
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(test_api())
