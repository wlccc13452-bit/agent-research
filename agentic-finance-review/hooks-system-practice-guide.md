# Claude Code Hooks 系统实践指南

基于 Agentic Finance Review 项目的深入研究。

---

## 1. Hooks 系统概述

### 1.1 什么是 Hooks

Hooks 是 Claude Code 提供的事件驱动机制，允许在特定事件点注入自定义逻辑。这是实现**专业化自验证代理**的核心技术。

### 1.2 事件类型

| 事件 | 触发时机 | 典型用途 |
|------|---------|---------|
| `PreToolUse` | 工具执行前 | 阻止危险操作、参数预处理 |
| `PostToolUse` | 工具执行后 | 验证输出、记录日志 |
| `Stop` | Agent 完成时 | 最终验证、清理工作 |

### 1.3 配置位置

Hooks 可以配置在两个层级：

```
┌─────────────────────────────────────────────────────────────┐
│                    Hooks 配置层级                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Level 1: 全局设置                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ .claude/settings.json                               │   │
│  │                                                     │   │
│  │ {                                                   │   │
│  │   "hooks": {                                        │   │
│  │     "PostToolUse": [...]                            │   │
│  │   }                                                 │   │
│  │ }                                                   │   │
│  │                                                     │   │
│  │ 适用范围: 所有 Agent                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Level 2: 专业化设置（推荐）                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ .claude/commands/my-command.md                      │   │
│  │ .claude/agents/my-agent.md                          │   │
│  │                                                     │   │
│  │ ---                                                 │   │
│  │ hooks:                                              │   │
│  │   PostToolUse:                                      │   │
│  │     - matcher: "Read|Edit|Write"                    │   │
│  │       hooks:                                        │   │
│  │         - type: command                             │   │
│  │           command: "uv run validator.py"            │   │
│  │ ---                                                 │   │
│  │                                                     │   │
│  │ 适用范围: 仅此 command/agent                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Hook 配置详解

### 2.1 基本结构

```yaml
hooks:
  <EventName>:
    - matcher: "<regex>"        # 可选：匹配特定工具
      hooks:
        - type: command
          command: "<script>"   # 执行的命令
```

### 2.2 PostToolUse 示例

**场景：每次编辑 CSV 后验证**

```yaml
---
name: csv-edit-agent
description: Edit CSV files with validation
tools: Read, Edit, Write
hooks:
  PostToolUse:
    - matcher: "Read|Edit|Write"   # 匹配这些工具
      hooks:
        - type: command
          command: "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/csv-single-validator.py"
---
```

**执行流程：**

```
Agent 调用 Edit 工具
        │
        ▼
工具执行完成
        │
        ▼
PostToolUse Hook 触发
        │
        ├─ matcher 匹配 "Edit" ✓
        │
        ▼
执行 csv-single-validator.py
        │
        ├─ 验证通过 → 返回 {}
        │           → Agent 继续执行
        │
        └─ 验证失败 → 返回 {"decision": "block", "reason": "..."}
                    → 错误反馈给 Agent
                    → Agent 自动修正
```

### 2.3 Stop Hook 示例

**场景：Agent 完成时进行最终验证**

```yaml
---
name: normalize-csv-agent
description: Normalize CSV files
tools: Read, Write, Edit, Bash, Glob, Grep, Skill
hooks:
  Stop:
    - hooks:
        - type: command
          command: "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/csv-validator.py"
        - type: command
          command: "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/normalized-balance-validator.py"
---
```

**特点：**
- Stop Hook 没有 matcher（在 Agent 结束时触发）
- 可以配置多个验证器，按顺序执行
- 任一验证失败都会阻塞

### 2.4 多验证器链

```yaml
hooks:
  Stop:
    - hooks:
        - type: command
          command: "uv run validators/csv-validator.py"      # 1. CSV 结构
        - type: command
          command: "uv run validators/balance-validator.py"  # 2. 余额一致性
        - type: command
          command: "uv run validators/schema-validator.py"   # 3. 数据模式
```

---

## 3. 验证器脚本开发

### 3.1 标准模板

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "any-other-deps"]
# ///

"""
验证器脚本模板

输入: 通过 stdin 接收 JSON (PostToolUse 时)
输出: JSON 决策

Exit codes:
  0 = Success (继续)
  2 = Block (反馈错误给 Agent)
  other = Non-blocking error
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 日志文件（可选）
LOG_FILE = Path(__file__).parent / "validator.log"

def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def validate(file_path: Path) -> list[str]:
    """
    实现验证逻辑
    返回错误列表，空列表表示通过
    """
    errors = []
    
    # TODO: 实现验证逻辑
    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
    
    return errors

def main():
    log("=" * 50)
    log("VALIDATOR TRIGGERED")
    
    # 解析 stdin (PostToolUse)
    file_path = None
    try:
        stdin_data = sys.stdin.read()
        if stdin_data.strip():
            hook_input = json.loads(stdin_data)
            tool_input = hook_input.get("tool_input", {})
            file_path = tool_input.get("file_path")
            log(f"File from stdin: {file_path}")
    except Exception as e:
        log(f"Error parsing stdin: {e}")
    
    # 回退到命令行参数 (Stop hook)
    if not file_path and len(sys.argv) > 1:
        file_path = sys.argv[1]
        log(f"File from arg: {file_path}")
    
    if not file_path:
        log("No file path, skipping")
        print(json.dumps({}))
        return
    
    # 执行验证
    errors = validate(Path(file_path))
    
    # 输出决策
    if errors:
        log(f"BLOCK: {len(errors)} errors")
        for err in errors:
            log(f"  ✗ {err}")
        print(json.dumps({
            "decision": "block",
            "reason": "Validation failed:\n" + "\n".join(errors)
        }))
    else:
        log("PASS")
        print(json.dumps({}))

if __name__ == "__main__":
    main()
```

### 3.2 Hook 输入数据结构

**PostToolUse 输入：**

```json
{
  "hook_event_name": "PostToolUse",
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/path/to/file.csv",
    "old_string": "...",
    "new_string": "..."
  },
  "tool_output": {
    "result": "success"
  }
}
```

**Stop 输入：**

```json
{
  "hook_event_name": "Stop",
  "reason": "complete"
}
```

### 3.3 输出格式

```python
# 通过验证
print(json.dumps({}))

# 阻塞并要求修复
print(json.dumps({
    "decision": "block",
    "reason": "详细错误信息，Agent 会看到这个"
}))
```

---

## 4. 实战案例分析

### 4.1 CSV 验证器

```python
# csv-single-validator.py 核心实现

def validate_csv_parseable(file_path: Path) -> list[str]:
    """验证 CSV 可解析"""
    errors = []
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return [f"Failed to parse CSV: {e}"]
    
    if len(df) == 0:
        errors.append("CSV file is empty")
    if len(df.columns) == 0:
        errors.append("CSV has no columns")
    
    return errors

def validate_normalized_csv(file_path: Path) -> list[str]:
    """验证标准化 CSV 格式"""
    errors = []
    df = pd.read_csv(file_path)
    
    # 1. 检查必需列
    required = ["date", "description", "category", 
                "deposit", "withdrawal", "balance", "account_name"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        return [f"Missing columns: {missing}"]
    
    # 2. 余额一致性验证
    deposits = [parse_numeric(v) for v in df["deposit"]]
    withdrawals = [parse_numeric(v) for v in df["withdrawal"]]
    balances = [parse_numeric(v) for v in df["balance"]]
    
    # 从底向上验证（最早记录在最后）
    for i in range(len(df) - 2, -1, -1):
        prev_balance = balances[i + 1]
        curr_deposit = deposits[i]
        curr_withdrawal = withdrawals[i]
        curr_balance = balances[i]
        
        expected = prev_balance - curr_withdrawal + curr_deposit
        if abs(expected - curr_balance) > 0.01:
            errors.append(
                f"Row {i + 2}: Balance mismatch! "
                f"Expected ${expected:,.2f}, got ${curr_balance:,.2f}"
            )
    
    return errors
```

**验证逻辑说明：**

```
CSV 余额验证原理：

原始数据（从新到旧）：
Row 1: balance = $1000  (最新)
Row 2: withdrawal = $50, balance = $1050
Row 3: deposit = $200, balance = $1100  (最早)

验证公式：
current_balance = prev_balance - withdrawal + deposit

Row 2 验证：
expected = $1000 - (-$50) + $0 = $1050 ✓
actual = $1050 ✓

Row 3 验证：
expected = $1050 - $0 + $200 = $1250 ✗
actual = $1100 ✗ → 报告错误
```

### 4.2 HTML 验证器

```python
# html-validator.py 核心实现

def validate_html(file_path: Path) -> list[str]:
    """验证 HTML 文件"""
    errors = []
    
    content = file_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, "lxml")
    
    # 1. 检查基本结构
    if not soup.find("html"):
        errors.append("Missing <html> tag")
    if not soup.find("head"):
        errors.append("Missing <head> tag")
    if not soup.find("body"):
        errors.append("Missing <body> tag")
    if not soup.find("title"):
        errors.append("Missing <title> tag")
    
    # 2. 检查图片存在
    parent_dir = file_path.parent
    images = soup.find_all("img")
    valid_images = 0
    
    for img in images:
        src = img.get("src", "")
        if not src.startswith(("http://", "https://", "data:")):
            img_path = parent_dir / src
            if img_path.exists():
                valid_images += 1
            else:
                errors.append(f"Image not found: {src}")
    
    # 3. 检查图片数量
    MIN_IMAGES = 5
    if valid_images < MIN_IMAGES:
        errors.append(f"Found {valid_images} images, need at least {MIN_IMAGES}")
    
    return errors
```

### 4.3 图表验证器

```python
# graph-validator.py 核心实现

def validate_graphs(directory: Path) -> list[str]:
    """验证图表生成"""
    errors = []
    
    assets_dir = directory / "assets"
    if not assets_dir.exists():
        return ["assets/ directory not found"]
    
    # 检查必需的图表
    required_graphs = [
        "plot_balance_over_time.png",
        "plot_category_breakdown.png",
        "plot_income_vs_expenses.png",
        # ... 更多
    ]
    
    for graph_name in required_graphs:
        graph_path = assets_dir / graph_name
        if not graph_path.exists():
            errors.append(f"Missing graph: {graph_name}")
        elif graph_path.stat().st_size == 0:
            errors.append(f"Empty graph: {graph_name}")
    
    return errors
```

---

## 5. 最佳实践

### 5.1 验证器设计原则

| 原则 | 说明 |
|------|------|
| **确定性** | 验证结果必须可重复 |
| **快速** | 避免耗时操作，影响 Agent 流程 |
| **清晰** | 错误信息要具体，帮助 Agent 修正 |
| **独立** | 每个验证器只负责一类检查 |
| **幂等** | 多次执行结果一致 |

### 5.2 Matcher 使用

```yaml
# 匹配单个工具
matcher: "Edit"

# 匹配多个工具（正则）
matcher: "Read|Edit|Write"

# 匹配所有文件操作
matcher: "Read|Edit|Write|Glob"

# 匹配特定文件类型（在脚本中处理）
matcher: ".*"  # 在脚本中检查 file_path.suffix
```

### 5.3 错误信息格式

```python
# 好的错误信息
errors.append(
    f"{file_path.name} row {row_num} (date: {date}): "
    f"Balance mismatch! Expected ${expected:,.2f}, got ${actual:,.2f}"
)

# 不好的错误信息
errors.append("Balance error")  # 太模糊
```

### 5.4 日志记录

```python
LOG_FILE = Path(__file__).parent / "validator.log"

def log(message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

# 使用
log("=" * 50)
log("VALIDATOR TRIGGERED")
log(f"File: {file_path}")
log(f"RESULT: {'PASS' if not errors else 'BLOCK'}")
```

---

## 6. 调试技巧

### 6.1 查看验证日志

```bash
# 查看最近的验证日志
tail -50 .claude/hooks/validators/csv-single-validator.log
```

### 6.2 手动测试验证器

```bash
# 测试 CSV 验证器
echo '{"tool_input": {"file_path": "test.csv"}}' | \
  uv run .claude/hooks/validators/csv-single-validator.py

# 测试 HTML 验证器（Stop hook 风格）
uv run .claude/hooks/validators/html-validator.py "apps/data/mock_dataset_2026"
```

### 6.3 检查 Hook 触发

在验证器中添加详细日志：

```python
def main():
    log("=" * 50)
    log("VALIDATOR TRIGGERED")
    log(f"sys.argv: {sys.argv}")
    
    stdin_data = sys.stdin.read()
    log(f"stdin length: {len(stdin_data)}")
    if stdin_data.strip():
        hook_input = json.loads(stdin_data)
        log(f"hook_event: {hook_input.get('hook_event_name')}")
        log(f"tool_name: {hook_input.get('tool_name')}")
```

---

## 7. 常见问题

### Q1: Hook 没有触发？

**检查清单：**
1. YAML frontmatter 格式正确？
2. matcher 正则是否匹配？
3. 命令路径是否正确（使用 `$CLAUDE_PROJECT_DIR`）？
4. 脚本是否有执行权限？

### Q2: 验证通过但 Agent 没继续？

可能是验证器输出了非空 JSON：

```python
# 错误：输出了额外内容
print(json.dumps({}))
print("Validation complete")  # 这会导致问题

# 正确：只输出 JSON
print(json.dumps({}))
```

### Q3: 如何跳过某些文件？

在验证器中添加过滤逻辑：

```python
def main():
    # ...
    file_path = Path(file_path)
    
    # 跳过非 CSV 文件
    if file_path.suffix.lower() != ".csv":
        print(json.dumps({}))
        return
```

### Q4: 多个 Agent 共享验证器？

使用环境变量或参数区分：

```yaml
# Agent A
command: "uv run validator.py --type=monthly"

# Agent B
command: "uv run validator.py --type=cumulative"
```

---

## 8. 总结

Claude Code Hooks 系统的核心价值：

```
┌─────────────────────────────────────────────────────────────┐
│                    Hooks 核心价值                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 即时验证                                                │
│     • PostToolUse 每次操作后验证                            │
│     • 不等问题积累                                          │
│                                                             │
│  2. 自动修正                                                │
│     • 验证失败反馈给 Agent                                  │
│     • Agent 自动重试修正                                    │
│                                                             │
│  3. 专业化                                                  │
│     • 每个 Agent 有自己的验证逻辑                           │
│     • 不影响其他 Agent                                      │
│                                                             │
│  4. 可观测                                                  │
│     • 日志记录所有验证过程                                  │
│     • 便于调试和审计                                        │
│                                                             │
│  结果：专业化 Agent + 确定性验证 = 可信自动化               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
