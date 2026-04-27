"""
测试持仓股票名称清理功能
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from services.holdings_manager import HoldingsManager

def test_read_holdings_clean():
    """测试 read_holdings() 是否清理了HTML注释"""
    manager = HoldingsManager()
    
    # 读取持仓数据
    data = manager.read_holdings()
    
    print("\n=== 测试持仓股票名称清理 ===\n")
    
    for sector in data.get('sectors', []):
        print(f"板块: {sector['name']}")
        for stock_name in sector.get('stocks', []):
            # 检查是否包含HTML注释
            has_comment = '<!--' in stock_name or '-->' in stock_name
            status = "[FAIL] Contains comment" if has_comment else "[OK] Clean"
            print(f"  {status}: {stock_name}")
    
    print("\n=== 验证结果 ===\n")
    
    # 检查所有股票名称是否都不包含HTML注释
    all_clean = True
    for sector in data.get('sectors', []):
        for stock_name in sector.get('stocks', []):
            if '<!--' in stock_name or '-->' in stock_name:
                all_clean = False
                print(f"[FAIL] Found stock with comment: {stock_name}")
    
    if all_clean:
        print("[OK] All stock names are clean, no HTML comments")
    else:
        print("[FAIL] Some stock names still contain HTML comments")
    
    return all_clean

if __name__ == "__main__":
    test_read_holdings_clean()
