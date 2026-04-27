# 股票数据源测试文件

本目录包含市场情绪数据多数据源方案的测试和验证脚本。

## 📁 文件说明

### 主要测试文件

#### `test_market_sentiment_multisource.py` ⭐
**多数据源完整测试脚本**
- 测试Tushare数据源
- 测试AKShare数据源
- 测试缓存机制
- 测试API端点
- **用途**: 完整的功能验证

#### `test_tushare_daily.py` ⭐
**Tushare daily接口专项测试**
- 测试daily接口权限
- 测试最近交易日回退
- 显示详细涨跌统计
- **用途**: Tushare数据源调试

#### `test_akshare_market_sentiment.py`
**AKShare市场情绪测试**
- 测试东方财富接口
- 测试腾讯财经接口
- 验证数据完整性
- **用途**: AKShare数据源调试

---

### 辅助测试文件

#### `check_cache.py`
**缓存数据检查工具**
- 查看数据库缓存
- 显示最新市场情绪数据
- **用途**: 调试缓存机制

#### `fix_akshare_proxy.py`
**AKShare代理修复工具**
- 修复代理连接问题
- 网络诊断
- **用途**: 解决网络问题

---

### 其他测试文件

- `test_market_sentiment_5000.py` - 5000只股票数据测试
- `test_market_sentiment_full.py` - 完整市场情绪测试
- `test_akshare_connection.py` - AKShare连接测试
- `test_alternative_apis.py` - 备用API测试
- `test_network.py` - 网络连接测试
- `test_new_api.py` - 新API测试
- `test_sina_api.py` - 新浪API测试

---

## 🚀 快速使用

### 完整测试
```bash
# 运行完整的多数据源测试
python test_market_sentiment_multisource.py
```

### Tushare测试
```bash
# 测试Tushare daily接口
python test_tushare_daily.py
```

### AKShare测试
```bash
# 测试AKShare数据源
python test_akshare_market_sentiment.py
```

### 检查缓存
```bash
# 查看数据库缓存数据
python check_cache.py
```

---

## 📊 测试结果示例

### Tushare成功示例
```
[OK] Tushare Token 已配置
[OK] Tushare 服务可用
[OK] 获取成功:
  - 总股票数: 5481
  - 上涨家数: 1502
  - 下跌家数: 3828
  - 涨停家数: 69
  - 跌停家数: 22
  - 市场宽度: 27.4%
  - 数据质量: full
```

### AKShare失败示例（非交易时间）
```
[FAIL] 东方财富: 不可用
[FAIL] 腾讯财经: 不可用
原因: 非交易时间，网络API不稳定
```

---

## ⚙️ 配置要求

### 环境变量
确保以下配置正确：
```env
# backend/.env
TUSHARE_TOKEN=your_tushare_token_here
```

### 依赖包
```bash
pip install akshare tushare pandas
```

---

## 📝 注意事项

1. **交易时间测试**
   - AKShare在交易时间更稳定
   - 建议在9:30-15:00测试

2. **Tushare权限**
   - 需要500+积分才能使用daily接口
   - 2100积分可访问所有接口

3. **网络环境**
   - 检查代理设置
   - 确保网络畅通

4. **数据质量**
   - 完整数据: >=5000只股票
   - 部分数据: <5000只股票

---

## 📚 相关文档

- [市场情绪数据多数据源方案](../../backend/市场情绪数据多数据源方案.md)
- [涨跌分布数据完整分析报告](../../backend/涨跌分布数据完整分析报告.md)
- [检查代理设置](../../backend/检查代理设置.md)

---

## 🔧 故障排查

### 问题1: Tushare无权限
```
解决: 确认Tushare积分 >= 500
升级: 访问 https://tushare.pro 积分商城
```

### 问题2: AKShare连接失败
```
解决: 检查网络代理设置
测试: 在交易时间重新测试
```

### 问题3: 缓存数据不足
```
解决: 运行测试脚本更新缓存
检查: 数据库连接是否正常
```

---

**最后更新**: 2026-03-14
**版本**: v1.0
**维护**: Stock-PEG Team
