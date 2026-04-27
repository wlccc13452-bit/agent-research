#!/usr/bin/env python3
"""测试股票名称解析功能"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from services.akshare_service import akshare_service


async def test_stock_name_resolve():
    """测试股票名称解析"""
    print("=" * 100)
    print("Testing stock name resolution")
    print("=" * 100)

    # 测试不同的股票名称
    test_names = [
        "中国银行",      # 常见股票
        "平安银行",      # 常见股票
        "南山铝业",      # 自持股票
        "贵州茅台",      # 高价股
        "不存在股票",    # 不存在的股票
    ]

    for stock_name in test_names:
        print(f"\n[Testing] Stock name: '{stock_name}'")
        print("-" * 80)

        try:
            if akshare_service.available:
                stock_code = await akshare_service.search_stock_by_name(stock_name)

                if stock_code:
                    print(f"  [OK] Resolved to stock code: {stock_code}")
                else:
                    print(f"  [FAIL] Could not resolve stock code")
            else:
                print(f"  [ERROR] Akshare service not available")
        except Exception as e:
            print(f"  [ERROR] Exception: {e}")

    print("\n" + "=" * 100)
    print("Test completed")
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(test_stock_name_resolve())
