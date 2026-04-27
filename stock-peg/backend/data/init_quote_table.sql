-- 创建行情数据表
CREATE TABLE IF NOT EXISTS stock_realtime_quote (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code VARCHAR(10) NOT NULL UNIQUE,
    stock_name VARCHAR(50),
    price DECIMAL(10, 2),
    change DECIMAL(10, 2),
    change_pct DECIMAL(10, 4),
    open DECIMAL(10, 2),
    high DECIMAL(10, 2),
    low DECIMAL(10, 2),
    pre_close DECIMAL(10, 2),
    volume BIGINT,
    amount DECIMAL(15, 2),
    trade_time DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(20),
    is_updating INTEGER DEFAULT 0
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_stock_realtime_quote_code ON stock_realtime_quote(stock_code);

-- 验证表结构
SELECT '✅ 行情数据表创建成功！' as message;
SELECT name FROM sqlite_master WHERE type='table' AND name='stock_realtime_quote';
