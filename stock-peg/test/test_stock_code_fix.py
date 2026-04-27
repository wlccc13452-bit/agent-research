"""
测试 stock_code 提取逻辑修复

问题:
  - 原代码: stock_code = form_data.get("stock_code", "") if isinstance(form_data, dict) else action_value.get("stock_code", "")
  - 当 form_data = {} 时,逻辑错误导致 stock_code = ""

修复:
  - 优先从 action_value 获取
  - 如果为空,再从 form_data 获取
"""

def test_old_logic():
    """测试旧逻辑(错误)"""
    print("=" * 60)
    print("测试旧逻辑(错误)")
    print("=" * 60)
    
    # 模拟数据
    action_value = {
        "action": "query_stock_detail",
        "stock_code": "300378",
        "stock_name": "鼎捷数智"
    }
    form_data = {}  # 空字典
    
    # 旧逻辑
    stock_code = form_data.get("stock_code", "") if isinstance(form_data, dict) else action_value.get("stock_code", "")
    
    print(f"form_data = {form_data}")
    print(f"action_value = {action_value}")
    print(f"stock_code = '{stock_code}' (期望: '300378')")
    print(f"结果: {'[ERROR] 错误' if not stock_code else '[OK] 正确'}")
    print()


def test_new_logic():
    """测试新逻辑(正确)"""
    print("=" * 60)
    print("测试新逻辑(正确)")
    print("=" * 60)
    
    # 模拟数据
    action_value = {
        "action": "query_stock_detail",
        "stock_code": "300378",
        "stock_name": "鼎捷数智"
    }
    form_data = {}  # 空字典
    
    # 新逻辑
    stock_code = action_value.get("stock_code", "") if isinstance(action_value, dict) else ""
    if not stock_code and isinstance(form_data, dict):
        stock_code = form_data.get("stock_code", "")
    
    print(f"form_data = {form_data}")
    print(f"action_value = {action_value}")
    print(f"stock_code = '{stock_code}' (期望: '300378')")
    print(f"结果: {'[OK] 正确' if stock_code == '300378' else '[ERROR] 错误'}")
    print()


def test_form_data_fallback():
    """测试从 form_data 回退逻辑"""
    print("=" * 60)
    print("测试从 form_data 回退逻辑")
    print("=" * 60)
    
    # 模拟数据 - action_value 中没有 stock_code
    action_value = {
        "action": "query_stock",
    }
    form_data = {
        "stock_code": "000001"
    }
    
    # 新逻辑
    stock_code = action_value.get("stock_code", "") if isinstance(action_value, dict) else ""
    if not stock_code and isinstance(form_data, dict):
        stock_code = form_data.get("stock_code", "")
    
    print(f"form_data = {form_data}")
    print(f"action_value = {action_value}")
    print(f"stock_code = '{stock_code}' (期望: '000001')")
    print(f"结果: {'[OK] 正确' if stock_code == '000001' else '[ERROR] 错误'}")
    print()


def test_empty_both():
    """测试两者都为空"""
    print("=" * 60)
    print("测试两者都为空")
    print("=" * 60)
    
    # 模拟数据 - 两者都没有 stock_code
    action_value = {"action": "query_stock"}
    form_data = {}
    
    # 新逻辑
    stock_code = action_value.get("stock_code", "") if isinstance(action_value, dict) else ""
    if not stock_code and isinstance(form_data, dict):
        stock_code = form_data.get("stock_code", "")
    
    print(f"form_data = {form_data}")
    print(f"action_value = {action_value}")
    print(f"stock_code = '{stock_code}' (期望: '')")
    print(f"结果: {'[OK] 正确' if stock_code == '' else '[ERROR] 错误'}")
    print()


if __name__ == "__main__":
    test_old_logic()
    test_new_logic()
    test_form_data_fallback()
    test_empty_both()
    
    print("=" * 60)
    print("修复验证完成!")
    print("=" * 60)
