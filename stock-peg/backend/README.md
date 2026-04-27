# 统一数据源架构使用指南

## 概述

本项目已升级为统一数据源架构，所有外部数据调用统一通过 `backend/datasource/` 模块。

### 核心特性

1. **统一接口** - 所有数据源实现相同的基类接口
2. **功能注册制** - 数据源只实现支持的功能，使用装饰器标记
3. **智能路由** - 自动选择最优数据源（基于历史成功率、响应时间、优先级）
4. **熔断保护** - 连续失败后自动熔断，避免无效调用
5. **适配器模式** - 现有 services 无需重写，通过适配器包装接入
6. **Facade便捷方法** - `get_realtime_quote()`, `get_kline()`, `get_market_sentiment()` 等

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    DataSourceManager                        │
│  (统一入口，智能路由，熔断保护，Facade方法)                  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ SmartRouter  │   │ CallRecorder │   │ UnifiedRate  │
│  (智能选择)   │   │  (统计记录)  │   │  Limiter     │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
    ┌──────────┬────────┬───┴────┬──────────┬──────────┐
    │          │        │        │          │          │
    ▼          ▼        ▼        ▼          ▼          ▼
┌────────┐┌────────┐┌──────┐┌──────┐┌────────┐┌────────┐
│Tushare ││Akshare ││Tencent││East- ││USMarket││Adapters│
│ (10)   ││(30)    ││(20)  ││money ││(50)    ││(30-60) │
└────────┘└────────┘└──────┘└──────┘└────────┘└────────┘
```

## 数据源列表

| 数据源 | 优先级 | 说明 |
|--------|--------|------|
| Tushare | 10 | 付费API，数据最全面 |
| FundamentalAnalyzerAdapter | 15 | Tushare财务数据补充 |
| Tencent | 20 | 免费，实时行情首选 |
| AkshareDataSource | 20 | AKShare完整实现（40+方法） |
| Eastmoney | 40 | 东方财富资金流等 |
| USMarketDataSource | 50 | 美股数据（多源级联） |
| NewsServiceAdapter | 60 | 新闻数据 |

## 快速开始

### 1. 获取数据源管理器

```python
from datasource import get_datasource

# 获取管理器实例（自动初始化）
manager = get_datasource()
```

### 2. 使用 Facade 便捷方法

```python
from datasource import get_datasource

manager = get_datasource()

# 获取实时行情
quote = await manager.get_realtime_quote("600219")

# 获取K线
kline = await manager.get_kline("600219", period="day", count=120)

# 获取市场情绪
sentiment = await manager.get_market_sentiment()
```

### 3. 按功能类型调用（自动路由）

```python
from datasource import get_datasource, FunctionType

manager = get_datasource()

# 自动选择最优数据源
result = await manager.call(FunctionType.REALTIME_QUOTE, stock_code="600219")
result = await manager.call(FunctionType.KLINE_DAILY, stock_code="600219", count=100)
```

## 添加新数据源

### 1. 创建数据源类

```python
from datasource import BaseDataSource, provider
from datasource import FunctionType, DataSourceType

class MyDataSource(BaseDataSource):
    """自定义数据源"""
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.MY_SOURCE
    
    @property
    def priority(self) -> int:
        return 25
    
    async def is_available(self) -> bool:
        return True
    
    @provider(FunctionType.REALTIME_QUOTE)
    async def get_realtime_quote(self, stock_code: str):
        data = await self._fetch_data(stock_code)
        return data
```

### 2. 注册数据源

在 `datasource/__init__.py` 的 `init_datasources()` 中添加实例并注册。

## 相关文件

- `datasource/__init__.py` - 统一入口，`get_datasource()` 全局访问
- `datasource/core/` - 基础设施（基类、装饰器、路由、统计、限速）
- `datasource/sources/` - 数据源实现
- `datasource/sources/adapters.py` - 服务适配器（包装现有 services）
