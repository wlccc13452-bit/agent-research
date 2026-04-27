# Force Index 实现说明

## 完成内容

### 1. 核心服务 (`backend/services/force_index_calculator.py`)

**功能**:
- 计算Alexander Elder强力指数（Force Index）
- 生成买卖信号（强度评分 -10 到 +10）
- 分析趋势方向和强度
- 分析买卖力量平衡

**数据获取优先级**:
1. 本地数据库 (stock_kline_data表)
2. 内存缓存 (kline_cache)
3. 网络API (stock_service)

### 2. API路由 (`backend/routers/force_index.py`)

**端点**:

#### 单只股票分析
```
GET /api/indicators/force-index/{stock_code_or_name}
```

**参数**:
- `stock_code_or_name`: 股票代码或名称（如"000001"或"平安银行"）
- `period`: K线周期，默认"day"
- `ema_short`: 短期EMA周期，默认2
- `ema_long`: 长期EMA周期，默认13
- `count`: K线数量，默认100

**示例**:
```bash
# 使用股票代码
curl http://localhost:8000/api/indicators/force-index/000001

# 使用股票名称
curl http://localhost:8000/api/indicators/force-index/平安银行

# 自定义参数
curl "http://localhost:8000/api/indicators/force-index/600519?period=day&ema_short=2&ema_long=13"
```

#### 批量分析
```
GET /api/indicators/force-index-batch
```

**示例**:
```bash
curl http://localhost:8000/api/indicators/force-index-batch?period=day
```

### 3. SKILL文档 (`skills/indicators/force-index/SKILL.md`)

完整的技能文档，包含:
- 指标说明
- 使用方法
- 返回数据结构
- 实际应用示例
- 注意事项

## 测试结果

已通过实际股票数据测试:
- ✅ 平安银行 (000001) - 信号: 偏强
- ✅ 贵州茅台 (600519) - 信号: 偏弱
- ✅ 五粮液 (000858) - 信号: 偏强

## 使用示例

### Python调用
```python
import requests

# 分析单只股票
response = requests.get("http://localhost:8000/api/indicators/force-index/平安银行")
result = response.json()

print(f"股票: {result['stock_name']}")
print(f"信号: {result['signals']['current_signal']}")
print(f"强度: {result['signals']['signal_strength']}")
print(f"趋势: {result['trend_analysis']['trend_direction']}")
```

### 前端集成
```typescript
// 获取Force Index分析
const response = await fetch('/api/indicators/force-index/平安银行');
const data = await response.json();

// 显示信号
console.log('信号:', data.signals.current_signal);
console.log('强度:', data.signals.signal_strength);
```

## 下一步建议

1. **前端展示**: 创建Force Index分析页面
2. **预警集成**: 将Force Index信号加入预警系统
3. **组合分析**: 结合PMR等其他指标进行综合分析
4. **数据可视化**: 绘制Force Index指标图表

## 相关文件

- 计算服务: `backend/services/force_index_calculator.py`
- API路由: `backend/routers/force_index.py`
- 技能文档: `skills/indicators/force-index/SKILL.md`
- 测试脚本: `backend/test_force_index.py`
- 进度记录: `progress.md`
