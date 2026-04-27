"""数据源常量定义"""
from enum import Enum, auto


class FunctionType(Enum):
    """数据源支持的功能类型"""
    # === 行情数据 ===
    REALTIME_QUOTE = auto()          # 实时行情（单只/批量）
    KLINE_DAILY = auto()             # 日K线
    KLINE_WEEKLY = auto()            # 周K线
    KLINE_MONTHLY = auto()           # 月K线
    KLINE_MINUTE = auto()            # 分钟K线
    TICK_DATA = auto()               # 分笔数据
    INDEX_QUOTE = auto()             # 指数实时行情
    INDEX_KLINE = auto()             # 指数K线
    HK_QUOTE = auto()                # 港股行情
    US_QUOTE = auto()                # 美股行情
    ETF_QUOTE = auto()               # ETF行情

    # === 财务数据 ===
    FINANCIAL_REPORT = auto()        # 财务报表
    FINANCIAL_INDICATOR = auto()     # 财务指标
    BALANCE_SHEET = auto()           # 资产负债表
    INCOME_STATEMENT = auto()        # 利润表
    CASH_FLOW = auto()               # 现金流量表
    ANNUAL_REPORT = auto()           # 年报
    QUARTERLY_REPORT = auto()        # 季报

    # === 市场数据 ===
    STOCK_LIST = auto()              # 股票列表
    STOCK_INFO = auto()              # 个股信息（市值/行业等）
    TRADE_CALENDAR = auto()          # 交易日历
    MARKET_INDEX = auto()            # 市场指数数据
    MARKET_SENTIMENT = auto()        # 市场情绪（涨跌统计）
    INDUSTRY_SECTORS = auto()        # 行业板块列表
    CONCEPT_SECTORS = auto()         # 概念板块列表
    SECTOR_STOCKS = auto()           # 板块成分股

    # === 资金流向 ===
    MONEY_FLOW = auto()              # 个股资金流向
    SECTOR_MONEY_FLOW = auto()       # 板块资金流向
    MARKET_MONEY_FLOW = auto()       # 大盘资金流向
    NORTH_MONEY_FLOW = auto()        # 北向资金流向
    NORTH_MONEY_TOP10 = auto()       # 北向资金持股TOP10

    # === 宏观经济 ===
    MACRO_CPI = auto()               # CPI数据
    MACRO_GDP = auto()               # GDP数据
    MACRO_PMI = auto()               # PMI数据

    # === 其他 ===
    NEWS = auto()                    # 新闻资讯
    DIVIDEND = auto()                # 分红送转
    SHAREHOLDER = auto()             # 股东信息
    INSTITUTION_HOLDINGS = auto()    # 机构持仓
    LHB_DETAIL = auto()              # 龙虎榜详情
    STOCK_SEARCH = auto()            # 股票搜索（按名称/代码）
    FORECAST = auto()                # 业绩预告
    EXPRESS = auto()                 # 业绩快报


class DataSourceType(Enum):
    """数据源类型"""
    TUSHARE = "tushare"
    AKSHARE = "akshare"
    TENCENT = "tencent"
    EASTMONEY = "eastmoney"
    SINAFINANCE = "sina"
    YFINANCE = "yfinance"
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    LOCAL_DB = "local_db"

    def __str__(self):
        return self.value
