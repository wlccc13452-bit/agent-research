#!/usr/bin/env python3
"""测试"中国银行"股票查询功能"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from services.stock_service import stock_service


async def test_bank_of_china_query():
    """测试中国银行股票查询"""
    print("=" * 100)
    print("Testing '中国银行' stock query")
    print("=" * 100)

    # 测试不同的输入格式
    test_inputs = [
        "中国银行",      # 中文名称
        "601988",       # 股票代码
        "sh601988",     # 带交易所前缀
    ]

    for test_input in test_inputs:
        print(f"\n[Testing] Input: '{test_input}'")
        print("-" * 80)

        try:
            # 尝试标准化股票代码
            print(f"  Step 1: Normalizing stock code...")
            normalized_code = await stock_service.normalize_stock_code(test_input)
            print(f"  [OK] Normalized to: {normalized_code}")

            # 尝试获取行情
            print(f"  Step 2: Fetching quote...")
            quote = await stock_service.get_realtime_quote(normalized_code)

            if quote:
                print(f"  [OK] Quote retrieved:")
                print(f"    Stock name: {getattr(quote, 'name', 'N/A')}")
                print(f"    Price: {getattr(quote, 'price', 'N/A')}")
                print(f"    Change pct: {getattr(quote, 'change_pct', 'N/A')}")
            else:
                print(f"  [FAIL] Quote is None")

        except Exception as e:
            print(f"  [ERROR] Exception: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 100)
    print("Test completed")
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(test_bank_of_china_query())
