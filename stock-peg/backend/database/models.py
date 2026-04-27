"""SQLAlchemy数据库模型"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Date, DECIMAL, BigInteger, UniqueConstraint, Index
from sqlalchemy.sql import func
from database.base import Base


class DailyReport(Base):
    """每日分析报告表"""
    __tablename__ = "daily_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    report_date = Column(Date, nullable=False, index=True)
    create_time = Column(DateTime, server_default=func.now())
    
    # 行情回顾
    open_price = Column(DECIMAL(10, 2))
    close_price = Column(DECIMAL(10, 2))
    high_price = Column(DECIMAL(10, 2))
    low_price = Column(DECIMAL(10, 2))
    change_pct = Column(DECIMAL(10, 4))
    change_amount = Column(DECIMAL(10, 2))
    volume = Column(BigInteger)
    turnover_rate = Column(DECIMAL(10, 4))
    
    # 技术面分析
    ma5 = Column(DECIMAL(10, 2))
    ma10 = Column(DECIMAL(10, 2))
    ma20 = Column(DECIMAL(10, 2))
    macd = Column(DECIMAL(10, 6))
    macd_signal = Column(DECIMAL(10, 6))
    macd_hist = Column(DECIMAL(10, 6))
    rsi = Column(DECIMAL(10, 4))
    kdj_k = Column(DECIMAL(10, 4))
    kdj_d = Column(DECIMAL(10, 4))
    kdj_j = Column(DECIMAL(10, 4))
    technical_score = Column(Integer)
    
    # 基本面分析
    pe_ratio = Column(DECIMAL(10, 2))
    pb_ratio = Column(DECIMAL(10, 2))
    market_cap = Column(DECIMAL(15, 2))
    north_money = Column(DECIMAL(15, 2))
    institution_money = Column(DECIMAL(15, 2))
    fundamental_score = Column(Integer)
    
    # 资金面分析
    main_money = Column(DECIMAL(15, 2))
    big_order_money = Column(DECIMAL(15, 2))
    money_score = Column(Integer)
    
    # 消息面分析
    news_score = Column(Integer)
    news_summary = Column(Text)
    
    # 国际面分析
    international_score = Column(Integer)
    international_summary = Column(Text)
    
    # 预测结果
    predict_direction = Column(String(10))
    predict_probability = Column(DECIMAL(10, 4))
    target_price_low = Column(DECIMAL(10, 2))
    target_price_high = Column(DECIMAL(10, 2))
    risk_level = Column(String(10))
    confidence = Column(String(10))
    
    # 关键影响因素
    key_factors = Column(Text)  # JSON格式
    
    # 操作建议
    action = Column(String(20))
    position = Column(DECIMAL(10, 2))
    stop_loss = Column(DECIMAL(10, 2))
    take_profit = Column(DECIMAL(10, 2))
    action_summary = Column(Text)
    
    # 报告总结
    overall_score = Column(Integer)
    summary = Column(Text)
    
    # 预测验证
    actual_direction = Column(String(10))
    actual_change_pct = Column(DECIMAL(10, 4))
    is_correct = Column(Integer)
    
    # 智能分析（新增）
    smart_analysis = Column(Text, nullable=True)  # LLM 原始回复 (JSON)
    smart_analysis_formatted = Column(Text, nullable=True)  # 格式化后的分析
    pmr_data = Column(Text, nullable=True)  # PMR 数据 (JSON)
    llm_model = Column(String(50), nullable=True)  # 使用的 LLM 模型
    llm_provider = Column(String(50), nullable=True)  # LLM 提供商


class SectorReport(Base):
    """板块分析表"""
    __tablename__ = "sector_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sector_name = Column(String(50), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)
    create_time = Column(DateTime, server_default=func.now())
    
    sector_index = Column(DECIMAL(10, 2))
    sector_change_pct = Column(DECIMAL(10, 4))
    sector_ranking = Column(Integer)
    money_flow = Column(DECIMAL(15, 2))
    is_hotspot = Column(Integer)


class USRelatedStock(Base):
    """美股相关标的表"""
    __tablename__ = "us_related_stocks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cn_stock_code = Column(String(10), nullable=False, index=True)
    cn_stock_name = Column(String(50), nullable=False)
    us_stock_code = Column(String(20), nullable=False)
    us_stock_name = Column(String(100))
    relation_type = Column(String(50))  # 同行业/产业链/ETF/期货
    correlation_score = Column(DECIMAL(10, 4))
    created_at = Column(DateTime, server_default=func.now())


class USDailyData(Base):
    """美股每日数据表"""
    __tablename__ = "us_daily_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    us_stock_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    open_price = Column(DECIMAL(10, 2))
    close_price = Column(DECIMAL(10, 2))
    high_price = Column(DECIMAL(10, 2))
    low_price = Column(DECIMAL(10, 2))
    volume = Column(BigInteger)
    change_pct = Column(DECIMAL(10, 4))
    
    # 技术指标
    ma5 = Column(DECIMAL(10, 2))
    ma10 = Column(DECIMAL(10, 2))
    ma20 = Column(DECIMAL(10, 2))
    rsi = Column(DECIMAL(10, 4))
    macd = Column(DECIMAL(10, 6))
    
    # AI分析结果
    sentiment = Column(String(20))  # 乐观/悲观/中性
    sentiment_analysis = Column(Text)


class FundamentalMetrics(Base):
    """基本面指标表"""
    __tablename__ = "fundamental_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # 估值指标
    pe_ttm = Column(DECIMAL(10, 2))
    pe_lyr = Column(DECIMAL(10, 2))
    pb = Column(DECIMAL(10, 2))
    ps_ttm = Column(DECIMAL(10, 2))
    peg = Column(DECIMAL(10, 2))
    
    # 成长性指标
    revenue_cagr_3y = Column(DECIMAL(10, 4))
    revenue_cagr_5y = Column(DECIMAL(10, 4))
    profit_cagr_3y = Column(DECIMAL(10, 4))
    profit_cagr_5y = Column(DECIMAL(10, 4))
    roe = Column(DECIMAL(10, 4))
    roa = Column(DECIMAL(10, 4))
    
    # 财务健康度
    debt_ratio = Column(DECIMAL(10, 4))
    current_ratio = Column(DECIMAL(10, 4))
    ocf_to_profit = Column(DECIMAL(10, 4))
    altman_z_score = Column(DECIMAL(10, 2))
    
    # 市场趋势
    price_percentile_3y = Column(DECIMAL(10, 2))
    adx = Column(DECIMAL(10, 2))
    volatility_30d = Column(DECIMAL(10, 4))
    trend_direction = Column(String(50))
    ma_status = Column(String(100))
    
    # 综合评分
    valuation_score = Column(DECIMAL(10, 2))
    growth_score = Column(DECIMAL(10, 2))
    financial_health_score = Column(DECIMAL(10, 2))
    market_trend_score = Column(DECIMAL(10, 2))
    overall_score = Column(DECIMAL(10, 2))
    
    # 投资建议
    recommendation_rating = Column(String(20))
    recommendation_reason = Column(Text)


class FinancialHistory(Base):
    """财务数据历史表"""
    __tablename__ = "financial_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)
    report_type = Column(String(20))  # quarterly/annual
    created_at = Column(DateTime, server_default=func.now())
    
    revenue = Column(DECIMAL(15, 2))
    net_profit = Column(DECIMAL(15, 2))
    gross_profit = Column(DECIMAL(15, 2))
    total_assets = Column(DECIMAL(15, 2))
    total_liab = Column(DECIMAL(15, 2))
    total_equity = Column(DECIMAL(15, 2))
    
    operating_cashflow = Column(DECIMAL(15, 2))
    investing_cashflow = Column(DECIMAL(15, 2))
    financing_cashflow = Column(DECIMAL(15, 2))

    # 创建联合唯一索引，确保同一股票同一报告日期只有一条记录
    __table_args__ = (
        UniqueConstraint('stock_code', 'report_date', name='uq_stock_financial_history'),
        {'extend_existing': True}
    )


class StockKLineData(Base):
    """股票K线数据表"""
    __tablename__ = "stock_kline_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    period = Column(String(10), nullable=False, index=True)  # day/week/month/m1/m5/m15/m30/m60
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    open = Column(DECIMAL(10, 2), nullable=False)
    close = Column(DECIMAL(10, 2), nullable=False)
    high = Column(DECIMAL(10, 2), nullable=False)
    low = Column(DECIMAL(10, 2), nullable=False)
    volume = Column(BigInteger)
    amount = Column(DECIMAL(15, 2))
    
    # 创建联合唯一索引和查询复合索引
    __table_args__ = (
        UniqueConstraint('stock_code', 'trade_date', 'period', name='uq_stock_kline'),
        Index('idx_stock_kline_query', 'stock_code', 'period', 'trade_date'),
        {'extend_existing': True}
    )


class DataUpdateLog(Base):
    """数据更新日志表"""
    __tablename__ = "data_update_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, index=True)
    data_type = Column(String(20), nullable=False, index=True)  # kline/financial
    update_type = Column(String(20))  # auto/force/scheduled
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime)
    status = Column(String(20), nullable=False, index=True)  # pending/running/completed/failed
    records_updated = Column(Integer, default=0)
    error_message = Column(Text)
    
    # 创建索引以优化查询性能
    __table_args__ = (
        {'extend_existing': True}
    )


class DataSourceTrack(Base):
    """数据来源追踪表 - 记录每次数据读取的来源和时间"""
    __tablename__ = "data_source_track"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    data_type = Column(String(20), nullable=False, index=True)  # kline/financial/us_index/cn_index/sector_index
    stock_code = Column(String(20), nullable=True, index=True)  # 股票代码或指数代码
    data_source = Column(String(20), nullable=False)  # db/cache/api
    read_time = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    last_update_time = Column(DateTime, nullable=True)  # 数据最后更新时间
    source_location = Column(String(100), nullable=True)  # 数据来源位置（API名称、数据库表等）
    is_updating = Column(Integer, default=0)  # 是否正在后台更新
    metadata_json = Column(Text, nullable=True)  # 额外的元数据（JSON格式）
    
    __table_args__ = (
        {'extend_existing': True}
    )


class StockRealtimeQuote(Base):
    """股票实时行情数据表（本地缓存）"""
    __tablename__ = "stock_realtime_quote"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, unique=True, index=True)  # 股票代码（唯一）
    stock_name = Column(String(50))  # 股票名称
    
    # 行情数据
    price = Column(DECIMAL(10, 2))  # 当前价格
    change = Column(DECIMAL(10, 2))  # 涨跌额
    change_pct = Column(DECIMAL(10, 4))  # 涨跌幅
    open = Column(DECIMAL(10, 2))  # 开盘价
    high = Column(DECIMAL(10, 2))  # 最高价
    low = Column(DECIMAL(10, 2))  # 最低价
    pre_close = Column(DECIMAL(10, 2))  # 昨收价
    volume = Column(BigInteger)  # 成交量
    amount = Column(DECIMAL(15, 2))  # 成交额
    
    # 时间戳
    trade_time = Column(DateTime)  # 交易时间
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 数据来源标记
    data_source = Column(String(20))  # tencent/akshare/manual
    is_updating = Column(Integer, default=0)  # 是否正在后台更新
    
    __table_args__ = (
        {'extend_existing': True}
    )


class ForceIndexCache(Base):
    """Force Index指标缓存表"""
    __tablename__ = "force_index_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50))
    period = Column(String(10), nullable=False, index=True)  # day/week/month
    
    # 计算参数
    ema_short = Column(Integer, default=2)
    ema_long = Column(Integer, default=13)
    
    # 当前值
    raw_force_index = Column(DECIMAL(20, 2))
    fi_short_ema = Column(DECIMAL(20, 2))
    fi_long_ema = Column(DECIMAL(20, 2))
    price_change = Column(DECIMAL(10, 2))
    volume = Column(BigInteger)
    
    # 信号分析
    current_signal = Column(String(20))  # 强烈买入/买入/偏强/中性/偏弱/卖出/强烈卖出
    signal_strength = Column(Integer)  # -10 到 +10
    buy_signals = Column(Text)  # JSON array
    sell_signals = Column(Text)  # JSON array
    
    # 趋势分析
    trend_direction = Column(String(20))  # 上涨/下跌/横盘
    trend_strength = Column(String(20))  # 很强/强/中等/弱
    trend_description = Column(Text)
    
    # 趋势变化分析 (新增)
    trend_type = Column(String(20))  # 上涨趋势/下跌趋势/趋势转折/横盘震荡
    fi2_trend = Column(String(20))  # FI2变化趋势
    fi13_trend = Column(String(20))  # FI13变化趋势
    trend_strength_change = Column(String(20))  # 增强/减弱/无变化
    trend_days = Column(Integer)  # 趋势持续天数
    trend_change_description = Column(Text)  # 趋势变化描述
    
    # 趋势策略建议 (新增)
    trend_based_strategy = Column(Text)  # 基于趋势的策略建议
    
    # 力量分析
    buying_power = Column(Integer)
    selling_power = Column(Integer)
    power_balance = Column(String(50))
    divergence = Column(Integer, default=0)  # 0/1
    
    # 最近数据（JSON格式）
    recent_data = Column(Text)
    
    # 时间戳
    calculation_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 创建联合唯一索引
    __table_args__ = (
        UniqueConstraint('stock_code', 'period', 'ema_short', 'ema_long', 
                        name='uq_force_index_params'),
        {'extend_existing': True}
    )


class DailyWatchlist(Base):
    """每日关注股票表"""
    __tablename__ = "daily_watchlist"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    watch_date = Column(Date, nullable=False, index=True)
    
    # 关注信息
    reason = Column(Text)  # 关注理由
    target_price = Column(DECIMAL(10, 2))  # 目标价格
    change_up_pct = Column(DECIMAL(10, 4))  # 上涨控制比例%
    change_down_pct = Column(DECIMAL(10, 4))  # 下跌控制比例%
    stop_loss_price = Column(DECIMAL(10, 2))  # 止损价格
    notes = Column(Text)  # 备注
    
    # 归档状态
    is_archived = Column(Integer, default=0, index=True)  # 0:未归档, 1:已归档
    archived_at = Column(DateTime)  # 归档时间
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 创建联合唯一索引和查询复合索引
    __table_args__ = (
        UniqueConstraint('stock_code', 'watch_date', name='uq_daily_watchlist'),
        Index('idx_daily_watchlist_query', 'watch_date', 'is_archived'),
        {'extend_existing': True}
    )


class FeishuChatMessage(Base):
    """飞书Bot对话记录表"""
    __tablename__ = "feishu_chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(50), nullable=False, index=True)  # 飞书会话ID
    
    # 消息信息
    message_id = Column(String(100), unique=True, index=True)  # 飞书消息ID（唯一）
    sender_id = Column(String(50), index=True)  # 发送者ID
    sender_name = Column(String(100))  # 发送者名称
    sender_type = Column(String(20))  # user/bot
    
    # 消息内容
    message_type = Column(String(20))  # text/post/interactive
    content = Column(Text, nullable=False)  # 消息内容
    
    # 时间戳
    send_time = Column(DateTime, nullable=False, index=True)  # 消息发送时间
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联信息
    reply_to_id = Column(String(100))  # 回复的消息ID
    
    __table_args__ = (
        Index('idx_feishu_chat_query', 'chat_id', 'send_time'),
        {'extend_existing': True}
    )


class MarketSentimentCache(Base):
    """市场情绪数据缓存表"""
    __tablename__ = "market_sentiment_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(Date, nullable=False, unique=True, index=True)  # 交易日期（唯一）
    
    # 市场统计数据
    total_count = Column(Integer, nullable=False)  # 总股票数
    up_count = Column(Integer, nullable=False)  # 上涨家数
    down_count = Column(Integer, nullable=False)  # 下跌家数
    flat_count = Column(Integer, nullable=False)  # 平盘家数
    limit_up = Column(Integer, nullable=False)  # 涨停家数
    limit_down = Column(Integer, nullable=False)  # 跌停家数
    market_breadth = Column(DECIMAL(10, 2), nullable=False)  # 市场宽度（上涨占比%）
    avg_change_pct = Column(DECIMAL(10, 4))  # 平均涨跌幅
    
    # 上证指数数据
    sh_index_close = Column(DECIMAL(10, 2))  # 上证指数收盘价
    sh_index_change_pct = Column(DECIMAL(10, 4))  # 上证指数涨跌幅
    
    # 数据质量
    data_source = Column(String(20))  # akshare/local_db/manual
    data_quality = Column(String(20))  # full/partial
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        {'extend_existing': True}
    )


class PriceAlert(Base):
    """价格提醒表 - 同时支持目标价格和涨跌幅监控"""
    __tablename__ = "price_alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, index=True)  # 股票代码
    stock_name = Column(String(50))  # 股票名称
    
    # 基准价格（创建时的价格）
    base_price = Column(DECIMAL(10, 2))  # 基准价格
    
    # 提醒条件（至少设置一个）
    target_price = Column(DECIMAL(10, 2))  # 目标价格（可选）
    change_up_pct = Column(DECIMAL(10, 4))  # 上涨幅度%（可选）
    change_down_pct = Column(DECIMAL(10, 4))  # 下跌幅度%（可选）
    
    # 当前状态
    current_price = Column(DECIMAL(10, 2))  # 当前价格
    current_change_pct = Column(DECIMAL(10, 4))  # 当前涨跌幅
    
    # 提醒状态
    is_active = Column(Integer, default=1, index=True)  # 1:激活, 0:停用
    is_triggered = Column(Integer, default=0)  # 1:已触发, 0:未触发
    triggered_count = Column(Integer, default=0)  # 触发次数统计
    triggered_at = Column(DateTime)  # 最后触发时间
    last_triggered_at = Column(DateTime)  # 最后触发时间（用于冷却机制）
    trigger_reason = Column(String(50))  # 触发原因 (target_price/change_up/change_down)
    
    # 冷却机制配置
    cooldown_minutes = Column(Integer, default=30)  # 冷却时间（分钟）
    hysteresis_pct = Column(DECIMAL(5, 2), default=0.5)  # 偏差容忍度（%）
    
    # 飞书通知
    feishu_notified = Column(Integer, default=0)  # 1:已通知, 0:未通知
    feishu_chat_id = Column(String(50))  # 飞书会话ID
    
    # 备注
    notes = Column(Text)  # 备注
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 创建索引
    __table_args__ = (
        Index('idx_price_alert_active', 'is_active', 'is_triggered'),
        {'extend_existing': True}
    )

