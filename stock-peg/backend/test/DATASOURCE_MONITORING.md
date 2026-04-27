# Datasource 监控和优化指南

## 概述

利用 `CallRecorder` 和 `SmartRouter` 的统计数据，分析调用热点，优化性能。

## 监控指标

### 1. 调用统计

```python
from datasource.core.call_recorder import CallRecorder

recorder = CallRecorder()

# 获取统计数据
stats = recorder.get_statistics(DataSourceType.AKSHARE)

print(f"总调用次数: {stats['total_calls']}")
print(f"成功次数: {stats['success_calls']}")
print(f"失败次数: {stats['failed_calls']}")
print(f"成功率: {stats['success_rate']:.1%}")
print(f"平均响应时间: {stats['avg_duration']:.2f}s")
```

### 2. 热点分析

```python
# 获取调用热点
hotspots = recorder.get_function_hotspots(DataSourceType.AKSHARE)

for func_type, count in hotspots:
    print(f"{func_type.value}: {count} 次调用")
```

### 3. 错误分析

```python
# 获取错误统计
errors = recorder.get_error_statistics(DataSourceType.AKSHARE)

for error_type, count in errors.items():
    print(f"{error_type}: {count} 次")
```

## 性能优化策略

### 1. 缓存优化

**问题**: 重复调用相同数据

**解决方案**: 使用 `services/extended_cache.py` 的缓存机制

```python
from services.extended_cache import quote_cache

# 缓存实时行情（5分钟有效期）
@quote_cache.cache(expire=300)
async def get_quote_cached(stock_code: str):
    return await akshare_source.get_realtime_quote(stock_code)
```

### 2. 批量请求优化

**问题**: 多次单独请求效率低

**解决方案**: 使用批量 API

```python
# 批量获取行情
async def get_quotes_batch(stock_codes: List[str]):
    # 使用 AkshareDataSource 的批量方法（如果有）
    # 或使用 asyncio.gather 并发请求
    tasks = [get_realtime_quote(code) for code in stock_codes]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### 3. 限流优化

**问题**: API 调用频率过高被限流

**解决方案**: 调整 `UnifiedRateLimiter` 参数

```python
from datasource.core.rate_limiter import UnifiedRateLimiter

# 自定义限流策略
limiter = UnifiedRateLimiter()

# Tushare: 200次/分钟
limiter.set_limit(DataSourceType.TUSHARE, max_calls=200, period=60)

# Akshare: 100次/分钟
limiter.set_limit(DataSourceType.AKSHARE, max_calls=100, period=60)
```

### 4. 熔断优化

**问题**: 连续失败后继续尝试浪费时间

**解决方案**: 调整熔断阈值

```python
from datasource.core.smart_router import SmartRouter

router = SmartRouter()

# 设置熔断阈值：连续失败 3 次后熔断
router.set_circuit_breaker_threshold(failure_threshold=3)

# 设置熔断恢复时间：5分钟后尝试恢复
router.set_circuit_breaker_timeout(recovery_timeout=300)
```

## 监控仪表板（示例）

### 1. 实时监控脚本

```python
#!/usr/bin/env python3
"""实时监控 datasource 调用"""
import asyncio
from datetime import datetime
from datasource.core.call_recorder import CallRecorder
from datasource import get_datasource, DataSourceType

async def monitor():
    recorder = CallRecorder()
    
    while True:
        # 清屏
        print("\033[2J\033[H", end="")
        
        print("=" * 60)
        print(f"Datasource 监控仪表板 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 显示各数据源统计
        for source_type in [DataSourceType.TUSHARE, DataSourceType.AKSHARE, 
                           DataSourceType.TENCENT, DataSourceType.EASTMONEY]:
            stats = recorder.get_statistics(source_type)
            if stats and stats['total_calls'] > 0:
                print(f"\n{source_type.value.upper()}:")
                print(f"  总调用: {stats['total_calls']}")
                print(f"  成功率: {stats['success_rate']:.1%}")
                print(f"  平均响应: {stats['avg_duration']:.2f}s")
        
        # 显示热点函数
        print("\n热点函数:")
        hotspots = recorder.get_function_hotspots(limit=5)
        for func_type, count in hotspots:
            print(f"  {func_type.value}: {count} 次")
        
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(monitor())
```

### 2. 日志分析脚本

```bash
#!/bin/bash
# 分析 datasource 日志

LOG_FILE="logs/datasource.log"

echo "Datasource 日志分析"
echo "=================="

# 统计调用次数
echo -e "\n调用次数统计:"
grep "datasource call" $LOG_FILE | wc -l

# 统计成功率
echo -e "\n成功/失败统计:"
echo "成功: $(grep "success" $LOG_FILE | wc -l)"
echo "失败: $(grep "error" $LOG_FILE | wc -l)"

# 平均响应时间
echo -e "\n平均响应时间:"
grep "duration" $LOG_FILE | awk '{sum+=$NF; count++} END {print sum/count "ms"}'
```

## 性能基准测试

### 1. 响应时间测试

```python
import time
import asyncio
from datasource import get_datasource, DataSourceType

async def benchmark_response_time():
    manager = get_datasource()
    source = manager.get_source(DataSourceType.AKSHARE)
    
    # 测试 100 次调用
    durations = []
    for _ in range(100):
        start = time.time()
        await source.get_realtime_quote('600219')
        duration = time.time() - start
        durations.append(duration)
    
    avg = sum(durations) / len(durations)
    min_d = min(durations)
    max_d = max(durations)
    
    print(f"平均响应时间: {avg:.3f}s")
    print(f"最小响应时间: {min_d:.3f}s")
    print(f"最大响应时间: {max_d:.3f}s")

asyncio.run(benchmark_response_time())
```

### 2. 并发测试

```python
async def benchmark_concurrency():
    manager = get_datasource()
    source = manager.get_source(DataSourceType.AKSHARE)
    
    # 并发 50 个请求
    tasks = [source.get_realtime_quote('600219') for _ in range(50)]
    
    start = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.time() - start
    
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    
    print(f"总耗时: {duration:.3f}s")
    print(f"成功率: {success_count}/{len(results)}")
    print(f"平均每个请求: {duration/len(results):.3f}s")

asyncio.run(benchmark_concurrency())
```

## 优化检查清单

### 日常优化

- [ ] 检查 CallRecorder 统计数据
- [ ] 识别调用热点
- [ ] 分析错误日志
- [ ] 调整限流参数

### 定期优化

- [ ] 性能基准测试
- [ ] 并发压力测试
- [ ] 内存使用分析
- [ ] 数据源可用性检查

### 架构优化

- [ ] 评估数据源优先级
- [ ] 优化 fallback 策略
- [ ] 调整熔断阈值
- [ ] 增加缓存命中率

## 监控告警

### 告警规则示例

```python
# 告警配置
ALERT_RULES = {
    'high_error_rate': {
        'condition': 'success_rate < 0.8',
        'message': '成功率低于 80%'
    },
    'slow_response': {
        'condition': 'avg_duration > 2.0',
        'message': '平均响应时间超过 2 秒'
    },
    'circuit_breaker_triggered': {
        'condition': 'circuit_breaker_count > 0',
        'message': '熔断器被触发'
    }
}

# 检查告警
def check_alerts():
    recorder = CallRecorder()
    
    for source_type in DataSourceType:
        stats = recorder.get_statistics(source_type)
        
        if stats['success_rate'] < 0.8:
            send_alert(f"{source_type.value} 成功率过低: {stats['success_rate']:.1%}")
        
        if stats['avg_duration'] > 2.0:
            send_alert(f"{source_type.value} 响应过慢: {stats['avg_duration']:.2f}s")
```

---

**文档版本**: v1.0
**更新日期**: 2026-03-22
