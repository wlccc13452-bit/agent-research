# 财务数据测试发现的问题

**测试时间**: 2026-03-09 20:15

---

## ⚠️ 发现新问题：财务数据表结构不匹配

### 问题1: fundamental_metrics 表

**代码期望的字段**:
- `valuation` (JSON对象)
- `growth` (JSON对象)
- `financial_health` (JSON对象)

**实际数据库字段**:
- `valuation_score` (数值)
- `growth_score` (数值)
- `financial_health_score` (数值)
- `pe_ttm`, `pb`, `roe` 等具体指标字段

**实际表结构**:
```
id, stock_code, report_date, created_at,
pe_ttm, pe_lyr, pb, ps_ttm, peg,
revenue_cagr_3y, revenue_cagr_5y, profit_cagr_3y, profit_cagr_5y,
roe, roa, debt_ratio, current_ratio, ocf_to_profit, altman_z_score,
price_percentile_3y, adx, volatility_30d,
valuation_score, growth_score, financial_health_score, market_trend_score, overall_score
```

**样例数据**:
```json
{
  "stock_code": "600219",
  "report_date": "2026-03-05",
  "pe_ttm": 20.5,
  "pb": 2.1,
  "roe": 12.5,
  "valuation_score": 3.5,
  "growth_score": 4.0,
  "financial_health_score": 4.0,
  "overall_score": 3.7
}
```

---

### 问题2: financial_history 表

**代码期望的字段**:
- `basic_eps`
- `pe_ratio`

**实际数据库字段**:
- `revenue`
- `net_profit`
- `gross_profit`
- `total_assets`, `total_liab`, `total_equity`
- `operating_cashflow`, `investing_cashflow`, `financing_cashflow`

**实际表结构**:
```
id, stock_code, report_date, report_type, created_at,
revenue, net_profit, gross_profit,
total_assets, total_liab, total_equity,
operating_cashflow, investing_cashflow, financing_cashflow
```

**样例数据**:
```json
{
  "stock_code": "300308",
  "report_date": "2022-12-31",
  "report_type": "quarterly",
  "revenue": 9641794766.08,
  "net_profit": 1233689242.88
}
```

---

## 📊 数据库现状

### 数据量
- ✅ `fundamental_metrics`: **1286条记录**
- ✅ `financial_history`: **120条记录**

### 数据完整性
- ✅ 有PE、PB、ROE等关键指标
- ✅ 有评分数据（valuation_score等）
- ⚠️ 部分字段为空（如 price_percentile_3y, adx, volatility_30d）

---

## 🔧 需要修复的问题

### 问题1: 模型定义与数据库不匹配

**可能原因**:
1. 数据库表结构已更新，但模型定义未同步
2. 代码期望JSON字段，但数据库使用单独字段存储

**需要检查的文件**:
- `backend/database/models.py` - FundamentalMetrics 模型定义
- `backend/services/fundamental_analyzer.py` - 财务数据服务

---

### 问题2: 财务数据查询失败

**影响范围**:
- `/api/fundamental/{stock_code}/annual-report` - 年报接口
- `/api/fundamental/{stock_code}/quarterly` - 季度数据接口
- `/api/fundamental/{stock_code}` - 综合分析接口

**错误信息**:
```
sqlite3.OperationalError: no such column: valuation
```

---

## ✅ 正确的查询方式

### 查询财务指标
```sql
-- ✅ 正确
SELECT stock_code, pe_ttm, pb, roe, valuation_score, growth_score, overall_score
FROM fundamental_metrics
WHERE stock_code = '600519'
ORDER BY report_date DESC LIMIT 1;

-- ❌ 错误
SELECT stock_code, valuation, growth, financial_health
FROM fundamental_metrics
WHERE stock_code = '600519';
```

### 查询财务历史
```sql
-- ✅ 正确
SELECT stock_code, report_date, revenue, net_profit
FROM financial_history
WHERE stock_code = '600519'
ORDER BY report_date DESC;

-- ❌ 错误
SELECT stock_code, report_date, basic_eps, pe_ratio
FROM financial_history
WHERE stock_code = '600519';
```

---

## 📝 修复方案

### 方案1: 更新模型定义（推荐）

修改 `backend/database/models.py`:

```python
class FundamentalMetrics(Base):
    __tablename__ = 'fundamental_metrics'
    
    id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False)
    report_date = Column(Date)
    created_at = Column(DateTime)
    
    # 估值指标
    pe_ttm = Column(Numeric(10, 2))
    pe_lyr = Column(Numeric(10, 2))
    pb = Column(Numeric(10, 2))
    ps_ttm = Column(Numeric(10, 2))
    peg = Column(Numeric(10, 2))
    
    # 成长指标
    revenue_cagr_3y = Column(Numeric(10, 4))
    revenue_cagr_5y = Column(Numeric(10, 4))
    profit_cagr_3y = Column(Numeric(10, 4))
    profit_cagr_5y = Column(Numeric(10, 4))
    
    # 财务健康指标
    roe = Column(Numeric(10, 4))
    roa = Column(Numeric(10, 4))
    debt_ratio = Column(Numeric(10, 4))
    current_ratio = Column(Numeric(10, 4))
    
    # 评分
    valuation_score = Column(Numeric(10, 2))
    growth_score = Column(Numeric(10, 2))
    financial_health_score = Column(Numeric(10, 2))
    overall_score = Column(Numeric(10, 2))
```

---

### 方案2: 更新服务层代码

修改 `backend/services/fundamental_analyzer.py`:

```python
async def get_metrics_from_db(self, stock_code: str):
    """从数据库获取财务指标"""
    
    # ✅ 使用正确的字段名
    stmt = select(FundamentalMetrics).where(
        FundamentalMetrics.stock_code == stock_code
    ).order_by(desc(FundamentalMetrics.report_date)).limit(1)
    
    result = await session.execute(stmt)
    metrics = result.scalar_one_or_none()
    
    if metrics:
        # 构建返回格式（兼容前端期望的JSON格式）
        return {
            'stock_code': metrics.stock_code,
            'valuation': {
                'pe_ttm': float(metrics.pe_ttm) if metrics.pe_ttm else None,
                'pb': float(metrics.pb) if metrics.pb else None,
                'score': float(metrics.valuation_score) if metrics.valuation_score else None
            },
            'growth': {
                'revenue_cagr_3y': float(metrics.revenue_cagr_3y) if metrics.revenue_cagr_3y else None,
                'profit_cagr_3y': float(metrics.profit_cagr_3y) if metrics.profit_cagr_3y else None,
                'score': float(metrics.growth_score) if metrics.growth_score else None
            },
            'financial_health': {
                'roe': float(metrics.roe) if metrics.roe else None,
                'debt_ratio': float(metrics.debt_ratio) if metrics.debt_ratio else None,
                'score': float(metrics.financial_health_score) if metrics.financial_health_score else None
            },
            'overall_score': float(metrics.overall_score) if metrics.overall_score else None,
            'report_date': metrics.report_date
        }
    
    return None
```

---

## 🎯 总结

### 发现的问题
1. ✅ **美股指数**: 列名 `symbol` → `us_stock_code`
2. ✅ **A股指数**: 代码格式不兼容
3. ⚠️ **财务数据**: 表结构与代码期望不匹配

### 数据状态
- ✅ 数据库有财务数据（1286条）
- ✅ 数据结构正确，只是字段名不匹配
- ✅ 数据可以正常获取，只需修改查询代码

### 优先级
- **高**: 修复财务数据查询（1286条数据可用）
- **中**: 美股数据查询（11条数据可用）
- **中**: A股指数获取（代码格式问题）

---

**更新时间**: 2026-03-09 20:20
