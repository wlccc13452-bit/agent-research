# LLM智能评估报告功能说明

## 功能概述

LLM智能评估报告功能是一个基于大语言模型（LLM）的股票智能分析工具，能够自动收集股票的多维度数据，并生成专业的投资评估报告。

## 核心特性

### 1. 多维度数据收集
- **K线数据**：最近20天的股价、成交量数据
- **技术指标**：MA5/MA10/MA20/MA30/MA60/MA120、EMA20/EMA60/EMA120、MACD、RSI、KDJ
- **指数数据**：上证指数、深证指数实时数据
- **财务数据**：PE、PB、ROE等财务指标
- **新闻数据**：相关股票和公司新闻

### 2. LLM智能分析
- **技术面分析**：趋势判断、支撑压力位、成交量分析
- **基本面分析**：估值评估、盈利能力、成长潜力
- **市场环境分析**：大盘走势、市场情绪
- **消息面分析**：新闻影响、情绪判断
- **交易建议**：买卖点判断、价格区间、止损止盈
- **风险评估**：风险等级、风险因素

### 3. 报告生成与保存
- 自动生成Markdown格式报告
- 保存到 `backend/data/llm_reports/` 目录
- 支持历史报告查看

## 使用方法

### 方式一：前端界面使用

1. **选择股票**：在左侧面板选择要分析的股票
2. **生成报告**：
   - 在右侧面板的"智能"标签页
   - 点击"分析报告"卡片中的"AI评估"按钮（紫色按钮）
3. **查看进度**：
   - 实时显示生成进度
   - WebSocket推送进度更新
4. **查看报告**：
   - 生成完成后自动显示摘要
   - 点击"查看完整报告"在新窗口查看

### 方式二：API调用

```bash
# 生成LLM报告
curl -X POST http://localhost:8000/api/reports/llm/generate \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600219",
    "stock_name": "南山铝业",
    "days": 20
  }'

# 获取LLM报告列表
curl http://localhost:8000/api/reports/llm/list?stock_code=600219

# 获取报告内容
curl http://localhost:8000/api/reports/llm/content/600219_南山铝业_20260310_075206.md
```

## 报告示例

```markdown
# LLM智能评估报告

**股票代码**: 600219
**股票名称**: 南山铝业
**分析日期**: 2026-03-10T07:51:38
**综合评级**: 中性
**置信度**: 75%

---

## 技术面分析

**趋势判断**: 震荡
**趋势强度**: 中
**支撑位**: 7.25
**压力位**: 7.85
**成交量趋势**: 平稳

**技术指标总结**:
股价在7.25-7.85区间震荡，MACD显示多头信号但力度较弱...

---

## 交易建议

**操作建议**: 持有

**买入价格区间**: [7.25, 7.40]
**卖出价格区间**: [7.80, 7.95]
**止损价位**: 7.00
**止盈价位**: 8.20
**建议仓位**: 50%
**持仓周期**: 中期

---

## 风险评估

**风险等级**: 中

**风险因素**:
1. 市场整体震荡风险
2. 行业周期性波动

**风险提示**: 建议设置止损位，控制仓位...
```

## 配置要求

### 1. 智谱AI配置

在 `backend/config/.env` 文件中配置：

```env
# 智谱AI配置
AI_DEFAULT_PROVIDER=zhipu
AI_DEFAULT_MODEL=glm-4
ZHIPU_API_KEY=your_zhipu_api_key_here
```

### 2. 数据源配置

确保以下数据源配置正确：
- Tushare Token（财务数据）
- 新闻API（消息面分析）

## 技术架构

### 后端服务
- `services/llm_report_service.py`：核心服务
  - 数据收集
  - LLM调用
  - 报告生成
  - 文件管理

### API端点
- `POST /api/reports/llm/generate`：生成报告
- `GET /api/reports/llm/list`：获取报告列表
- `GET /api/reports/llm/content/{file_name}`：获取报告内容

### 前端组件
- `components/SmartAnalysisTab.tsx`：智能分析标签页
  - "AI评估"按钮
  - 进度显示
  - 报告预览
  - 历史报告列表

### WebSocket事件
- `llm_report_progress`：进度更新
- `llm_report_completed`：报告完成
- `llm_report_error`：生成失败

## 注意事项

1. **API Key安全**：
   - 不要在代码中硬编码API Key
   - 使用环境变量或配置文件管理

2. **性能优化**：
   - 报告生成耗时约30-60秒
   - 建议在后台任务中执行
   - 使用WebSocket推送进度

3. **数据时效性**：
   - K线数据、技术指标实时更新
   - 财务数据可能有延迟
   - 新闻数据实时获取

4. **费用控制**：
   - 每次生成报告会调用智谱AI API
   - 注意Token使用量和费用

## 测试验证

运行测试脚本验证功能：

```bash
cd d:/2026projects/stocks-research/stock-peg
d:/2026projects/stocks-research/stock-peg/backend/.venv/Scripts/python.exe test/LLM/test_llm_report_v2.py
```

测试内容包括：
- ✅ 数据收集（5项）
- ✅ LLM调用
- ✅ 报告生成
- ✅ 文件保存

## 未来扩展

1. **多模型支持**：支持OpenAI、Claude等其他LLM
2. **报告模板**：支持自定义报告模板
3. **批量生成**：为所有持仓股票批量生成报告
4. **定时生成**：定时自动生成报告
5. **报告对比**：对比不同时期的报告变化

## 常见问题

**Q: 为什么报告生成速度较慢？**
A: 报告生成需要调用多个数据API和LLM API，建议在后台任务中执行。

**Q: 如何查看历史报告？**
A: 报告保存在 `backend/data/llm_reports/` 目录，可以通过API或前端界面查看。

**Q: 报告可以自定义吗？**
A: 目前使用固定模板，未来版本将支持自定义模板。

**Q: 如何获取智谱AI API Key？**
A: 访问 https://open.bigmodel.cn/ 注册并获取API Key。

## 联系支持

如有问题或建议，请联系开发团队。
