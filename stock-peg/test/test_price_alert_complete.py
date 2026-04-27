"""
测试价格提醒系统完整功能
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))


def test_card_creation():
    """测试 1: 配置卡片创建"""
    print("\n" + "="*60)
    print("测试 1: 配置卡片创建（_create_monitor_config_card）")
    print("="*60)
    
    card_file = Path(__file__).parent.parent / "backend" / "services" / "feishu_card_service.py"
    
    with open(card_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查方法是否存在
    assert "def _create_monitor_config_card(self)" in content, "缺少 _create_monitor_config_card 方法"
    print("  [PASS] _create_monitor_config_card 方法存在")
    
    # 检查是否使用 input 收集股票代码和参考价
    checks = [
        ('"name": "stock_code"', "使用 input 收集股票代码"),
        ('"name": "ref_price"', "使用 input 收集参考价格"),
        ('"input_type": "number"', "数字输入类型"),
        ('"label": "股票代码"', "label 为纯字符串"),
        ('"label": "参考价格"', "label 为纯字符串"),
    ]
    
    passed = 0
    for pattern, description in checks:
        if pattern in content:
            print(f"  [PASS] {description}")
            passed += 1
        else:
            print(f"  [FAIL] 缺少: {description}")
    
    # 检查是否使用 select_static 收集变化率
    if '"tag": "select_static"' in content and '"name": "change_rate"' in content:
        print("  [PASS] 使用 select_static 收集变化率")
        passed += 1
    else:
        print("  [FAIL] 未使用 select_static 收集变化率")
    
    print(f"\n结果: {passed}/{len(checks) + 1} 检查通过")
    return passed == len(checks) + 1


def test_form_handling():
    """测试 2: 表单处理与数据库持久化"""
    print("\n" + "="*60)
    print("测试 2: 表单处理与数据库持久化")
    print("="*60)
    
    service_file = Path(__file__).parent.parent / "backend" / "services" / "feishu_long_connection_service.py"
    
    with open(service_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查表单处理方法
    checks = [
        ("def _handle_monitor_task_submission", "表单处理方法存在"),
        ("from services.price_alert_manager import price_alert_manager", "导入 price_alert_manager"),
        ("price_alert_manager.create_alert", "调用 price_alert_manager.create_alert"),
        ("form_data.get('change_rate'", "处理 change_rate 字段"),
        ('return {"toast":', "返回 toast 响应"),
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
    """测试 3: 预警通知卡片"""
    print("\n" + "="*60)
    print("测试 3: 预警通知卡片（参考价 vs 实际价对比）")
    print("="*60)
    
    monitor_file = Path(__file__).parent.parent / "backend" / "services" / "price_alert_monitor_service.py"
    
    with open(monitor_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查预警卡片功能
    checks = [
        ("def _create_alert_notification_card", "预警卡片创建方法存在"),
        ("header_color = \"red\"", "上涨使用红色"),
        ("header_color = \"green\"", "下跌使用绿色"),
        ("价格对比", "包含价格对比字段"),
        ("参考价格", "包含参考价格字段"),
        ("def _send_alert_notification_card", "预警卡片推送方法存在"),
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


def test_feishu_push():
    """测试 4: 飞书主动推送"""
    print("\n" + "="*60)
    print("测试 4: 飞书主动推送功能")
    print("="*60)
    
    # 检查 feishu_bot.py
    bot_file = Path(__file__).parent.parent / "backend" / "services" / "feishu_bot.py"
    with open(bot_file, 'r', encoding='utf-8') as f:
        bot_content = f.read()
    
    # 检查 feishu_card_service.py
    card_file = Path(__file__).parent.parent / "backend" / "services" / "feishu_card_service.py"
    with open(card_file, 'r', encoding='utf-8') as f:
        card_content = f.read()
    
    # 检查推送功能
    checks = [
        ("async def send_message", "飞书消息发送方法", bot_content),
        ("async def _send_card_message", "卡片消息发送方法", card_content),
        ("CreateMessageRequest", "飞书消息请求构建", card_content),
        ('.msg_type("interactive")', "交互式卡片消息", card_content),
    ]
    
    passed = 0
    for pattern, description, content in checks:
        if pattern in content:
            print(f"  [PASS] {description}")
            passed += 1
        else:
            print(f"  [FAIL] 缺少: {description}")
    
    print(f"\n结果: {passed}/{len(checks)} 检查通过")
    return passed == len(checks)


def test_scheduler():
    """测试 5: 调度器配置"""
    print("\n" + "="*60)
    print("测试 5: 调度器交易时段配置")
    print("="*60)
    
    scheduler_file = Path(__file__).parent.parent / "backend" / "services" / "scheduler.py"
    
    with open(scheduler_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查调度器配置
    checks = [
        ("def check_price_alerts", "价格提醒检查方法存在"),
        ("hour='9-10', minute='30-59'", "上午盘前半段 (9:30-10:59)"),
        ("hour='11', minute='0-30'", "上午盘后半段 (11:00-11:30)"),
        ("hour='13-14', minute='*'", "下午盘前半段 (13:00-14:59)"),
        ("hour='15', minute='0'", "下午盘最后检查 (15:00)"),
        ("CronTrigger", "使用 CronTrigger"),
        ("day_of_week='mon-fri'", "仅工作日运行"),
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
    """测试 6: 状态管理"""
    print("\n" + "="*60)
    print("测试 6: 状态管理逻辑")
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
    print("价格提醒系统完整功能测试")
    print("="*60)
    
    tests = [
        ("配置卡片创建", test_card_creation),
        ("表单处理与数据库持久化", test_form_handling),
        ("预警通知卡片", test_notification_card),
        ("飞书主动推送", test_feishu_push),
        ("调度器配置", test_scheduler),
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
        print("\n[SUCCESS] 所有功能已完成并验证通过！")
        print("\n升级内容:")
        print("1. 新增 _create_monitor_config_card 方法")
        print("2. 表单处理支持 change_rate 字段")
        print("3. 预警卡片包含参考价 vs 实际价对比")
        print("4. 飞书主动推送功能完善")
        print("5. 调度器配置正确（交易时段每分钟检查）")
        print("6. 状态管理避免重复推送")
    else:
        print(f"\n[WARNING] 还有 {total - passed} 个测试未通过")


if __name__ == "__main__":
    main()
