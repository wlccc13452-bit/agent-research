
import sys
import asyncio
from pathlib import Path
from pprint import pprint

# 添加 backend 到 Python 路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from database.session import async_session_maker
from routers.stock import get_cn_indices

async def test_get_cn_indices():
    print("=" * 80)
    print("测试 get_cn_indices 接口逻辑")
    print("=" * 80)
    
    async with async_session_maker() as db:
        response = await get_cn_indices(db)
        
        print(f"数据源: {response.get('metadata', {}).get('data_source')}")
        print(f"是否正在更新: {response.get('metadata', {}).get('is_updating')}")
        
        indices = response.get('data', {}).get('indices', [])
        print(f"获取到 {len(indices)} 个指数:")
        
        for idx in indices:
            print(f"  - {idx.get('name')} ({idx.get('code')}): {idx.get('price')} ({idx.get('change_pct')}%)")

if __name__ == "__main__":
    asyncio.run(test_get_cn_indices())
