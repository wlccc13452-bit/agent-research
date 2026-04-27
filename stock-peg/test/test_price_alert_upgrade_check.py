"""
测试价格提醒系统升级（代码审查版）
"""
import sys
from pathlib import Path


def test_card_upgrade():
    """测试配置卡片升级"""
    print("\n" + "="*60)
    print("测试 1: 配置卡片升级")
    print("="*60)
    
    card_file = Path(__file__).parent.parent / "backend" / "services" / "feishu_card_service.py"
    
    with open(card_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查新增字段
    checks = [
        ('"name": "up_alert_pct"', "上涨预警%字段"),
        ('"name": "down_alert_pct"', "下跌预警%字段"),
        ('"input_type": "number"', "数字输入类型"),
        ('"label": "上涨预警%"', "上涨预警%标签"),
        ('"label": "下跌预警%"', "下跌预警%标签"),
    ]
    
    passed = 0
    for pattern, description in checks:
        if pattern in content:
            print(f"  [PASS] {description}")
            passed += 1
        else:
            print(f"  [FAIL] 缺少: {description}")
    
    print(f"\n结果: {passed}/{len(checks)} 检查通过")
    return passed == len(checks)


def test_form_handling():
    """测试表单处理逻辑"""
    print("\n" + "="*60)
    print("测试 2: 表单处理逻辑")
    print("="*60)
    
    service_file = Path(__file__).parent.parent / "backend" / "services" / "feishu_long_connection_service.py"
    
    with open(service_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查表单字段提取
    checks = [
        ("up_alert_pct", "提取上涨预警%字段"),
        ("down_alert_pct", "提取下跌预警%字段"),
        ('form_data.get(\'up_alert_pct', "从表单获取上涨预警%"),
        ('form_data.get(\'down_alert_pct', "从表单获取下跌预警%"),
    ]
    
    passed = 0
    for pattern, description in checks:
        if pattern in content:
            print(f"  [PASS] {description}")
            passed += 1
        else:
            print(f"  [FAIL] 缺少: {description}")
    
    print(f"\n结果: {passed}/{len(checks)} 检查通过")
    return passed == len(checks)


def test_notification_card():
    """测试预警通知卡片升级"""
    print("\n" + "="*60)
    print("测试 3: 预警通知卡片升级")
    print("="*60)
    
    monitor_file = Path(__file__).parent.parent / "backend" / "services" / "price_alert_monitor_service.py"
    
    with open(monitor_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查动态颜色和价格对比
    checks = [
        ('header_color = "red"', "上涨使用红色"),
        ('header_color = "green"', "下跌使用绿色"),
        ('价格对比', "包含价格对比字段"),
        ('参考价格', "包含参考价格字段"),
    ]
    
    passed = 0
    for pattern, description in checks:
        if pattern in content:
            print(f"  [PASS] {description}")
            passed += 1
        else:
            print(f"  [FAIL] 缺少: {description}")
    
    print(f"\n结果: {passed}/{len(checks)} 检查通过")
    return passed == len(checks)


def test_scheduler_config():
    """测试调度器配置"""
    print("\n" + "="*60)
    print("测试 4: 调度器交易时段配置")
    print("="*60)
    
    scheduler_file = Path(__file__).parent.parent / "backend" / "services" / "scheduler.py"
    
    with open(scheduler_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查交易时段配置
    checks = [
        ("hour='9-10', minute='30-59'", "上午盘前半段 (9:30-10:59)"),
        ("hour='11', minute='0-30'", "上午盘后半段 (11:00-11:30)"),
        ("hour='13-14', minute='*'", "下午盘前半段 (13:00-14:59)"),
        ("hour='15', minute='0'", "下午盘最后检查 (15:00)"),
    ]
    
    passed = 0
    for pattern, description in checks:
        if pattern in content:
            print(f"  [PASS] {description}")
            passed += 1
        else:
            print(f"  [FAIL] 缺少: {description}")
    
    print(f"\n结果: {passed}/{len(checks)} 检查通过")
    return passed == len(checks)


def test_state_management():
    """测试状态管理逻辑"""
    print("\n" + "="*60)
    print("测试 5: 状态管理逻辑")
    print("="*60)
    
    monitor_file = Path(__file__).parent.parent / "backend" / "services" / "price_alert_monitor_service.py"
    
    with open(monitor_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 验证状态管理逻辑
    checks = [
        ("is_triggered = 1", "触发后设置 is_triggered = 1"),
        ("is_triggered == 0", "查询时过滤已触发的预警"),
        ("triggered_at =", "记录触发时间"),
        ("trigger_reason =", "记录触发原因"),
    ]
    
    passed = 0
    for pattern, description in checks:
        if pattern in content:
            print(f"  [PASS] {description}")
            passed += 1
        else:
            print(f"  [FAIL] 缺少: {description}")
    
    print(f"\n结果: {passed}/{len(checks)} 检查通过")
    return passed == len(checks)


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("价格提醒系统升级测试（代码审查版）")
    print("="*60)
    
    tests = [
        ("配置卡片升级", test_card_upgrade),
        ("表单处理逻辑", test_form_handling),
        ("预警通知卡片", test_notification_card),
        ("调度器交易时段配置", test_scheduler_config),
        ("状态管理逻辑", test_state_management),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "PASS" if result else "FAIL", None))
        except Exception as e:
            results.append((name, "FAIL", str(e)))
            import traceback
            traceback.print_exc()
    
    # 打印测试结果汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, status, error in results:
        print(f"[{status}] {name}")
        if error:
            print(f"  错误: {error}")
    
    passed = sum(1 for _, status, _ in results if status == "PASS")
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    print("="*60)
    
    if passed == total:
        print("\n[SUCCESS] 所有升级功能已完成并验证通过！")
    else:
        print(f"\n[WARNING] 还有 {total - passed} 个测试未通过")


if __name__ == "__main__":
    main()
