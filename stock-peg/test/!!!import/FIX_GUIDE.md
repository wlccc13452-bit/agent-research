# 快速修复指南

基于测试验证，以下是具体修复步骤。

---

## 修复1: 美股数据库查询列名 (优先级: 最高)

### 需要修改的文件
`backend/services/us_market_analyzer.py`

### 具体修改
将所有SQL查询中的 `symbol` 列名替换为 `us_stock_code`

### 示例代码

**修改前** ❌:
```python
# 第594行附近
stmt = select(USDailyData).where(
    USDailyData.symbol == symbol  # ❌ 错误的列名
).order_by(desc(USDailyData.trade_date)).limit(limit)
```

**修改后** ✅:
```python
# 第594行附近
stmt = select(USDailyData).where(
    USDailyData.us_stock_code == symbol  # ✅ 正确的列名
).order_by(desc(USDailyData.trade_date)).limit(limit)
```

### 验证命令
```bash
# 在项目根目录执行
cd backend/services
grep -n "\.symbol" us_market_analyzer.py
# 或在Windows PowerShell:
Select-String -Path "us_market_analyzer.py" -Pattern "\.symbol"
```

---

## 修复2: A股指数代码格式转换 (优先级: 最高)

### 需要新增/修改的文件
1. `backend/utils/index_code_converter.py` (新建)
2. `backend/routers/stock.py` (修改)
3. `backend/services/akshare_service.py` (修改)

### 步骤1: 创建代码转换工具

新建文件 `backend/utils/index_code_converter.py`:

```python
"""指数代码格式转换工具"""

def normalize_index_code(code: str) -> dict:
    """
    标准化指数代码格式
    
    支持的输入格式:
    - "000001.SH" (带后缀，前端传递格式)
    - "sh000001" (带前缀)
    - "000001" (纯代码)
    
    返回: {
        'pure_code': '000001',      # 纯代码
        'market': 'sh',              # 市场（sh/sz）
        'akshare_code': 'sh000001', # Akshare格式
        'tencent_code': 'sh000001', # 腾讯API格式
        'original': '000001.SH'     # 原始代码
    }
    """
    result = {
        'pure_code': None,
        'market': None,
        'akshare_code': None,
        'tencent_code': None,
        'original': code
    }
    
    if '.' in code:
        # 格式: 000001.SH
        pure_code, suffix = code.split('.')
        market = suffix.lower()
    elif code.startswith(('sh', 'sz')):
        # 格式: sh000001
        market = code[:2]
        pure_code = code[2:]
    else:
        # 纯代码: 000001
        pure_code = code
        # 根据代码判断市场
        if code.startswith(('0', '5', '6')):
            market = 'sh'
        else:
            market = 'sz'
    
    result['pure_code'] = pure_code
    result['market'] = market
    result['akshare_code'] = f"{market}{pure_code}"
    result['tencent_code'] = f"{market}{pure_code}"
    
    return result


def normalize_index_codes(codes: list) -> list:
    """批量转换指数代码"""
    return [normalize_index_code(code) for code in codes]
```

### 步骤2: 修改指数获取接口

在 `backend/routers/stock.py` 中：

**修改前** ❌:
```python
@router.get("/index/realtime")
async def get_index_realtime(codes: str):
    """获取指数实时行情"""
    code_list = codes.split(',')
    # 直接使用原始代码...
```

**修改后** ✅:
```python
from utils.index_code_converter import normalize_index_codes

@router.get("/index/realtime")
async def get_index_realtime(codes: str):
    """获取指数实时行情"""
    code_list = codes.split(',')
    
    # ✅ 转换代码格式
    normalized_codes = normalize_index_codes(code_list)
    
    # 使用转换后的代码获取数据
    for item in normalized_codes:
        pure_code = item['pure_code']
        akshare_code = item['akshare_code']
        # ...
```

### 步骤3: 修改Akshare服务

在 `backend/services/akshare_service.py` 的 `get_kline` 方法中：

**修改前** ❌:
```python
async def get_kline(self, stock_code: str, period: str = "day", count: int = 100):
    # 直接使用 stock_code
    df = ak.stock_zh_a_hist(symbol=stock_code, ...)
```

**修改后** ✅:
```python
from utils.index_code_converter import normalize_index_code

async def get_kline(self, stock_code: str, period: str = "day", count: int = 100):
    # ✅ 检查是否为指数代码（包含.）
    if '.' in stock_code:
        normalized = normalize_index_code(stock_code)
        # 使用Akshare格式
        ak_code = normalized['akshare_code']
    else:
        ak_code = stock_code
    
    df = ak.stock_zh_a_hist(symbol=ak_code, ...)
```

---

## 修复3: 深证指数获取 (优先级: 高)

### 问题
深证成指(399001)和创业板指(399006)在Akshare指数列表中未找到

### 解决方案
使用Akshare的实时行情接口（包含深证指数）

在 `backend/services/akshare_service.py` 中添加：

```python
async def get_index_realtime_all(self) -> Optional[List[Dict]]:
    """获取所有A股指数实时行情（包括深证指数）"""
    try:
        import akshare as ak
        
        # 使用实时行情接口（包含所有A股，包括深证指数）
        df = ak.stock_zh_a_spot_em()
        
        # 过滤出指数（根据代码规则）
        # 指数代码: 000xxx, 399xxx, 510xxx, 688xxx等
        index_codes = ['000001', '000016', '000905', '399001', '399006']
        
        indices = []
        for code in index_codes:
            index_data = df[df['代码'] == code]
            if not index_data.empty:
                row = index_data.iloc[0]
                indices.append({
                    'code': code,
                    'name': row['名称'],
                    'price': float(row['最新价']),
                    'change_pct': float(row['涨跌幅']),
                    'volume': int(row['成交量']),
                    'amount': float(row['成交额'])
                })
        
        return indices
        
    except Exception as e:
        logger.error(f"获取指数实时行情失败: {str(e)}")
        return None
```

---

## 验证测试

修改完成后，执行以下测试：

### 测试1: 美股指数
```bash
curl http://localhost:8000/api/us-market/indices
```

**预期结果**: 返回4个美股指数数据

### 测试2: A股指数
```bash
curl "http://localhost:8000/api/stock/index/realtime?codes=000001.SH,399001.SZ,000016.SH"
```

**预期结果**: 返回3个A股指数数据

### 测试3: 后端日志
查看日志文件，确认没有以下错误：
- ❌ `no such column: symbol`
- ❌ `Server error '501 Not Implemented'` (腾讯API)
- ❌ `Akshare 未找到股票`

---

## 修改文件清单

### 必须修改
- [ ] `backend/services/us_market_analyzer.py` - 替换 `symbol` 为 `us_stock_code`
- [ ] `backend/utils/index_code_converter.py` - 新建代码转换工具
- [ ] `backend/routers/stock.py` - 添加代码格式转换
- [ ] `backend/services/akshare_service.py` - 处理指数代码格式

### 建议优化
- [ ] 优化VIX数据源获取
- [ ] 添加深证指数专门处理
- [ ] 完善错误处理和日志

---

## 修复4: 财务数据表结构不匹配 (优先级: 高) ⚠️ 新发现

### 问题
代码期望JSON字段（`valuation`, `growth`, `financial_health`），但数据库使用单独字段存储（`valuation_score`, `growth_score`等）

### 实际表结构
```
fundamental_metrics表:
- pe_ttm, pb, roe 等具体指标字段
- valuation_score, growth_score, financial_health_score 等评分字段

financial_history表:
- revenue, net_profit 等财务数据字段
```

### 数据库现状
- ✅ 有数据: 1286条记录
- ✅ 数据结构正确
- ✅ 有PE、PB、ROE等关键指标

### 修改位置
`backend/database/models.py` 和 `backend/services/fundamental_analyzer.py`

### 修复方案

#### 方案A: 更新模型定义（推荐）

在 `backend/database/models.py` 中更新 FundamentalMetrics 模型:

```python
class FundamentalMetrics(Base):
    __tablename__ = 'fundamental_metrics'
    
    # 基础字段
    id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False)
    report_date = Column(Date)
    created_at = Column(DateTime)
    
    # 估值指标
    pe_ttm = Column(Numeric(10, 2))
    pe_lyr = Column(Numeric(10, 2))
    pb = Column(Numeric(10, 2))
    
    # 成长指标
    revenue_cagr_3y = Column(Numeric(10, 4))
    profit_cagr_3y = Column(Numeric(10, 4))
    
    # 财务健康指标
    roe = Column(Numeric(10, 4))
    debt_ratio = Column(Numeric(10, 4))
    
    # 评分字段
    valuation_score = Column(Numeric(10, 2))
    growth_score = Column(Numeric(10, 2))
    financial_health_score = Column(Numeric(10, 2))
    overall_score = Column(Numeric(10, 2))
```

#### 方案B: 更新服务层代码

在 `backend/services/fundamental_analyzer.py` 中修改查询和数据组装:

**修改前** ❌:
```python
# 直接返回数据库对象（期望有JSON字段）
metrics = await session.execute(
    select(FundamentalMetrics).where(...)
)
return metrics.scalar_one_or_none()
```

**修改后** ✅:
```python
# 查询数据库
stmt = select(FundamentalMetrics).where(
    FundamentalMetrics.stock_code == stock_code
).order_by(desc(FundamentalMetrics.report_date)).limit(1)

result = await session.execute(stmt)
metrics = result.scalar_one_or_none()

if metrics:
    # ✅ 组装成前端期望的JSON格式
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
```

### 需要修改的文件
- [ ] `backend/database/models.py` - 更新FundamentalMetrics模型
- [ ] `backend/services/fundamental_analyzer.py` - 修改查询和数据组装逻辑

---

## 预计修复时间

- 美股数据库查询: **5分钟**
- A股代码转换: **10分钟**
- 深证指数处理: **15分钟**
- **财务数据模型**: **15分钟** ⚠️ 新增
- 测试验证: **10分钟**

**总计**: 约 **55分钟**

---

## 修改文件清单（完整）

### 必须修改
- [ ] `backend/services/us_market_analyzer.py` - 替换 `symbol` 为 `us_stock_code`
- [ ] `backend/utils/index_code_converter.py` - 新建代码转换工具
- [ ] `backend/routers/stock.py` - 添加代码格式转换
- [ ] `backend/services/akshare_service.py` - 处理指数代码格式
- [ ] **`backend/database/models.py`** - 更新财务数据模型 ⚠️ 新增
- [ ] **`backend/services/fundamental_analyzer.py`** - 修改财务数据查询 ⚠️ 新增

### 建议优化
- [ ] 优化VIX数据源获取
- [ ] 添加深证指数专门处理
- [ ] 完善错误处理和日志

---

**创建时间**: 2026-03-09 20:00  
**更新时间**: 2026-03-09 20:20  
**状态**: ✅ 测试验证通过，发现财务数据问题，可以执行
