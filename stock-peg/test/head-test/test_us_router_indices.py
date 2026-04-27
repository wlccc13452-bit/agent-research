
import sys
import asyncio
from pathlib import Path
from pprint import pprint

# 添加 backend 到 Python 路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from database.session import async_session_maker
from routers.us_market import get_us_market_indices

async def test_get_us_indices():
    print("=" * 80)
    print("测试 get_us_market_indices 接口逻辑")
    print("=" * 80)
    
    async with async_session_maker() as db:
        response = await get_us_market_indices(db)
        
        print(f"数据源: {response.get('metadata', {}).get('data_source')}")
        print(f"是否正在更新: {response.get('metadata', {}).get('is_updating')}")
        
        indices = response.get('data', {})
        print(f"获取到 {len(indices)} 个美股指数:")
        
        for symbol, data in indices.items():
            print(f"  - {data.get('name')} ({symbol}): {data.get('previous_close')} ({data.get('change_pct')}%)")

if __name__ == "__main__":
    asyncio.run(test_get_us_indices())
