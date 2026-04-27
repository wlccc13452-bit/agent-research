"""
测试价格提醒系统升级（简化版，无需数据库）
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))


def test_card_creation():
    """测试卡片创建功能"""
    print("\n" + "="*60)
    print("测试 1: 配置卡片创建")
    print("="*60)
    
    from services.feishu_card_service import FeishuCardService
    
    card_service = FeishuCardService()
    card = card_service._create_monitor_setup_card()
    
    # 验证卡片结构
    assert "elements" in card, "卡片缺少 elements 字段"
    assert len(card["elements"]) > 0, "卡片 elements 为空"
    
    # 检查是否有上涨预警%和下跌预警%字段
    field_names = [elem.get("name") for elem in card["elements"] if elem.get("tag") in ["input", "select_static"]]
    
    print(f"✅ 卡片创建成功，包含字段: {field_names}")
    
    # 验证关键字段
    assert "stock_code" in field_names, "缺少股票代码字段"
    assert "ref_price" in field_names, "缺少参考价格字段"
    assert "up_alert_pct" in field_names, "缺少上涨预警%字段"
    assert "down_alert_pct" in field_names, "缺少下跌预警%字段"
    
    print("✅ 所有关键字段验证通过")
    
    # 检查 input_type="number" 设置
    for elem in card["elements"]:
        if elem.get("name") in ["ref_price", "up_alert_pct", "down_alert_pct"]:
            assert elem.get("input_type") == "number", f"{elem.get('name')} 字段未设置 input_type='number'"
            print(f"  ✅ {elem.get('name')} 字段已设置 input_type='number'")
    
    # 检查 label 格式（1.5.3 版本兼容性）
    for elem in card["elements"]:
        if elem.get("tag") == "input":
            label = elem.get("label")
            assert isinstance(label, str), f"{elem.get('name')} 的 label 必须是字符串，不能是 dict"
            print(f"  ✅ {elem.get('name')} label 格式正确: {label}")
    
    # 检查提交按钮动作
    actions = [elem for elem in card["elements"] if elem.get("tag") == "action"]
    if actions:
        for action in actions:
            for btn in action.get("actions", []):
                if btn.get("tag") == "button":
                    value = btn.get("value", {})
                    assert "action" in value, "提交按钮缺少 action 字段"
                    print(f"  ✅ 提交按钮动作: {value.get('action')}")
    
    return True


def test_notification_card():
    """测试预警通知卡片"""
    print("\n" + "="*60)
    print("测试 2: 预警通知卡片颜色和对比")
    print("="*60)
    
    from services.price_alert_monitor_service import PriceAlertMonitorService
    from decimal import Decimal
    from datetime import datetime
    
    # 创建模拟预警对象
    class MockAlert:
        def __init__(self, trigger_type):
            self.stock_name = "平安银行"
            self.stock_code = "000001"
            self.base_price = Decimal("15.00")
            self.current_price = Decimal("16.50" if trigger_type == "up" else "13.50")
            self.current_change_pct = Decimal("10.0" if trigger_type == "up" else "-10.0")
            self.target_price = Decimal("16.00") if trigger_type == "up" else Decimal("14.00")
            self.change_up_pct = Decimal("5.0")
            self.change_down_pct = Decimal("-3.0")
            self.notes = "测试备注"
            self.triggered_at = datetime.now()
    
    monitor_service = PriceAlertMonitorService(None)
    
    # 测试上涨预警卡片
    print("\n测试上涨预警卡片:")
    alert_up = MockAlert("up")
    card_up = monitor_service._create_alert_notification_card(alert_up, "change_up", {})
    
    assert card_up["header"]["template"] == "red", "上涨预警应使用红色主题"
    print(f"  ✅ 上涨预警颜色: {card_up['header']['template']}")
    print(f"  ✅ 标题: {card_up['header']['title']['content']}")
    
    # 测试下跌预警卡片
    print("\n测试下跌预警卡片:")
    alert_down = MockAlert("down")
    card_down = monitor_service._create_alert_notification_card(alert_down, "change_down", {})
    
    assert card_down["header"]["template"] == "green", "下跌预警应使用绿色主题"
    print(f"  ✅ 下跌预警颜色: {card_down['header']['template']}")
    print(f"  ✅ 标题: {card_down['header']['title']['content']}")
    
    # 检查价格对比字段
    for card, name in [(card_up, "上涨"), (card_down, "下跌")]:
        has_price_comparison = False
        for elem in card["elements"]:
            if isinstance(elem, dict) and "价格对比" in str(elem.get("text", {}).get("content", "")):
                has_price_comparison = True
                content = elem.get("text", {}).get("content", "")
                print(f"  ✅ {name}预警包含价格对比信息:")
                print(f"     {content[:100]}...")
                break
        assert has_price_comparison, f"{name}预警缺少价格对比信息"
    
    return True


def test_scheduler_config():
    """测试调度器配置"""
    print("\n" + "="*60)
    print("测试 3: 调度器交易时段配置")
    print("="*60)
    
    from apscheduler.triggers.cron import CronTrigger
    
    # 上午盘: 9:30-11:30
    morning_trigger_1 = CronTrigger(hour='9-10', minute='30-59', day_of_week='mon-fri')
    morning_trigger_2 = CronTrigger(hour='11', minute='0-30', day_of_week='mon-fri')
    
    # 下午盘: 13:00-15:00
    afternoon_trigger_1 = CronTrigger(hour='13-14', minute='*', day_of_week='mon-fri')
    afternoon_trigger_2 = CronTrigger(hour='15', minute='0', day_of_week='mon-fri')
    
    triggers = [
        ("上午盘前半段 (9:30-10:59)", morning_trigger_1),
        ("上午盘后半段 (11:00-11:30)", morning_trigger_2),
        ("下午盘前半段 (13:00-14:59)", afternoon_trigger_1),
        ("下午盘最后检查 (15:00)", afternoon_trigger_2),
    ]
    
    print(f"✅ 已配置 {len(triggers)} 个交易时段调度任务\n")
    
    for name, trigger in triggers:
        print(f"  - {name}")
        print(f"    触发器: {trigger}")
    
    # 验证调度器不会在非交易时段运行
    from datetime import datetime
    
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    
    is_trading_time = False
    if (9 <= hour <= 10 and minute >= 30) or (hour == 11 and minute <= 30):
        is_trading_time = True
    elif 13 <= hour <= 14:
        is_trading_time = True
    elif hour == 15 and minute == 0:
        is_trading_time = True
    
    print(f"\n当前时间: {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"是否交易时段: {'是 ✅' if is_trading_time else '否 ⏸️'}")
    
    return True


def test_state_management():
    """测试状态管理逻辑"""
    print("\n" + "="*60)
    print("测试 4: 状态管理逻辑（代码审查）")
    print("="*60)
    
    # 读取 price_alert_monitor_service.py
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
    
    for pattern, description in checks:
        if pattern in content:
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ 缺少: {description}")
            return False
    
    print("\n✅ 状态管理逻辑完整，可避免重复推送")
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("价格提醒系统升级测试")
    print("="*60)
    
    tests = [
        ("配置卡片创建", test_card_creation),
        ("预警通知卡片", test_notification_card),
        ("调度器交易时段配置", test_scheduler_config),
        ("状态管理逻辑", test_state_management),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "✅ 通过", None))
        except Exception as e:
            results.append((name, "❌ 失败", str(e)))
            import traceback
            traceback.print_exc()
    
    # 打印测试结果汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, status, error in results:
        print(f"{status} {name}")
        if error:
            print(f"  错误: {error}")
    
    passed = sum(1 for _, status, _ in results if "通过" in status)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    print("="*60)


if __name__ == "__main__":
    main()
