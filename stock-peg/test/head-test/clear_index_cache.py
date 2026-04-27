
import sys
import asyncio
from pathlib import Path

# 添加 backend 到 Python 路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from services.extended_cache import index_list_cache

async def clear_cache():
    print("=" * 80)
    print("清理指数缓存")
    print("=" * 80)
    
    cache_key = "cn_indices_list_local"
    await index_list_cache.delete(cache_key)
    print(f"✅ 缓存 {cache_key} 已清理")

if __name__ == "__main__":
    asyncio.run(clear_cache())
