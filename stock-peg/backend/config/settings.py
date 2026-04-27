"""应用配置"""
import os
import configparser
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List

# 设置 Tushare 等库的存储路径为项目 backend/data 目录
# 这将重定向 os.path.expanduser('~') 到 data 文件夹
# 确保 data 目录存在
data_path = Path(__file__).parent.parent / "data"
data_path.mkdir(exist_ok=True)
os.environ['USERPROFILE'] = str(data_path.absolute())
os.environ['HOME'] = os.environ['USERPROFILE']  # 兼容不同系统


# 读取INI配置文件
def load_ini_config():
    """加载INI配置文件"""
    config = configparser.ConfigParser()
    ini_path = Path(__file__).parent / "layout.ini"
    if ini_path.exists():
        config.read(ini_path, encoding='utf-8')
    return config

# 读取控制台输出配置
def load_console_output_config():
    """加载控制台输出配置"""
    config = configparser.ConfigParser()
    ini_path = Path(__file__).parent / "console_output.ini"
    if ini_path.exists():
        config.read(ini_path, encoding='utf-8')
    return config

# 读取交易时段配置
def load_trading_hours_config():
    """加载交易时段配置"""
    config = configparser.ConfigParser()
    ini_path = Path(__file__).parent / "trading_hours.ini"
    if ini_path.exists():
        config.read(ini_path, encoding='utf-8')
    return config

_ini_config = load_ini_config()
_console_config = load_console_output_config()
_trading_hours_config = load_trading_hours_config()


class Settings(BaseSettings):
    """应用配置类"""

    # 应用基础配置
    app_name: str = "Stock PEG Analysis Platform"
    app_version: str = "0.1.0"
    debug: bool = False  # [FIX] 强制设置为False，关闭SQLAlchemy的SQL输出
    server_host: str = "0.0.0.0"
    server_port: int = 8000  # 后端运行端口（与 .env 保持一致）
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost,http://127.0.0.1"
    
    # 飞书机器人配置（从INI读取）
    bot_name: str = _ini_config.get('bot', 'name', fallback='PegBot')
    bot_version: str = _ini_config.get('bot', 'version', fallback='0.1.0')

    # 路径配置
    data_dir: Path = Path(__file__).parent.parent / "data"

    # 数据库配置
    database_url: str = f"sqlite+aiosqlite:///{data_dir}/stock_peg.db"

    # 持仓文件路径（使用绝对路径）
    holdings_file_path: str = str(data_dir / "自持股票.md")

    # API配置
    tushare_token: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    zhipu_api_key: Optional[str] = None

    # AI服务配置
    ai_default_provider: str = "zhipu"
    ai_default_model: str = "glm-4"

    # 数据源配置
    tencent_api_base: str = "https://web.sqt.gtimg.cn"
    eastmoney_api_base: str = "https://push2.eastmoney.com"
    yahoo_api_base: str = "https://query1.finance.yahoo.com"

    # 美股数据源配置 (替代 yfinance)
    # Alpha Vantage: https://www.alphavantage.co/support/#api-key
    alphavantage_api_key: Optional[str] = None
    # Finnhub: https://finnhub.io/register
    finnhub_api_key: Optional[str] = None

    # 美股数据源优先级
    us_stock_data_source: str = "alphavantage"  # alphavantage / finnhub / yahoo

    # 飞书机器人配置
    feishu_app_id: Optional[str] = None
    feishu_app_secret: Optional[str] = None
    feishu_encrypt_key: Optional[str] = None  # 用于签名验证
    feishu_verification_token: Optional[str] = None  # 用于验证请求来源

    # 调度配置
    report_generate_time: str = "15:30"  # 每日报告生成时间
    prediction_generate_time: str = "15:00"  # 预测生成时间

    # ===== 数据更新策略配置（从INI文件读取） =====
    # 后台更新任务配置
    max_concurrent_tasks: int = _ini_config.getint('data_update', 'max_concurrent_tasks', fallback=5)
    task_timeout_seconds: int = _ini_config.getint('data_update', 'task_timeout_seconds', fallback=30)

    # 更新锁配置
    lock_expire_seconds: int = _ini_config.getint('data_update', 'lock_expire_seconds', fallback=300)
    cache_expire_seconds: int = _ini_config.getint('data_update', 'cache_expire_seconds', fallback=60)

    # 启动预加载配置
    preload_timeout_seconds: int = _ini_config.getint('data_update', 'preload_timeout_seconds', fallback=30)
    preload_wait_for_completion: bool = _ini_config.getboolean('data_update', 'preload_wait_for_completion', fallback=True)

    # K线数据更新间隔（小时）
    kline_trading_update_interval: int = _ini_config.getint('data_update', 'kline_trading_update_interval', fallback=1)
    kline_non_trading_update_interval: int = _ini_config.getint('data_update', 'kline_non_trading_update_interval', fallback=12)

    # 财务数据更新间隔（天）
    financial_update_interval_days: int = _ini_config.getint('data_update', 'financial_update_interval_days', fallback=7)

    # 美股指数更新间隔（小时）
    us_index_update_interval_hours: int = _ini_config.getint('data_update', 'us_index_update_interval_hours', fallback=24)

    # ===== 控制台输出控制配置（从console_output.ini读取） =====
    # 总开关
    enable_console_output: bool = _console_config.getboolean('console_output', 'enable_console_output', fallback=True)

    # 数据类输出
    enable_stock_data: bool = _console_config.getboolean('console_output', 'enable_stock_data', fallback=False)
    enable_market_index: bool = _console_config.getboolean('console_output', 'enable_market_index', fallback=False)
    enable_kline_data: bool = _console_config.getboolean('console_output', 'enable_kline_data', fallback=False)
    enable_financial_data: bool = _console_config.getboolean('console_output', 'enable_financial_data', fallback=False)
    enable_us_market: bool = _console_config.getboolean('console_output', 'enable_us_market', fallback=False)

    # 功能类输出
    enable_update_progress: bool = _console_config.getboolean('console_output', 'enable_update_progress', fallback=False)
    enable_preload_progress: bool = _console_config.getboolean('console_output', 'enable_preload_progress', fallback=False)
    enable_cache: bool = _console_config.getboolean('console_output', 'enable_cache', fallback=False)
    enable_websocket: bool = _console_config.getboolean('console_output', 'enable_websocket', fallback=False)

    # 飞书机器人专用
    enable_feishu_bot: bool = _console_config.getboolean('console_output', 'enable_feishu_bot', fallback=True)
    enable_feishu_connection: bool = _console_config.getboolean('console_output', 'enable_feishu_connection', fallback=True)
    enable_feishu_chat: bool = _console_config.getboolean('console_output', 'enable_feishu_chat', fallback=True)

    # 其他输出
    enable_scheduler: bool = _console_config.getboolean('console_output', 'enable_scheduler', fallback=False)
    enable_background_task: bool = _console_config.getboolean('console_output', 'enable_background_task', fallback=False)
    enable_database: bool = _console_config.getboolean('console_output', 'enable_database', fallback=False)
    enable_api_request: bool = _console_config.getboolean('console_output', 'enable_api_request', fallback=False)

    # 错误和警告
    enable_errors: bool = _console_config.getboolean('console_output', 'enable_errors', fallback=True)
    enable_warnings: bool = _console_config.getboolean('console_output', 'enable_warnings', fallback=True)
    enable_debug: bool = _console_config.getboolean('console_output', 'enable_debug', fallback=False)

    # 启动信息
    enable_startup_info: bool = _console_config.getboolean('console_output', 'enable_startup_info', fallback=True)
    enable_system_status: bool = _console_config.getboolean('console_output', 'enable_system_status', fallback=True)

    # 进度条配置
    show_progress_bar: bool = _console_config.getboolean('progress_bar', 'show_progress_bar', fallback=True)
    progress_update_interval: int = _console_config.getint('progress_bar', 'progress_update_interval', fallback=500)

    # ===== 交易时段配置（从trading_hours.ini读取） =====
    # 上午盘交易时段
    morning_session_start: str = _trading_hours_config.get('trading_hours', 'morning_session_start', fallback='09:30')
    morning_session_end: str = _trading_hours_config.get('trading_hours', 'morning_session_end', fallback='11:30')
    
    # 下午盘交易时段
    afternoon_session_start: str = _trading_hours_config.get('trading_hours', 'afternoon_session_start', fallback='13:00')
    afternoon_session_end: str = _trading_hours_config.get('trading_hours', 'afternoon_session_end', fallback='15:00')
    
    # 交易日配置
    trading_days: str = _trading_hours_config.get('trading_hours', 'trading_days', fallback='1,2,3,4,5')
    
    # 价格提醒检查频率（分钟）
    price_alert_check_interval: int = _trading_hours_config.getint('trading_hours', 'price_alert_check_interval', fallback=1)
    
    # 监控设置
    enable_price_alert_monitoring: bool = _trading_hours_config.getboolean('monitor_settings', 'enable_price_alert_monitoring', fallback=True)
    auto_stop_after_trigger: bool = _trading_hours_config.getboolean('monitor_settings', 'auto_stop_after_trigger', fallback=True)
    market_sentiment_update_interval: int = _trading_hours_config.getint('monitor_settings', 'market_sentiment_update_interval', fallback=5)

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]
    
    @property
    def trading_days_list(self) -> List[int]:
        """获取交易日列表"""
        return [int(day.strip()) for day in self.trading_days.split(",") if day.strip().isdigit()]

    class Config:
        env_file = str(Path(__file__).parent.parent / ".env")
        case_sensitive = False


# 创建settings实例
settings = Settings()
