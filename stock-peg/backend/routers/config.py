from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import configparser
import os
from pathlib import Path
from typing import List

router = APIRouter()

# 配置文件路径
CONFIG_DIR = Path(__file__).parent.parent / "config"
CONFIG_FILE = CONFIG_DIR / "layout.ini"
TRADING_HOURS_FILE = CONFIG_DIR / "trading_hours.ini"


class LayoutConfig(BaseModel):
    left_panel_width: int
    right_panel_width: int
    center_panel_min_width: int
    headbar_height: int
    statusbar_height: int


def ensure_config_dir():
    """确保配置目录存在"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def get_default_config() -> LayoutConfig:
    """获取默认配置"""
    return LayoutConfig(
        left_panel_width=15,
        right_panel_width=20,
        center_panel_min_width=20,
        headbar_height=56,
        statusbar_height=32
    )


def read_config() -> LayoutConfig:
    """读取配置文件"""
    try:
        if not CONFIG_FILE.exists():
            ensure_config_dir()
            return get_default_config()
        
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE, encoding='utf-8')
        
        return LayoutConfig(
            left_panel_width=config.getint('layout', 'left_panel_width', fallback=15),
            right_panel_width=config.getint('layout', 'right_panel_width', fallback=20),
            center_panel_min_width=config.getint('layout', 'center_panel_min_width', fallback=20),
            headbar_height=config.getint('layout', 'headbar_height', fallback=56),
            statusbar_height=config.getint('layout', 'statusbar_height', fallback=32)
        )
    except Exception as e:
        print(f"读取配置失败: {str(e)}")
        return get_default_config()


def write_config(layout_config: LayoutConfig):
    """写入配置文件"""
    try:
        ensure_config_dir()
        
        config = configparser.ConfigParser()
        config['layout'] = {
            'left_panel_width': str(layout_config.left_panel_width),
            'right_panel_width': str(layout_config.right_panel_width),
            'center_panel_min_width': str(layout_config.center_panel_min_width),
            'headbar_height': str(layout_config.headbar_height),
            'statusbar_height': str(layout_config.statusbar_height)
        }
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            config.write(f)
        
        return True
    except Exception as e:
        print(f"写入配置失败: {str(e)}")
        return False


import asyncio

@router.get("/layout", response_model=LayoutConfig)
async def get_layout_config():
    """获取布局配置"""
    return await asyncio.to_thread(read_config)


@router.post("/layout", response_model=LayoutConfig)
async def update_layout_config(config: LayoutConfig):
    """更新布局配置"""
    # 验证配置
    total = config.left_panel_width + config.right_panel_width
    center_width = 100 - total
    
    if center_width < config.center_panel_min_width:
        raise HTTPException(
            status_code=400, 
            detail=f"中间面板宽度不能小于{config.center_panel_min_width}%"
        )
    
    if config.left_panel_width < 10 or config.left_panel_width > 40:
        raise HTTPException(
            status_code=400,
            detail="左侧面板宽度必须在10%-40%之间"
        )
    
    if config.right_panel_width < 10 or config.right_panel_width > 40:
        raise HTTPException(
            status_code=400,
            detail="右侧面板宽度必须在10%-40%之间"
        )
    
    success = await asyncio.to_thread(write_config, config)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="保存配置失败"
        )
    
    return config


# ===== 交易时段配置 =====

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


def get_default_trading_hours() -> TradingHoursConfig:
    """获取默认交易时段配置"""
    return TradingHoursConfig(
        morning_session_start="09:30",
        morning_session_end="11:30",
        afternoon_session_start="13:00",
        afternoon_session_end="15:00",
        trading_days="1,2,3,4,5",
        price_alert_check_interval=1,
        enable_price_alert_monitoring=True,
        auto_stop_after_trigger=True,
        market_sentiment_update_interval=5
    )


def read_trading_hours_config() -> TradingHoursConfig:
    """读取交易时段配置文件"""
    try:
        if not TRADING_HOURS_FILE.exists():
            ensure_config_dir()
            return get_default_trading_hours()
        
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
        print(f"读取交易时段配置失败: {str(e)}")
        return get_default_trading_hours()


def write_trading_hours_config(trading_config: TradingHoursConfig):
    """写入交易时段配置文件"""
    try:
        ensure_config_dir()
        
        config = configparser.ConfigParser()
        
        # [trading_hours] section
        config['trading_hours'] = {
            'morning_session_start': trading_config.morning_session_start,
            'morning_session_end': trading_config.morning_session_end,
            'afternoon_session_start': trading_config.afternoon_session_start,
            'afternoon_session_end': trading_config.afternoon_session_end,
            'trading_days': trading_config.trading_days,
            'price_alert_check_interval': str(trading_config.price_alert_check_interval)
        }
        
        # [monitor_settings] section
        config['monitor_settings'] = {
            'enable_price_alert_monitoring': str(trading_config.enable_price_alert_monitoring).lower(),
            'auto_stop_after_trigger': str(trading_config.auto_stop_after_trigger).lower(),
            'market_sentiment_update_interval': str(trading_config.market_sentiment_update_interval)
        }
        
        # 添加注释（写入时保留原文件的注释）
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


@router.get("/trading-hours", response_model=TradingHoursConfig)
async def get_trading_hours_config():
    """获取交易时段配置"""
    return await asyncio.to_thread(read_trading_hours_config)


@router.post("/trading-hours", response_model=TradingHoursConfig)
async def update_trading_hours_config(config: TradingHoursConfig):
    """更新交易时段配置"""
    # 验证时间格式 (HH:MM)
    import re
    time_pattern = r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$'
    
    for field in ['morning_session_start', 'morning_session_end', 
                   'afternoon_session_start', 'afternoon_session_end']:
        time_value = getattr(config, field)
        if not re.match(time_pattern, time_value):
            raise HTTPException(
                status_code=400,
                detail=f"{field} 格式不正确，应为 HH:MM 格式"
            )
    
    # 验证交易日 (1-7)
    try:
        days = [int(d.strip()) for d in config.trading_days.split(',')]
        if not all(1 <= d <= 7 for d in days):
            raise ValueError("交易日必须在1-7之间")
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"交易日格式不正确: {str(e)}"
        )
    
    # 验证检查间隔
    if config.price_alert_check_interval < 1 or config.price_alert_check_interval > 60:
        raise HTTPException(
            status_code=400,
            detail="价格提醒检查间隔必须在1-60分钟之间"
        )
    
    if config.market_sentiment_update_interval < 1 or config.market_sentiment_update_interval > 60:
        raise HTTPException(
            status_code=400,
            detail="市场情绪更新间隔必须在1-60分钟之间"
        )
    
    success = await asyncio.to_thread(write_trading_hours_config, config)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="保存配置失败"
        )
    
    # 注意：配置修改后需要重启后端服务才能生效
    return config
