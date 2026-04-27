#!/usr/bin/env python3
"""测试持仓股票基准价信息获取功能"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from services.holdings_manager import HoldingsManager


def test_get_holdings_target_price():
    """测试获取持仓股票基准价信息"""
    print("=" * 100)
    print("Testing HoldingsManager.get_holdings_target_price()")
    print("=" * 100)
    
    holdings_manager = HoldingsManager()
    
    # 测试股票
    test_stocks = [
        "南山铝业",    # 有基准价
        "雅化集团",    # 有基准价
        "中国神华",    # 无基准价
        "隆基绿能",    # 无基准价
    ]
    
    for stock_name in test_stocks:
        print(f"\n[Testing] {stock_name}")
        result = holdings_manager.get_holdings_target_price(stock_name)
        
        if result:
            print(f"  [OK] Found target price data:")
            print(f"    Target price: {result['target_price']}")
            print(f"    Change up pct: {result['change_up_pct']}%")
            print(f"    Change down pct: {result['change_down_pct']}%")
        else:
            print(f"  [INFO] No target price data found")
    
    print("\n" + "=" * 100)
    print("Test completed")
    print("=" * 100)


if __name__ == "__main__":
    test_get_holdings_target_price()
