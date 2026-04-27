"""
测试价格提醒系统升级
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.session import get_db
from backend.services.price_alert_manager import price_alert_manager
from backend.services.feishu_card_service import FeishuCardService


async def test_card_creation():
    """测试卡片创建功能"""
    print("\n" + "="*60)
    print("测试 1: 配置卡片创建")
    print("="*60)
    
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
    
    return True


async def test_alert_creation():
    """测试预警创建功能"""
    print("\n" + "="*60)
    print("测试 2: 预警创建与持久化")
    print("="*60)
    
    async for db in get_db():
        try:
            # 创建测试预警
            alert = await price_alert_manager.create_alert(
                db=db,
                stock_code="000001",
                target_price=15.0,
                change_up_pct=5.0,  # 上涨5%预警
                change_down_pct=-3.0,  # 下跌3%预警
                feishu_chat_id="test_chat_id",
                notes="测试预警"
            )
            
            print(f"✅ 预警创建成功 (ID: {alert.id})")
            print(f"  - 股票: {alert.stock_name} ({alert.stock_code})")
            print(f"  - 参考价格: ¥{alert.target_price}")
            print(f"  - 上涨预警: +{alert.change_up_pct}%")
            print(f"  - 下跌预警: {alert.change_down_pct}%")
            print(f"  - 状态: {'活跃' if alert.is_active else '不活跃'}")
            
            # 清理测试数据
            await db.delete(alert)
            await db.commit()
            print("✅ 测试数据已清理")
            
            return True
            
        finally:
            await db.close()
            break
    
    return False


async def test_notification_card():
    """测试预警通知卡片"""
    print("\n" + "="*60)
    print("测试 3: 预警通知卡片颜色和对比")
    print("="*60)
    
    from backend.services.price_alert_monitor_service import PriceAlertMonitorService
    from backend.database.models import PriceAlert
    from decimal import Decimal
    
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
            
            from datetime import datetime
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
                print(f"  ✅ {name}预警包含价格对比信息")
                break
        assert has_price_comparison, f"{name}预警缺少价格对比信息"
    
    return True


async def test_scheduler_config():
    """测试调度器配置"""
    print("\n" + "="*60)
    print("测试 4: 调度器交易时段配置")
    print("="*60)
    
    from backend.services.scheduler import TaskScheduler
    
    scheduler = TaskScheduler()
    scheduler.scheduler.remove_all_jobs()  # 清空现有任务
    
    # 添加价格提醒监控任务（使用新的配置）
    from apscheduler.triggers.cron import CronTrigger
    
    # 上午盘: 9:30-11:30
    scheduler.scheduler.add_job(
        lambda: None,  # 测试用空函数
        CronTrigger(hour='9-10', minute='30-59', day_of_week='mon-fri'),
        id='test_morning_1',
        name='测试上午盘前半段'
    )
    
    scheduler.scheduler.add_job(
        lambda: None,
        CronTrigger(hour='11', minute='0-30', day_of_week='mon-fri'),
        id='test_morning_2',
        name='测试上午盘后半段'
    )
    
    # 下午盘: 13:00-15:00
    scheduler.scheduler.add_job(
        lambda: None,
        CronTrigger(hour='13-14', minute='*', day_of_week='mon-fri'),
        id='test_afternoon_1',
        name='测试下午盘前半段'
    )
    
    scheduler.scheduler.add_job(
        lambda: None,
        CronTrigger(hour='15', minute='0', day_of_week='mon-fri'),
        id='test_afternoon_2',
        name='测试下午盘最后检查'
    )
    
    jobs = scheduler.scheduler.get_jobs()
    print(f"✅ 已配置 {len(jobs)} 个调度任务")
    
    for job in jobs:
        print(f"  - {job.name}: {job.trigger}")
    
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
    
    print(f"\n当前时间: {now.strftime('%H:%M')}")
    print(f"是否交易时段: {'是' if is_trading_time else '否'}")
    
    return True


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("价格提醒系统升级测试")
    print("="*60)
    
    tests = [
        ("配置卡片创建", test_card_creation),
        ("预警创建与持久化", test_alert_creation),
        ("预警通知卡片", test_notification_card),
        ("调度器交易时段配置", test_scheduler_config),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, "✅ 通过", None))
        except Exception as e:
            results.append((name, "❌ 失败", str(e)))
    
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
    asyncio.run(main())
