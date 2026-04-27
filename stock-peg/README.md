# Stock PEG - 智能股票分析平台

以**自持股票.md为核心**的智能股票分析平台，通过实时监控、多维分析、AI预测和国际市场联动，为用户提供全方位的投资决策支持。

## 项目结构

```
stock-peg/
├── backend/              # 后端服务 (Python FastAPI + UV)
│   ├── config/          # 配置文件
│   ├── database/        # 数据库模型和会话管理
│   ├── models/          # Pydantic数据模型
│   ├── routers/         # API路由
│   │   ├── holding.py   # 持仓管理路由
│   │   └── stock.py     # 股票行情路由
│   ├── services/        # 业务服务
│   │   ├── holding_manager.py  # 持仓管理服务
│   │   └── stock_service.py    # 股票数据服务
│   ├── data/            # 数据存储 (SQLite)
│   ├── main.py          # FastAPI入口
│   ├── pyproject.toml   # UV项目配置
│   └── .python-version  # Python版本
├── frontend/            # 前端应用 (React + TypeScript + Vite)
│   ├── src/
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
└── 自持股票.md          # 持仓配置文件（核心数据源）

```

## 核心功能

### 1. 持仓管理（已完成）
- 以自持股票.md为唯一数据源
- 支持动态增删改查持仓股票
- 自动识别板块和股票代码
- 文件变更实时监控

### 2. A股实时监控（已完成基础）
- 实时行情推送（腾讯股票API）
- K线图表展示
- 技术指标计算（MA/MACD/RSI/KDJ）

### 3. 基本面财务分析（待实现）
- PEG/PE/PS/PB估值指标
- 成长性分析（营收/利润CAGR）
- 财务健康度评估
- 市场价格趋势分析

### 4. 美国市场联动分析（待实现）
- AI识别相关美股标的
- 昨日美股AI分析
- 中美市场联动预测

### 5. 明日行情预测（待实现）
- 板块轮动分析
- 多维度数据整合
- LightGBM预测模型

### 6. 每日分析报告（待实现）
- 自动生成分析报告
- 历史查询和对比
- 预测准确性验证

## 技术栈

### 后端
- **框架**: FastAPI (Python)
- **包管理**: UV
- **数据库**: SQLite + SQLAlchemy
- **数据源**: 腾讯股票API、东方财富API、Tushare
- **AI分析**: OpenAI/Claude API、LightGBM

### 前端
- **框架**: React 19 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **数据请求**: TanStack Query
- **图表**: ECharts

## 快速开始

### 后端启动

```bash
cd backend

# 使用UV安装依赖（推荐）
uv sync

# 或使用pip
pip install -r requirements.txt

# 启动开发服务器
python main.py
```

后端服务将在 `http://localhost:8000` 运行

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将在 `http://localhost:5173` 运行

## API文档

启动后端服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 配置

### 后端配置

在 `backend/config/.env` 文件中配置：

```env
# Tushare Token (财务数据)
TUSHARE_TOKEN=your_token

# OpenAI API Key (AI分析)
OPENAI_API_KEY=your_key

# Anthropic API Key (Claude AI)
ANTHROPIC_API_KEY=your_key
```

## 开发计划

- [x] 后端基础架构
- [x] 持仓管理服务
- [x] 股票数据服务
- [ ] 基本面分析服务
- [ ] 美股市场分析服务
- [ ] 预测引擎
- [ ] 报告生成服务
- [x] 前端基础架构
- [ ] 前端持仓管理页面
- [ ] 前端实时监控页面
- [ ] 前端基本面分析页面
- [ ] 前端预测看板

## 许可证

MIT
