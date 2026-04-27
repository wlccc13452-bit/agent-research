"""Settings API Router - System configuration management"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import List
from pathlib import Path
import configparser
from datetime import time

from config.settings import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


class TradingHoursConfig(BaseModel):
    """Trading hours configuration model"""
    # Morning session
    morning_session_start: str
    morning_session_end: str
    
    # Afternoon session
    afternoon_session_start: str
    afternoon_session_end: str
    
    # Trading days
    trading_days: str
    
    # Check interval
    price_alert_check_interval: int
    
    # Monitor settings
    enable_price_alert_monitoring: bool
    auto_stop_after_trigger: bool
    market_sentiment_update_interval: int
    
    @field_validator('morning_session_start', 'morning_session_end', 
                     'afternoon_session_start', 'afternoon_session_end')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time format HH:MM"""
        try:
            parts = v.split(':')
            if len(parts) != 2:
                raise ValueError('Invalid time format')
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError('Invalid time range')
            return v
        except Exception as e:
            raise ValueError(f'Time must be in HH:MM format: {e}')
    
    @field_validator('trading_days')
    @classmethod
    def validate_trading_days(cls, v: str) -> str:
        """Validate trading days format"""
        try:
            days = [int(d.strip()) for d in v.split(',')]
            if not all(1 <= d <= 7 for d in days):
                raise ValueError('Trading days must be between 1-7')
            return v
        except Exception as e:
            raise ValueError(f'Invalid trading days format: {e}')
    
    @field_validator('price_alert_check_interval', 'market_sentiment_update_interval')
    @classmethod
    def validate_positive_int(cls, v: int) -> int:
        """Validate positive integer"""
        if v <= 0:
            raise ValueError('Must be positive integer')
        return v


class TradingHoursResponse(BaseModel):
    """Trading hours response model"""
    morning_session_start: str
    morning_session_end: str
    afternoon_session_start: str
    afternoon_session_end: str
    trading_days: str
    trading_days_list: List[int]
    price_alert_check_interval: int
    enable_price_alert_monitoring: bool
    auto_stop_after_trigger: bool
    market_sentiment_update_interval: int


def _get_config_path() -> Path:
    """Get trading_hours.ini config file path"""
    return Path(__file__).parent.parent / "config" / "trading_hours.ini"


@router.get("/trading-hours", response_model=TradingHoursResponse)
async def get_trading_hours():
    """Get current trading hours configuration
    
    Returns:
        TradingHoursResponse: Current configuration with parsed trading days list
    """
    return TradingHoursResponse(
        morning_session_start=settings.morning_session_start,
        morning_session_end=settings.morning_session_end,
        afternoon_session_start=settings.afternoon_session_start,
        afternoon_session_end=settings.afternoon_session_end,
        trading_days=settings.trading_days,
        trading_days_list=settings.trading_days_list,
        price_alert_check_interval=settings.price_alert_check_interval,
        enable_price_alert_monitoring=settings.enable_price_alert_monitoring,
        auto_stop_after_trigger=settings.auto_stop_after_trigger,
        market_sentiment_update_interval=settings.market_sentiment_update_interval
    )


@router.put("/trading-hours", response_model=TradingHoursResponse)
async def update_trading_hours(config: TradingHoursConfig):
    """Update trading hours configuration
    
    This will update the trading_hours.ini file and reload settings.
    
    Args:
        config: New trading hours configuration
        
    Returns:
        TradingHoursResponse: Updated configuration
        
    Raises:
        HTTPException: If update fails
    """
    try:
        config_path = _get_config_path()
        
        # Read current config
        parser = configparser.ConfigParser()
        parser.read(config_path, encoding='utf-8')
        
        # Update trading_hours section
        if 'trading_hours' not in parser:
            parser.add_section('trading_hours')
        
        parser.set('trading_hours', 'morning_session_start', config.morning_session_start)
        parser.set('trading_hours', 'morning_session_end', config.morning_session_end)
        parser.set('trading_hours', 'afternoon_session_start', config.afternoon_session_start)
        parser.set('trading_hours', 'afternoon_session_end', config.afternoon_session_end)
        parser.set('trading_hours', 'trading_days', config.trading_days)
        parser.set('trading_hours', 'price_alert_check_interval', str(config.price_alert_check_interval))
        
        # Update monitor_settings section
        if 'monitor_settings' not in parser:
            parser.add_section('monitor_settings')
        
        parser.set('monitor_settings', 'enable_price_alert_monitoring', 
                   str(config.enable_price_alert_monitoring).lower())
        parser.set('monitor_settings', 'auto_stop_after_trigger', 
                   str(config.auto_stop_after_trigger).lower())
        parser.set('monitor_settings', 'market_sentiment_update_interval', 
                   str(config.market_sentiment_update_interval))
        
        # Write back to file
        with open(config_path, 'w', encoding='utf-8') as f:
            parser.write(f)
        
        # Reload settings
        # Note: This requires restarting the service or implementing dynamic reload
        # For now, we'll just update the in-memory settings
        import importlib
        from config import settings as settings_module
        importlib.reload(settings_module)
        from config.settings import settings as new_settings
        
        # Return updated config
        return TradingHoursResponse(
            morning_session_start=new_settings.morning_session_start,
            morning_session_end=new_settings.morning_session_end,
            afternoon_session_start=new_settings.afternoon_session_start,
            afternoon_session_end=new_settings.afternoon_session_end,
            trading_days=new_settings.trading_days,
            trading_days_list=new_settings.trading_days_list,
            price_alert_check_interval=new_settings.price_alert_check_interval,
            enable_price_alert_monitoring=new_settings.enable_price_alert_monitoring,
            auto_stop_after_trigger=new_settings.auto_stop_after_trigger,
            market_sentiment_update_interval=new_settings.market_sentiment_update_interval
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.post("/trading-hours/reload")
async def reload_trading_hours():
    """Reload trading hours configuration from INI file
    
    This endpoint forces a reload of the trading_hours.ini configuration.
    Useful after manual edits to the INI file.
    
    Returns:
        dict: Success message
    """
    try:
        import importlib
        from config import settings as settings_module
        importlib.reload(settings_module)
        
        return {"status": "success", "message": "Configuration reloaded successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload configuration: {str(e)}")
