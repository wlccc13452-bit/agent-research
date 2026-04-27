"""
测试交易时段配置API
"""
import configparser
from pathlib import Path
from pydantic import BaseModel
from typing import List

# 配置文件路径
backend_dir = Path(__file__).parent.parent / "backend"
CONFIG_DIR = backend_dir / "config"
TRADING_HOURS_FILE = CONFIG_DIR / "trading_hours.ini"


class TradingHoursConfig(BaseModel):
    """交易时段配置模型"""
    morning_session_start: str
    morning_session_end: str
    afternoon_session_start: str
    afternoon_session_end: str
    trading_days: str
    price_alert_check_interval: int
    enable_price_alert_monitoring: bool
    auto_stop_after_trigger: bool
    market_sentiment_update_interval: int


def read_trading_hours_config() -> TradingHoursConfig:
    """读取交易时段配置文件"""
    try:
        if not TRADING_HOURS_FILE.exists():
            raise FileNotFoundError(f"配置文件不存在: {TRADING_HOURS_FILE}")
        
        config = configparser.ConfigParser()
        config.read(TRADING_HOURS_FILE, encoding='utf-8')
        
        return TradingHoursConfig(
            morning_session_start=config.get('trading_hours', 'morning_session_start', fallback='09:30'),
            morning_session_end=config.get('trading_hours', 'morning_session_end', fallback='11:30'),
            afternoon_session_start=config.get('trading_hours', 'afternoon_session_start', fallback='13:00'),
            afternoon_session_end=config.get('trading_hours', 'afternoon_session_end', fallback='15:00'),
            trading_days=config.get('trading_hours', 'trading_days', fallback='1,2,3,4,5'),
            price_alert_check_interval=config.getint('trading_hours', 'price_alert_check_interval', fallback=1),
            enable_price_alert_monitoring=config.getboolean('monitor_settings', 'enable_price_alert_monitoring', fallback=True),
            auto_stop_after_trigger=config.getboolean('monitor_settings', 'auto_stop_after_trigger', fallback=True),
            market_sentiment_update_interval=config.getint('monitor_settings', 'market_sentiment_update_interval', fallback=5)
        )
    except Exception as e:
        raise Exception(f"读取交易时段配置失败: {str(e)}")


def write_trading_hours_config(trading_config: TradingHoursConfig) -> bool:
    """写入交易时段配置文件"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # 写入时保留注释
        with open(TRADING_HOURS_FILE, 'w', encoding='utf-8') as f:
            f.write("[trading_hours]\n")
            f.write("# ========================================\n")
            f.write("# A股交易时段配置\n")
            f.write("# ========================================\n")
            f.write("# 说明：\n")
            f.write("# - 交易时段格式：HH:MM-HH:MM（24小时制）\n")
            f.write("# - 支持多个时段，用逗号分隔\n")
            f.write("# - 配置修改后需重启后端服务生效\n")
            f.write("# - 前端UI修改会自动更新此文件\n\n")
            f.write("# 上午盘交易时段\n")
            f.write(f"morning_session_start = {trading_config.morning_session_start}\n")
            f.write(f"morning_session_end = {trading_config.morning_session_end}\n\n")
            f.write("# 下午盘交易时段\n")
            f.write(f"afternoon_session_start = {trading_config.afternoon_session_start}\n")
            f.write(f"afternoon_session_end = {trading_config.afternoon_session_end}\n\n")
            f.write("# 交易日配置（周几交易）\n")
            f.write("# 1=周一, 2=周二, ..., 5=周五, 6=周六, 7=周日\n")
            f.write("# 示例：1,2,3,4,5 表示周一到周五\n")
            f.write(f"trading_days = {trading_config.trading_days}\n\n")
            f.write("# 价格提醒检查频率（分钟）\n")
            f.write("# 建议值：1-5分钟\n")
            f.write(f"price_alert_check_interval = {trading_config.price_alert_check_interval}\n\n")
            f.write("[monitor_settings]\n")
            f.write("# ========================================\n")
            f.write("# 监控设置\n")
            f.write("# ========================================\n\n")
            f.write("# 是否启用价格提醒监控\n")
            f.write(f"enable_price_alert_monitoring = {str(trading_config.enable_price_alert_monitoring).lower()}\n\n")
            f.write("# 预警触发后是否自动停止监控（避免重复推送）\n")
            f.write(f"auto_stop_after_trigger = {str(trading_config.auto_stop_after_trigger).lower()}\n\n")
            f.write("# 市场情绪数据更新频率（分钟）\n")
            f.write(f"market_sentiment_update_interval = {trading_config.market_sentiment_update_interval}\n")
        
        return True
    except Exception as e:
        print(f"写入交易时段配置失败: {str(e)}")
        return False

def test_read_config():
    """测试读取配置"""
    print("=" * 60)
    print("测试1: 读取交易时段配置")
    print("=" * 60)
    
    config = read_trading_hours_config()
    print(f"[OK] 读取成功")
    print(f"  上午盘: {config.morning_session_start} - {config.morning_session_end}")
    print(f"  下午盘: {config.afternoon_session_start} - {config.afternoon_session_end}")
    print(f"  交易日: {config.trading_days}")
    print(f"  价格提醒检查间隔: {config.price_alert_check_interval}分钟")
    print(f"  启用价格提醒监控: {config.enable_price_alert_monitoring}")
    print(f"  自动停止: {config.auto_stop_after_trigger}")
    print(f"  市场情绪更新间隔: {config.market_sentiment_update_interval}分钟")
    print()

def test_write_config():
    """测试写入配置"""
    print("=" * 60)
    print("测试2: 写入交易时段配置")
    print("=" * 60)
    
    # 读取当前配置
    config = read_trading_hours_config()
    
    # 修改配置
    original_interval = config.price_alert_check_interval
    config.price_alert_check_interval = 2  # 修改为2分钟
    
    # 写入配置
    success = write_trading_hours_config(config)
    
    if success:
        print("[OK] 写入成功")
        
        # 重新读取验证
        new_config = read_trading_hours_config()
        if new_config.price_alert_check_interval == 2:
            print("[OK] 验证成功: 配置已更新")
        else:
            print("[FAIL] 验证失败: 配置未正确更新")
        
        # 恢复原配置
        config.price_alert_check_interval = original_interval
        write_trading_hours_config(config)
        print("[OK] 已恢复原配置")
    else:
        print("[FAIL] 写入失败")
    print()

def test_config_file():
    """测试配置文件"""
    print("=" * 60)
    print("测试3: 检查配置文件")
    print("=" * 60)
    
    config_file = backend_dir / "config" / "trading_hours.ini"
    
    if config_file.exists():
        print(f"[OK] 配置文件存在: {config_file}")
        print()
        print("文件内容:")
        print("-" * 60)
        with open(config_file, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print(f"[FAIL] 配置文件不存在: {config_file}")
    print()

if __name__ == "__main__":
    try:
        test_read_config()
        test_write_config()
        test_config_file()
        
        print("=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
