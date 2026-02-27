# Agentic Finance Review 架构与框架研究

## 项目概述

**Agentic Finance Review** 是一个基于 Claude Code 的自治财务审查系统，核心创新点是**专业化自验证代理（Specialized Self-Validating Agents）**。

**核心理念：**
```
Focused Agent + Specialized Validation = Trusted Automation
```

如果代理能够自主验证其工作，就能建立信任，从而节省工程师最宝贵的资源——时间。

---

## 1. 整体架构

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Agentic Finance Review System                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Orchestrator (review-finances.md)                │   │
│  │                      /review-finances <month> <csvs>                │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                          │
│                                 ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Agent Pipeline (串行)                         │   │
│  │                                                                      │   │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │   │
│  │  │  normalize   │──▶│  categorize  │──▶│    merge     │            │   │
│  │  │  csv-agent   │   │  csv-agent   │   │  accounts    │            │   │
│  │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘            │   │
│  │         │                  │                  │                     │   │
│  │         ▼                  ▼                  ▼                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │                    Validators (Hook System)                  │  │   │
│  │  │  • csv-validator.py (CSV 结构验证)                           │  │   │
│  │  │  • normalized-balance-validator.py (余额一致性验证)           │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │   │
│  │  │  accumulate  │──▶│    graph     │──▶│ generative   │            │   │
│  │  │    csvs      │   │   agent      │   │  ui-agent    │            │   │
│  │  └──────────────┘   └──────────────┘   └──────────────┘            │   │
│  │                                                 │                   │   │
│  │                                                 ▼                   │   │
│  │                                    ┌──────────────────────┐        │   │
│  │                                    │   html-validator.py  │        │   │
│  │                                    │   graph-validator.py │        │   │
│  │                                    └──────────────────────┘        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Commands (Slash Commands)                       │   │
│  │  /csv-edit  /normalize-csv  /categorize-csv  /merge-accounts       │   │
│  │  /accumulate-csvs  /graph-insights  /generative-ui  /build         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Validators (Hook Scripts)                       │   │
│  │  • csv-single-validator.py    • csv-validator.py                    │   │
│  │  • html-validator.py          • graph-validator.py                  │   │
│  │  • normalized-balance-validator.py  • ruff-validator.py             │   │
│  │  • ty-validator.py            • demo-validator.py                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Data Flow Pipeline                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT                                                                      │
│  ┌─────────────────┐     ┌─────────────────┐                               │
│  │ raw_checkings   │     │ raw_savings     │   (原始银行 CSV 导出)          │
│  │     *.csv       │     │     *.csv       │                               │
│  └────────┬────────┘     └────────┬────────┘                               │
│           │                       │                                         │
│           ▼                       ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Stage 1: NORMALIZE                                                  │   │
│  │ • 转换为标准列格式: date, description, category, deposit,          │   │
│  │   withdrawal, balance, account_name                                 │   │
│  │ • 输出: normalized_*.csv                                            │   │
│  └────────────────────────────┬────────────────────────────────────────┘   │
│                               │                                             │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Stage 2: CATEGORIZE                                                 │   │
│  │ • 自动分类交易: groceries, utilities, entertainment, etc.           │   │
│  │ • 输出: normalized_*.csv (category 列填充)                          │   │
│  └────────────────────────────┬────────────────────────────────────────┘   │
│                               │                                             │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Stage 3: MERGE                                                      │   │
│  │ • 合并所有账户到单一数据集                                           │   │
│  │ • 输出: agentic_merged_transactions.csv                             │   │
│  └────────────────────────────┬────────────────────────────────────────┘   │
│                               │                                             │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Stage 4: ACCUMULATE                                                 │   │
│  │ • 添加到年度累计文件                                                 │   │
│  │ • 输出: agentic_cumulative_dataset_2026.csv                         │   │
│  └────────────────────────────┬────────────────────────────────────────┘   │
│                               │                                             │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Stage 5: GRAPH                                                      │   │
│  │ • 生成 8 个财务可视化图表                                            │   │
│  │ • 输出: assets/*.png (月度 + 年度)                                  │   │
│  └────────────────────────────┬────────────────────────────────────────┘   │
│                               │                                             │
│                               ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Stage 6: DASHBOARD                                                  │   │
│  │ • 创建交互式 HTML 报告                                               │   │
│  │ • 输出: index.html (月度 + 年度)                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  OUTPUT                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ apps/agentic-finance-review/data/mock_dataset_2026/                 │   │
│  │ ├── agentic_cumulative_dataset_2026.csv                             │   │
│  │ ├── index.html (年度 dashboard)                                     │   │
│  │ ├── assets/ (年度图表)                                              │   │
│  │ └── mock_dataset_mar_1st_2026/                                      │   │
│  │     ├── raw_checkings.csv                                           │   │
│  │     ├── normalized_checkings.csv                                    │   │
│  │     ├── agentic_merged_transactions.csv                             │   │
│  │     ├── index.html (月度 dashboard)                                 │   │
│  │     └── assets/ (月度图表)                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心框架组件

### 2.1 Claude Code Hooks 系统

这是项目的核心创新点。Hooks 允许在特定事件点注入验证逻辑。

**Hook 类型：**

| Hook 事件 | 触发时机 | 用途 |
|-----------|---------|------|
| `PreToolUse` | 工具执行前 | 阻止危险操作 |
| `PostToolUse` | 工具执行后 | 验证输出 |
| `Stop` | Agent 完成时 | 最终验证/清理 |

**专业化 Hooks：**
```yaml
# 关键创新：Hooks 现在可以嵌入到特定 agent 的 prompt 中
# 而非全局 settings.json
hooks:
  PostToolUse:
    - matcher: "Read|Edit|Write"
      hooks:
        - type: command
          command: "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/csv-single-validator.py"
```

### 2.2 Slash Commands（斜杠命令）

位于 `.claude/commands/` 目录，定义可重用的 prompt 模板。

**关键 Frontmatter 字段：**

```yaml
---
model: opus                        # 使用的模型
description: "..."                 # 触发描述
argument-hint: [csv_file] [request] # 参数提示
allowed-tools: Glob, Grep, Read, Edit, Write  # 工具限制
disable-model-invocation: false    # 是否禁止模型自动调用
hooks:                             # 专业化验证 hooks
  PostToolUse:
    - matcher: "Read|Edit|Write"
      hooks:
        - type: command
          command: "uv run ..."
---
```

**命令列表：**

| 命令 | 功能 | 验证 |
|------|------|------|
| `/csv-edit` | CSV 编辑/报告 | PostToolUse CSV 验证 |
| `/normalize-csv` | 标准化 CSV 格式 | - |
| `/categorize-csv` | 分类交易 | - |
| `/merge-accounts` | 合并账户 | - |
| `/accumulate-csvs` | 累计数据 | - |
| `/graph-insights` | 生成图表 | - |
| `/generative-ui` | 生成 HTML | - |
| `/build` | 构建项目 | Stop (ruff + ty) |
| `/review-finances` | 主编排器 | Stop (HTML) |
| `/view` | 查看结果 | - |
| `/prime` | 初始化 | - |

### 2.3 Subagents（子代理）

位于 `.claude/agents/` 目录，支持并行执行和上下文隔离。

**Agent 列表：**

| Agent | 功能 | 工具 | 验证 Hooks |
|-------|------|------|-----------|
| `csv-edit-agent` | CSV 编辑/报告 | Glob, Grep, Read, Edit, Write | PostToolUse CSV |
| `normalize-csv-agent` | 标准化 CSV | Read, Write, Edit, Bash, Glob, Grep, Skill | Stop (CSV + Balance) |
| `categorize-csv-agent` | 分类交易 | 同上 | Stop (CSV) |
| `merge-accounts-agent` | 合并账户 | 同上 | Stop (CSV) |
| `graph-agent` | 生成图表 | 同上 | Stop (Graph) |
| `generative-ui-agent` | 生成 HTML | 同上 | Stop (HTML) |

**Prompts vs Subagents 对比：**

| 特性 | Slash Command | Subagent |
|------|--------------|----------|
| 上下文 | 当前上下文运行 | 隔离上下文窗口 |
| 并行性 | 顺序执行 | 可并行执行多个 |
| 参数传递 | `$1`, `$2`, `$ARGUMENTS` | 从 prompt 推断 |
| 调用方式 | `/csv-edit file.csv "add row"` | "Use csv-edit-agent to..." |

### 2.4 Validators（验证器）

位于 `.claude/hooks/validators/`，确定性验证脚本。

**验证器列表：**

| 验证器 | 功能 | 触发方式 |
|--------|------|---------|
| `csv-single-validator.py` | 单 CSV 文件验证 | PostToolUse |
| `csv-validator.py` | 多 CSV 文件验证 | Stop |
| `normalized-balance-validator.py` | 余额一致性验证 | Stop |
| `html-validator.py` | HTML 结构验证 | Stop |
| `graph-validator.py` | 图表生成验证 | Stop |
| `ruff-validator.py` | Python 代码风格 | Stop |
| `ty-validator.py` | Python 类型检查 | Stop |

**验证器返回格式：**

```python
# 通过验证
print(json.dumps({}))

# 阻止并要求修复
print(json.dumps({
    "decision": "block",
    "reason": "CSV error: ..."
}))
```

**退出码含义：**

| 退出码 | 行为 |
|--------|------|
| 0 | 成功，继续正常流程 |
| 2 | 阻塞错误，stderr 反馈给 Claude |
| 其他 | 非阻塞错误 |

---

## 3. 核心设计模式

### 3.1 专业化自验证模式

```
┌─────────────────────────────────────────────────────────────┐
│              Specialized Self-Validation Pattern            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐       ┌─────────────────┐            │
│  │   Focused       │       │  Specialized    │            │
│  │   Agent         │──────▶│   Validator     │            │
│  │   (One Task)    │       │   (Deterministic)│           │
│  └─────────────────┘       └────────┬────────┘            │
│                                     │                       │
│                                     ▼                       │
│                           ┌─────────────────┐              │
│                           │    Decision     │              │
│                           │   ✓ Pass        │              │
│                           │   ✗ Block+Retry │              │
│                           └─────────────────┘              │
│                                                             │
│  Benefits:                                                  │
│  • 每次操作后立即验证                                        │
│  • 确定性验证 > 概率性信任                                   │
│  • 自动自我修正                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 自我修正循环

```
Agent 执行操作
     │
     ▼
Hook 触发验证
     │
     ├─✓ Pass ──▶ 继续
     │
     └─✗ Block ──▶ 错误反馈给 Agent
                        │
                        ▼
                   Agent 自动修正
                        │
                        ▼
                    重新验证
                        │
                        └──▶ 循环直到通过
```

**实际示例：**

```
User: /csv-edit savings.csv "add a row for a $100 deposit"

Agent: [Reads file]
Hook: [Validates CSV structure] ✓

Agent: [Edits file to add row]
Hook: [Validates CSV structure]
  ✗ Balance mismatch! Expected $1100, got $1000

Agent: [Fixes balance calculation]
Hook: [Validates CSV structure] ✓

Agent: "Added deposit row with correct balance."
```

### 3.3 编排器模式

主命令 `/review-finances` 作为编排器，链式调用专业代理：

```yaml
# review-finances.md 的工作流

## Agent Chain

Step 1: normalize-csv-agent     → 标准化 CSV
Step 2: categorize-csv-agent    → 分类交易
Step 3: merge-accounts-agent    → 合并账户
Step 4: /accumulate-csvs        → 累计数据
Step 5: graph-agent (Monthly)   → 生成月度图表
Step 6: graph-agent (Cumulative)→ 生成年度图表
Step 7: generative-ui-agent (Monthly)    → 月度 HTML
Step 8: generative-ui-agent (Cumulative) → 年度 HTML
Step 9: Open Dashboard          → 打开浏览器
```

---

## 4. 验证器详解

### 4.1 CSV 单文件验证器

```python
# csv-single-validator.py 核心逻辑

def validate_csv_parseable(file_path):
    """验证 CSV 可解析且非空"""
    df = pd.read_csv(file_path)
    if len(df) == 0: errors.append("CSV file is empty")
    if len(df.columns) == 0: errors.append("CSV has no columns")

def validate_normalized_csv(file_path):
    """验证标准化 CSV 格式"""
    # 检查必需列
    required_columns = ["date", "description", "category", 
                        "deposit", "withdrawal", "balance", "account_name"]
    
    # 余额一致性验证（从底向上）
    for i in range(len(df) - 2, -1, -1):
        expected_balance = prev_balance - withdrawal + deposit
        if abs(expected_balance - curr_balance) > 0.01:
            errors.append(f"Balance mismatch at row {i}")
```

### 4.2 HTML 验证器

```python
# html-validator.py 核心逻辑

def validate_html(file_path):
    """验证 HTML 文件"""
    soup = BeautifulSoup(content, "lxml")
    
    # 检查基本结构
    checks = [
        soup.find("html"),
        soup.find("head"),
        soup.find("body"),
        soup.find("title")
    ]
    
    # 检查图片存在
    images = soup.find_all("img")
    for img in images:
        if not img_path.exists():
            errors.append(f"Image not found: {src}")
    
    # 至少 5 张图片
    if valid_images < MIN_IMAGES:
        errors.append(f"Found {valid_images} images, expected {MIN_IMAGES}")
```

---

## 5. 项目目录结构

```
agentic-finance-review/
│
├── .claude/                          # Claude Code 配置目录
│   ├── settings.json                 # 全局设置（权限）
│   │
│   ├── commands/                     # Slash Commands
│   │   ├── accumulate-csvs.md        # 累计 CSV 数据
│   │   ├── build.md                  # 构建验证 (ruff + ty)
│   │   ├── categorize-csv.md         # 分类交易
│   │   ├── csv-edit.md               # CSV 编辑
│   │   ├── csv-mock-generator.md     # Mock 数据生成
│   │   ├── generative-ui.md          # 生成 HTML
│   │   ├── graph-insights.md         # 生成图表
│   │   ├── merge-accounts.md         # 合并账户
│   │   ├── normalize-csv.md          # 标准化 CSV
│   │   ├── prime.md                  # 初始化
│   │   ├── review-finances.md        # 主编排器 ⭐
│   │   └── view.md                   # 查看结果
│   │
│   ├── agents/                       # Subagents
│   │   ├── categorize-csv-agent.md
│   │   ├── csv-edit-agent.md
│   │   ├── generative-ui-agent.md
│   │   ├── graph-agent.md
│   │   ├── merge-accounts-agent.md
│   │   └── normalize-csv-agent.md
│   │
│   └── hooks/
│       └── validators/               # 验证脚本
│           ├── csv-single-validator.py
│           ├── csv-validator.py
│           ├── demo-validator.py
│           ├── graph-validator.py
│           ├── html-validator.py
│           ├── normalized-balance-validator.py
│           ├── ruff-validator.py
│           └── ty-validator.py
│
├── scripts/
│   └── generate_graphs.py            # 图表生成脚本
│
├── mock-input-data/                  # 测试数据
│   ├── raw_checkings_jan.csv
│   ├── raw_checkings_feb.csv
│   ├── raw_checkings_mar.csv
│   ├── raw_savings_jan.csv
│   ├── raw_savings_feb.csv
│   └── raw_savings_mar.csv
│
├── apps/agentic-finance-review/data/ # 输出目录
│   └── mock_dataset_2026/
│       ├── agentic_cumulative_dataset_2026.csv
│       ├── index.html
│       ├── assets/
│       └── mock_dataset_mar_1st_2026/
│           ├── raw_checkings.csv
│           ├── normalized_checkings.csv
│           ├── agentic_merged_transactions.csv
│           ├── index.html
│           └── assets/
│
├── ai_docs/
│   └── README.md
│
├── images/
│   └── ssva.png                       # 架构图
│
├── CLAUDE.md                          # 项目上下文
├── README.md                          # 项目说明
├── ruff.toml                          # Python 代码风格配置
└── ty.toml                            # Python 类型检查配置
```

---

## 6. 关键技术实现

### 6.1 确定性验证脚本

使用 `uv run --script` 内联声明依赖：

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "beautifulsoup4", "lxml"]
# ///

# 这样无需预装依赖，uv 自动处理
```

### 6.2 Hook 输入解析

```python
def main():
    # 从 stdin 读取 hook 输入
    stdin_data = sys.stdin.read()
    if stdin_data.strip():
        hook_input = json.loads(stdin_data)
        
        # 获取工具信息
        tool_name = hook_input.get("tool_name")
        tool_input = hook_input.get("tool_input", {})
        file_path = tool_input.get("file_path")
```

### 6.3 图表生成脚本

`scripts/generate_graphs.py` 生成 8 个标准图表：

1. **Balance Over Time** - 账户余额趋势
2. **Category Breakdown** - 支出分类饼图
3. **Income vs Expenses** - 收支对比
4. **Spending by Category** - 分类支出条形图
5. **Daily Transactions** - 每日交易数量
6. **Top Merchants** - 支出最多的商户
7. **Cumulative Spending** - 累计支出曲线
8. **Spending by Weekday** - 按星期支出

---

## 7. 设计原则总结

### 7.1 核心原则

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个 Agent 只做一件事 |
| **确定性验证** | 用代码验证，不靠概率信任 |
| **即时反馈** | PostToolUse 立即验证，不等结束 |
| **自我修正** | 验证失败自动重试修复 |
| **上下文隔离** | Subagent 隔离避免干扰 |
| **可观测性** | 日志记录所有验证过程 |

### 7.2 与传统 Agent 对比

| 方面 | 传统 Agent | 专业化自验证 Agent |
|------|-----------|-------------------|
| 可靠性 | 时好时坏 | 一致可靠 |
| 调试 | 困难 | 验证日志清晰 |
| 信任度 | 需要人工检查 | 自动验证可信任 |
| 并行性 | 可能冲突 | 隔离上下文可并行 |
| 错误处理 | 可能忽略 | 强制验证修复 |

### 7.3 适用场景

- ✅ 文件操作需要格式验证
- ✅ 代码生成需要语法/类型检查
- ✅ 数据处理需要一致性验证
- ✅ 构建流程需要增量验证
- ✅ 需要高可靠性的自动化任务

---

## 8. 扩展指南

### 8.1 创建新的验证 Agent

```yaml
# .claude/agents/my-validator-agent.md
---
name: my-validator-agent
description: Validate my specific file type
model: opus
tools: Read, Write, Edit, Bash
hooks:
  PostToolUse:
    - matcher: "Read|Edit|Write"
      hooks:
        - type: command
          command: "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/my-validator.py"
---

# Purpose
Validate my specific file type after every operation.

## Workflow
1. Read the file
2. Make modifications
3. Validator runs automatically
```

### 8.2 创建新的验证器

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["my-dependency"]
# ///

import json
import sys

def validate(file_path):
    errors = []
    # 实现验证逻辑
    return errors

def main():
    stdin_data = sys.stdin.read()
    hook_input = json.loads(stdin_data) if stdin_data.strip() else {}
    file_path = hook_input.get("tool_input", {}).get("file_path")
    
    errors = validate(file_path)
    
    if errors:
        print(json.dumps({
            "decision": "block",
            "reason": "\n".join(errors)
        }))
    else:
        print(json.dumps({}))

if __name__ == "__main__":
    main()
```

---

## 9. 参考资源

- [Claude Code Hooks 文档](https://code.claude.com/docs/en/hooks)
- [Custom Slash Commands](https://code.claude.com/docs/en/slash-commands)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
- [Agent Skills](https://code.claude.com/docs/en/skills)
- [视频演示](https://youtu.be/u5GkG71PkR0)

---

## 10. 总结

Agentic Finance Review 展示了一个关键洞见：

> **专业化代理 + 确定性验证 = 可信自动化**

通过 Claude Code 的 Hooks 系统，每个 Agent 可以：
1. 在每次操作后立即验证
2. 自动修正验证失败
3. 隔离上下文并行执行
4. 提供清晰的验证日志

这种模式将 Agent 从"有时工作"提升到"一致可靠"，为生产环境的自动化提供了信任基础。
