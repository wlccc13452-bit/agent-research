"""
控制台输出配置API

提供查看和动态修改控制台输出配置的接口
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from config.settings import settings
import configparser
from pathlib import Path

router = APIRouter()


class ConsoleOutputConfig(BaseModel):
    """控制台输出配置模型"""
    # 总开关
    enable_console_output: bool
    
    # 数据类输出
    enable_stock_data: bool
    enable_market_index: bool
    enable_kline_data: bool
    enable_financial_data: bool
    enable_us_market: bool
    
    # 功能类输出
    enable_update_progress: bool
    enable_preload_progress: bool
    enable_cache: bool
    enable_websocket: bool
    
    # 飞书机器人专用
    enable_feishu_bot: bool
    enable_feishu_connection: bool
    enable_feishu_chat: bool
    
    # 其他输出
    enable_scheduler: bool
    enable_background_task: bool
    enable_database: bool
    enable_api_request: bool
    
    # 错误和警告
    enable_errors: bool
    enable_warnings: bool
    enable_debug: bool
    
    # 启动信息
    enable_startup_info: bool
    enable_system_status: bool
    
    # 进度条
    show_progress_bar: bool
    progress_update_interval: int


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    config_key: str
    value: bool


@router.get("/console-output", response_model=ConsoleOutputConfig)
async def get_console_output_config():
    """
    获取当前控制台输出配置
    
    Returns:
        当前所有配置项的值
    """
    return ConsoleOutputConfig(
        # 总开关
        enable_console_output=settings.enable_console_output,
        
        # 数据类输出
        enable_stock_data=settings.enable_stock_data,
        enable_market_index=settings.enable_market_index,
        enable_kline_data=settings.enable_kline_data,
        enable_financial_data=settings.enable_financial_data,
        enable_us_market=settings.enable_us_market,
        
        # 功能类输出
        enable_update_progress=settings.enable_update_progress,
        enable_preload_progress=settings.enable_preload_progress,
        enable_cache=settings.enable_cache,
        enable_websocket=settings.enable_websocket,
        
        # 飞书机器人专用
        enable_feishu_bot=settings.enable_feishu_bot,
        enable_feishu_connection=settings.enable_feishu_connection,
        enable_feishu_chat=settings.enable_feishu_chat,
        
        # 其他输出
        enable_scheduler=settings.enable_scheduler,
        enable_background_task=settings.enable_background_task,
        enable_database=settings.enable_database,
        enable_api_request=settings.enable_api_request,
        
        # 错误和警告
        enable_errors=settings.enable_errors,
        enable_warnings=settings.enable_warnings,
        enable_debug=settings.enable_debug,
        
        # 启动信息
        enable_startup_info=settings.enable_startup_info,
        enable_system_status=settings.enable_system_status,
        
        # 进度条
        show_progress_bar=settings.show_progress_bar,
        progress_update_interval=settings.progress_update_interval,
    )


@router.get("/console-output/summary")
async def get_console_output_summary():
    """
    获取控制台输出配置摘要
    
    Returns:
        配置摘要信息
    """
    enabled_count = sum([
        settings.enable_stock_data,
        settings.enable_market_index,
        settings.enable_kline_data,
        settings.enable_financial_data,
        settings.enable_us_market,
        settings.enable_update_progress,
        settings.enable_preload_progress,
        settings.enable_cache,
        settings.enable_websocket,
        settings.enable_scheduler,
        settings.enable_background_task,
        settings.enable_database,
        settings.enable_api_request,
        settings.enable_debug,
    ])
    
    total_count = 14  # 上面统计的总项数
    
    return {
        "console_output_enabled": settings.enable_console_output,
        "errors_enabled": settings.enable_errors,
        "warnings_enabled": settings.enable_warnings,
        "debug_enabled": settings.enable_debug,
        "feishu_enabled": all([
            settings.enable_feishu_bot,
            settings.enable_feishu_connection,
            settings.enable_feishu_chat,
        ]),
        "data_outputs_enabled": enabled_count,
        "data_outputs_total": total_count,
        "progress_bar_enabled": settings.show_progress_bar,
        "status": "verbose" if enabled_count > 5 else "quiet" if enabled_count < 3 else "normal",
        "recommendation": get_recommendation(enabled_count, total_count)
    }


def get_recommendation(enabled_count: int, total_count: int) -> str:
    """根据当前配置给出推荐"""
    if enabled_count > 10:
        return "配置较详细，适合调试。生产环境建议减少输出以提升性能。"
    elif enabled_count < 3:
        return "配置简洁，适合生产环境。如需调试可开启特定配置项。"
    else:
        return "配置平衡，适合开发环境。"


@router.post("/console-output/update")
async def update_console_output_config(request: ConfigUpdateRequest):
    """
    更新单个配置项（需要重启服务生效）
    
    Args:
        request: 配置更新请求
        
    Returns:
        更新结果
    """
    # 验证配置项是否存在
    valid_keys = [
        'enable_console_output', 'enable_stock_data', 'enable_market_index',
        'enable_kline_data', 'enable_financial_data', 'enable_us_market',
        'enable_update_progress', 'enable_preload_progress', 'enable_cache',
        'enable_websocket', 'enable_feishu_bot', 'enable_feishu_connection',
        'enable_feishu_chat', 'enable_scheduler', 'enable_background_task',
        'enable_database', 'enable_api_request', 'enable_errors',
        'enable_warnings', 'enable_debug', 'enable_startup_info',
        'enable_system_status', 'show_progress_bar'
    ]
    
    if request.config_key not in valid_keys:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid config key: {request.config_key}"
        )
    
    # 更新INI文件
    try:
        config_path = Path(__file__).parent.parent / "config" / "console_output.ini"
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        
        # 确定section
        if request.config_key in ['show_progress_bar', 'progress_update_interval']:
            section = 'progress_bar'
        else:
            section = 'console_output'
        
        # 更新配置
        if section not in config:
            config.add_section(section)
        
        config.set(section, request.config_key, str(request.value).lower())
        
        # 写回文件
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        
        return {
            "success": True,
            "message": f"配置项 {request.config_key} 已更新为 {request.value}",
            "note": "需要重启服务才能生效"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新配置文件失败: {str(e)}"
        )


@router.post("/console-output/preset/{preset_name}")
async def apply_preset(preset_name: str):
    """
    应用预设配置
    
    Args:
        preset_name: 预设名称 (quiet/normal/debug/feishu-only)
        
    Returns:
        应用结果
    """
    presets = {
        "quiet": {
            "enable_console_output": True,
            "enable_errors": True,
            "enable_warnings": True,
            "enable_startup_info": True,
            "enable_feishu_bot": True,
            "enable_feishu_connection": True,
            "enable_feishu_chat": True,
            # 其他全部false
        },
        "normal": {
            "enable_console_output": True,
            "enable_errors": True,
            "enable_warnings": True,
            "enable_startup_info": True,
            "enable_system_status": True,
            "enable_feishu_bot": True,
            "enable_feishu_connection": True,
            "enable_feishu_chat": True,
        },
        "debug": {
            "enable_console_output": True,
            "enable_errors": True,
            "enable_warnings": True,
            "enable_debug": True,
            "enable_startup_info": True,
            "enable_system_status": True,
            "enable_stock_data": True,
            "enable_market_index": True,
        },
        "feishu-only": {
            "enable_console_output": True,
            "enable_errors": True,
            "enable_warnings": True,
            "enable_feishu_bot": True,
            "enable_feishu_connection": True,
            "enable_feishu_chat": True,
        }
    }
    
    if preset_name not in presets:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid preset name: {preset_name}. Available: {list(presets.keys())}"
        )
    
    preset = presets[preset_name]
    
    try:
        config_path = Path(__file__).parent.parent / "config" / "console_output.ini"
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        
        # 应用预设
        if 'console_output' not in config:
            config.add_section('console_output')
        
        # 先设置所有配置为false
        for key in [
            'enable_stock_data', 'enable_market_index', 'enable_kline_data',
            'enable_financial_data', 'enable_us_market', 'enable_update_progress',
            'enable_preload_progress', 'enable_cache', 'enable_websocket',
            'enable_scheduler', 'enable_background_task', 'enable_database',
            'enable_api_request', 'enable_debug'
        ]:
            config.set('console_output', key, 'false')
        
        # 应用预设中的配置
        for key, value in preset.items():
            config.set('console_output', key, str(value).lower())
        
        # 写回文件
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        
        return {
            "success": True,
            "message": f"已应用预设: {preset_name}",
            "preset": preset,
            "note": "需要重启服务才能生效"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"应用预设失败: {str(e)}"
        )
