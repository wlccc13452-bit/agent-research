# NanoClaw Container Skill 使用指南

## Skill 概述

NanoClaw 使用 Claude Agent SDK 的 Skill 系统，通过 Markdown 文件定义 Agent 能力。

## Skill 目录结构

```
nanoclaw/container/
├── skills/
│   └── agent-browser.md    # 浏览器自动化 Skill
├── agent-runner/
│   └── src/
│       └── index.ts        # Agent 运行器
└── Dockerfile              # 容器镜像
```

## Skill 文件格式

### agent-browser.md 示例

```markdown
---
name: agent-browser
description: Automates browser interactions for web testing...
allowed-tools: Bash(agent-browser:*)
---

# Browser Automation with agent-browser

## Quick start

\`\`\`bash
agent-browser open <url>        # Navigate to page
agent-browser snapshot -i       # Get interactive elements
agent-browser click @e1         # Click element by ref
\`\`\`

...详细使用说明...
```

### 元数据字段

| 字段 | 说明 |
|------|------|
| `name` | Skill 名称 |
| `description` | 描述（用于选择合适的 Skill） |
| `allowed-tools` | 允许使用的工具（限制范围） |

## Skill 加载流程

### 1. 容器启动

```dockerfile
# Dockerfile
FROM node:22-slim

# 安装 agent-browser 和 claude-code
RUN npm install -g agent-browser @anthropic-ai/claude-code

# 复制 Skill 文件
COPY skills/ /skills/
```

### 2. Agent Runner 初始化

```typescript
// agent-runner/src/index.ts

import { query } from '@anthropic-ai/claude-agent-sdk';

for await (const message of query({
    prompt: input.prompt,
    options: {
        cwd: '/workspace/group',
        allowedTools: [
            'Bash',
            'Read', 'Write', 'Edit', 'Glob', 'Grep',
            'WebSearch', 'WebFetch',
            'mcp__nanoclaw__*'  // MCP 工具
        ],
        permissionMode: 'bypassPermissions',
        mcpServers: {
            nanoclaw: ipcMcp  // IPC MCP Server
        }
    }
})) {
    // 处理消息
}
```

### 3. Skill 发现

Claude Agent SDK 自动发现：
1. 项目目录下的 `.claude/skills/` 目录
2. 全局 Skills 目录
3. 配置文件中指定的 Skills 路径

## Python 案例：在 NanoClaw 中使用 Skill

### 场景：创建浏览器自动化任务

**步骤 1：准备 Skill 文件**

```markdown
---
name: web-scraper
description: "Extract data from websites using browser automation"
allowed-tools: Bash(agent-browser:*)
---

# Web Scraper Skill

## 数据提取流程

1. 打开目标页面
2. 获取页面快照
3. 提取所需数据
4. 保存结果

## 示例：提取商品信息

\`\`\`bash
# 打开商品页面
agent-browser open https://example.com/products

# 获取可交互元素
agent-browser snapshot -i

# 提取文本
agent-browser get text @e1  # 商品名称
agent-browser get attr @e2 href  # 商品链接

# 截图保存
agent-browser screenshot products.png
\`\`\`
```

**步骤 2：用户发送消息**

```
用户: "帮我从 https://example.com/products 提取所有商品名称和价格"
```

**步骤 3：Agent 执行流程**

```
1. 检测到 web-scraper skill 可用
2. 调用 Bash(agent-browser open https://example.com/products)
3. 调用 Bash(agent-browser snapshot -i)
4. 解析页面元素
5. 提取数据并格式化输出
```

**步骤 4：输出结果**

```json
{
  "products": [
    {"name": "Product A", "price": "$19.99"},
    {"name": "Product B", "price": "$29.99"}
  ]
}
```

## MCP 工具集成

### IPC MCP Server

NanoClaw 通过 IPC（进程间通信）实现 MCP 工具：

```typescript
// agent-runner/src/ipc-mcp.ts

export function createIpcMcp(ctx: IpcMcpContext) {
    return createSdkMcpServer({
        name: 'nanoclaw',
        tools: [
            tool('send_message', 'Send a message to WhatsApp group', 
                { text: z.string() },
                async (args) => {
                    // 写入 IPC 文件
                    writeIpcFile(MESSAGES_DIR, {
                        type: 'message',
                        chatJid: ctx.chatJid,
                        text: args.text
                    });
                    return { content: [{ type: 'text', text: 'Message queued' }] };
                }
            ),
            tool('schedule_task', 'Schedule a recurring task', ...),
            tool('list_tasks', 'List scheduled tasks', ...),
            tool('pause_task', 'Pause a task', ...),
            tool('cancel_task', 'Cancel a task', ...),
        ]
    });
}
```

### IPC 通信流程

```
Container (Agent)                    Host (NanoClaw Main)
      │                                    │
      │  writeIpcFile(MESSAGES_DIR)        │
      │ ─────────────────────────────────► │
      │                                    │ 读取 IPC 文件
      │                                    │ 发送 WhatsApp 消息
      │                                    │
```

## 与 NanoBot Skill 对比

| 维度 | NanoClaw | NanoBot |
|------|----------|---------|
| Skill 格式 | Markdown + YAML frontmatter | 相同 |
| 加载方式 | Claude Agent SDK 自动 | SkillsLoader 手动 |
| 工具限制 | allowed-tools 字段 | requires 字段 |
| MCP 集成 | SDK 内置 | 需要手动连接 |
| 容器隔离 | Docker | 无（可选） |

## 技能扩展示例

### 创建新 Skill

**文件**: `skills/data-analysis.md`

```markdown
---
name: data-analysis
description: "Analyze data files (CSV, JSON) and generate reports"
allowed-tools: Bash(python:*), Read, Write
---

# Data Analysis Skill

## CSV 分析

\`\`\`python
import pandas as pd

# 读取数据
df = pd.read_csv('data.csv')

# 基本统计
print(df.describe())

# 可视化
df.plot()
\`\`\`

## JSON 处理

\`\`\`python
import json

with open('data.json') as f:
    data = json.load(f)

# 提取特定字段
values = [item['value'] for item in data]
\`\`\`
```

**使用**:

```
用户: "分析 sales.csv 文件，生成月度销售报告"

Agent:
1. 发现 data-analysis skill
2. 读取 sales.csv
3. 执行 Python 分析脚本
4. 生成报告文件
```

## 最佳实践

1. **明确工具范围**：使用 `allowed-tools` 限制 Skill 可用的工具
2. **提供详细示例**：在 Skill 中包含具体的使用示例
3. **错误处理**：在 Skill 中说明常见错误和解决方法
4. **组合使用**：多个 Skill 可以组合完成复杂任务
