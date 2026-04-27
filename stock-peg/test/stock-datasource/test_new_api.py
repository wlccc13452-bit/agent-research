"""
直接测试新的市场情绪API
"""
import sys
import os
import asyncio

# 设置 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加 backend 到路径
sys.path.insert(0, os.path.dirname(__file__))

from services.akshare_service import akshare_service

async def test():
    print("=" * 60)
    print("测试新的市场情绪API")
    print("=" * 60)
    
    # 测试 AKShare 服务
    print(f"\nAKShare 可用: {akshare_service.available}")
    
    # 调用新的 get_market_sentiment
    print("\n调用 get_market_sentiment()...")
    result = await akshare_service.get_market_sentiment()
    
    if result:
        print(f"\n✓ 成功获取数据!")
        print(f"  总股票数: {result.get('total_count')}")
        print(f"  数据源: {result.get('data_source')}")
        print(f"  数据质量: {result.get('data_quality')}")
        print(f"\n市场统计:")
        print(f"  上涨: {result.get('up_count')}")
        print(f"  下跌: {result.get('down_count')}")
        print(f"  平盘: {result.get('flat_count')}")
        print(f"  涨停: {result.get('limit_up')}")
        print(f"  跌停: {result.get('limit_down')}")
        print(f"  市场宽度: {result.get('market_breadth')}%")
        print(f"  平均涨跌: {result.get('avg_change_pct')}%")
        
        # 飘亮地显示 JSON
        import json
        print(f"\n完整JSON:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n✗ 获取数据失败")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test())
