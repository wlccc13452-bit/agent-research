# Datasource 模块测试文档

## 测试目标

确保 datasource 模块的稳定性、正确性和性能。

## 测试范围

### 1. 核心组件测试

#### DataSourceManager
- ✅ 单例模式验证
- ✅ 数据源注册和初始化
- ✅ 数据源获取方法
- ✅ Facade 便捷方法

#### SmartRouter
- ✅ 优先级路由
- ✅ 失败自动切换
- ✅ 可用性检查

#### UnifiedRateLimiter
- ✅ 限流检查
- ✅ 调用记录
- ✅ 限流策略

#### CallRecorder
- ✅ 成功调用记录
- ✅ 失败调用记录
- ✅ 统计数据计算
- ✅ 平均响应时间

### 2. 数据源测试

#### AkshareDataSource
- ✅ 数据源类型和优先级
- ✅ 可用性检查
- ✅ 实时行情获取（mock）
- ✅ K线数据获取（mock）
- ✅ 失败缓存机制

### 3. 集成测试

- ✅ 完整工作流测试
- ✅ Fallback 机制测试

## 运行测试

### 快速测试

```bash
cd backend
python test/run_datasource_tests.py
```

### 详细输出

```bash
python test/run_datasource_tests.py --verbose
```

### 覆盖率报告

```bash
python test/run_datasource_tests.py --coverage
```

覆盖率报告将生成在 `backend/htmlcov/index.html`

## 测试策略

### 1. 单元测试

- 每个类和方法都有独立的测试
- 使用 mock 避免实际网络调用
- 测试边界条件和异常情况

### 2. 集成测试

- 测试组件之间的协作
- 测试完整的数据流
- 测试 fallback 机制

### 3. 性能测试（待添加）

- 并发调用测试
- 限流效果测试
- 内存使用测试

## 测试数据

### Mock 数据格式

#### 实时行情
```python
{
    '代码': '600219',
    '名称': '南山铝业',
    '最新价': 10.5,
    '涨跌幅': 2.5,
    '成交量': 1000000
}
```

#### K线数据
```python
{
    '日期': '2026-03-22',
    '开盘': 10.0,
    '收盘': 10.5,
    '最高': 10.6,
    '最低': 9.9,
    '成交量': 1000000
}
```

## 测试覆盖率目标

| 模块 | 目标覆盖率 | 当前覆盖率 |
|------|------------|------------|
| core/manager.py | 80% | 待测试 |
| core/smart_router.py | 85% | 待测试 |
| core/rate_limiter.py | 80% | 待测试 |
| core/call_recorder.py | 90% | 待测试 |
| sources/akshare_source.py | 75% | 待测试 |

## 持续集成

建议在 CI/CD 流程中添加自动测试：

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      - name: Run tests
        run: |
          cd backend
          python test/run_datasource_tests.py --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 常见问题

### Q: 测试时出现导入错误？

A: 确保在 `backend` 目录下运行测试，或设置 `PYTHONPATH`：

```bash
export PYTHONPATH=/path/to/backend
python test/test_datasource.py
```

### Q: 如何测试异步方法？

A: 使用 `pytest-asyncio` 并在测试方法上添加 `@pytest.mark.asyncio` 装饰器。

### Q: 如何跳过需要网络的测试？

A: 所有测试都使用 mock，避免实际网络调用。如果需要测试真实网络，可以添加 `@pytest.mark.integration` 标记。

## 下一步

- [ ] 添加更多边界条件测试
- [ ] 添加性能基准测试
- [ ] 集成到 CI/CD 流程
- [ ] 添加 E2E 测试

---

**文档版本**: v1.0
**更新日期**: 2026-03-22
