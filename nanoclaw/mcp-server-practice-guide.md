# NanoClaw MCP Server 使用研究

## 一、MCP 概述

**MCP (Model Context Protocol)** 是 Anthropic 定义的协议，用于在 LLM Agent 和外部工具/服务之间建立标准化通信。

在 NanoClaw 中，MCP Server 用于：
- 发送 WhatsApp 消息
- 管理定时任务
- 注册群组

---

## 二、NanoClaw 中的 MCP 架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Claude Agent SDK                                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    query()                                     │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  mcpServers: {                                           │  │ │
│  │  │    nanoclaw: createIpcMcp(ctx)  ◄────────────────────────┼──┼─┤
│  │  │  }                                                       │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                          │                                     │ │
│  │                          ▼                                     │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  Tools:                                                   │  │ │
│  │  │  • mcp__nanoclaw__send_message                           │  │ │
│  │  │  • mcp__nanoclaw__schedule_task                          │  │ │
│  │  │  • mcp__nanoclaw__list_tasks                             │  │ │
│  │  │  • mcp__nanoclaw__pause_task                             │  │ │
│  │  │  • mcp__nanoclaw__resume_task                            │  │ │
│  │  │  • mcp__nanoclaw__cancel_task                            │  │ │
│  │  │  • mcp__nanoclaw__register_group                         │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────┐
                    │   IPC File System   │
                    │  /workspace/ipc/    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Host Process     │
                    │   IPC Watcher       │
                    └─────────────────────┘
```

### 2.2 关键文件

| 文件 | 作用 |
|------|------|
| `container/agent-runner/src/ipc-mcp.ts` | MCP Server 定义 |
| `container/agent-runner/src/index.ts` | MCP Server 注册到 Agent SDK |
| `container/agent-runner/package.json` | 依赖：`@anthropic-ai/claude-agent-sdk` |

---

## 三、MCP Server 创建流程

### 3.1 基本结构

```typescript
import { createSdkMcpServer, tool } from '@anthropic-ai/claude-agent-sdk';
import { z } from 'zod';

// 创建 MCP Server
export function createIpcMcp(ctx: IpcMcpContext) {
  return createSdkMcpServer({
    name: 'nanoclaw',           // Server 名称
    version: '1.0.0',           // 版本号
    tools: [                    // 工具列表
      // ... tool() 定义
    ]
  });
}
```

### 3.2 工具定义格式

```typescript
tool(
  'tool_name',                              // 工具名称
  'Tool description for the LLM',           // 工具描述
  {                                         // 参数 Schema (Zod)
    param1: z.string().describe('...'),
    param2: z.number().optional()
  },
  async (args) => {                         // 处理函数
    // 执行逻辑
    
    return {
      content: [{
        type: 'text',
        text: 'Result message'
      }],
      isError: false  // 可选，标记是否错误
    };
  }
)
```

### 3.3 注册到 Agent SDK

```typescript
// agent-runner/src/index.ts
import { query } from '@anthropic-ai/claude-agent-sdk';
import { createIpcMcp } from './ipc-mcp.js';

// 创建 MCP Server 实例
const ipcMcp = createIpcMcp({
  chatJid: input.chatJid,
  groupFolder: input.groupFolder,
  isMain: input.isMain
});

// 注册到 query()
for await (const message of query({
  prompt,
  options: {
    mcpServers: {
      nanoclaw: ipcMcp    // 注册 MCP Server
    },
    allowedTools: [
      'mcp__nanoclaw__*'  // 允许使用 nanoclaw 的所有工具
    ]
  }
})) {
  // 处理消息...
}
```

---

## 四、MCP Server 要求与约定

### 4.1 必须满足的要求

| 要求 | 描述 | 示例 |
|------|------|------|
| **命名规范** | 工具调用格式: `mcp__{server}__{tool}` | `mcp__nanoclaw__send_message` |
| **返回格式** | 必须返回 `{ content: [{ type: 'text', text: '...' }] }` | 见下方示例 |
| **参数验证** | 使用 Zod 定义参数 Schema | `z.string().describe('...')` |
| **错误处理** | 返回 `isError: true` 标记错误 | `{ content: [...], isError: true }` |

### 4.2 返回值约定

**成功返回**：
```typescript
return {
  content: [{
    type: 'text',
    text: 'Operation completed successfully'
  }]
};
```

**错误返回**：
```typescript
return {
  content: [{
    type: 'text',
    text: 'Error: Invalid parameters'
  }],
  isError: true
};
```

### 4.3 参数 Schema 约定

```typescript
// 基本类型
text: z.string().describe('The message text')

// 枚举类型
schedule_type: z.enum(['cron', 'interval', 'once'])

// 可选参数
target_group: z.string().optional().describe('...')

// 带默认值
context_mode: z.enum(['group', 'isolated']).default('group')

// 复杂描述
prompt: z.string().describe(`
  What the agent should do when the task runs.
  For isolated mode, include all necessary context here.
`)
```

### 4.4 工具命名约定

| 命名模式 | 示例 | 用途 |
|----------|------|------|
| `verb_noun` | `send_message` | 执行动作 |
| `list_nouns` | `list_tasks` | 查询列表 |
| `verb_noun` | `pause_task` | 状态变更 |

---

## 五、NanoClaw MCP 工具详解

### 5.1 send_message

```typescript
tool(
  'send_message',
  'Send a message to the current WhatsApp group. Use this to proactively share information or updates.',
  {
    text: z.string().describe('The message text to send')
  },
  async (args) => {
    const data = {
      type: 'message',
      chatJid,
      text: args.text,
      groupFolder,
      timestamp: new Date().toISOString()
    };

    const filename = writeIpcFile(MESSAGES_DIR, data);

    return {
      content: [{
        type: 'text',
        text: `Message queued for delivery (${filename})`
      }]
    };
  }
)
```

**IPC 输出**：
```json
// /workspace/ipc/{group}/messages/1234567890-abc123.json
{
  "type": "message",
  "chatJid": "120363336345536173@g.us",
  "text": "Hello from Andy!",
  "groupFolder": "main",
  "timestamp": "2026-02-19T10:00:00.000Z"
}
```

### 5.2 schedule_task

```typescript
tool(
  'schedule_task',
  `Schedule a recurring or one-time task...
   
   CONTEXT MODE - Choose based on task type:
   • "group": Task runs with chat history and memory
   • "isolated": Task runs in fresh session
   
   SCHEDULE VALUE FORMAT:
   • cron: "0 9 * * *"
   • interval: "3600000" (milliseconds)
   • once: "2026-02-01T15:30:00" (no Z suffix!)`,
  {
    prompt: z.string().describe('What the agent should do'),
    schedule_type: z.enum(['cron', 'interval', 'once']),
    schedule_value: z.string().describe('Schedule value'),
    context_mode: z.enum(['group', 'isolated']).default('group'),
    target_group: z.string().optional().describe('Target group (main only)')
  },
  async (args) => {
    // 验证 schedule_value
    if (args.schedule_type === 'cron') {
      try {
        CronExpressionParser.parse(args.schedule_value);
      } catch (err) {
        return {
          content: [{ type: 'text', text: `Invalid cron: "${args.schedule_value}"` }],
          isError: true
        };
      }
    }

    // 权限检查
    const targetGroup = isMain && args.target_group 
      ? args.target_group 
      : groupFolder;

    const data = {
      type: 'schedule_task',
      prompt: args.prompt,
      schedule_type: args.schedule_type,
      schedule_value: args.schedule_value,
      context_mode: args.context_mode || 'group',
      groupFolder: targetGroup,
      chatJid,
      createdBy: groupFolder,
      timestamp: new Date().toISOString()
    };

    writeIpcFile(TASKS_DIR, data);

    return {
      content: [{
        type: 'text',
        text: `Task scheduled: ${args.schedule_type} - ${args.schedule_value}`
      }]
    };
  }
)
```

### 5.3 list_tasks

```typescript
tool(
  'list_tasks',
  'List all scheduled tasks. From main: shows all tasks. From other groups: shows only that group\'s tasks.',
  {},
  async () => {
    const tasksFile = path.join(IPC_DIR, 'current_tasks.json');

    if (!fs.existsSync(tasksFile)) {
      return {
        content: [{ type: 'text', text: 'No scheduled tasks found.' }]
      };
    }

    const allTasks = JSON.parse(fs.readFileSync(tasksFile, 'utf-8'));

    // 权限过滤: Main 看全部，其他只看自己的
    const tasks = isMain
      ? allTasks
      : allTasks.filter(t => t.groupFolder === groupFolder);

    const formatted = tasks.map(t =>
      `- [${t.id}] ${t.prompt.slice(0, 50)}... (${t.schedule_type}: ${t.schedule_value})`
    ).join('\n');

    return {
      content: [{ type: 'text', text: `Scheduled tasks:\n${formatted}` }]
    };
  }
)
```

### 5.4 register_group (Main Only)

```typescript
tool(
  'register_group',
  `Register a new WhatsApp group so the agent can respond to messages there. Main group only.`,
  {
    jid: z.string().describe('The WhatsApp JID'),
    name: z.string().describe('Display name for the group'),
    folder: z.string().describe('Folder name (lowercase, hyphens)'),
    trigger: z.string().describe('Trigger word (e.g., "@Andy")')
  },
  async (args) => {
    // 权限检查
    if (!isMain) {
      return {
        content: [{ type: 'text', text: 'Only the main group can register new groups.' }],
        isError: true
      };
    }

    const data = {
      type: 'register_group',
      jid: args.jid,
      name: args.name,
      folder: args.folder,
      trigger: args.trigger,
      timestamp: new Date().toISOString()
    };

    writeIpcFile(TASKS_DIR, data);

    return {
      content: [{
        type: 'text',
        text: `Group "${args.name}" registered.`
      }]
    };
  }
)
```

---

## 六、完整示例：自定义 MCP Server

### 6.1 示例：天气查询 MCP Server

```typescript
// weather-mcp.ts
import { createSdkMcpServer, tool } from '@anthropic-ai/claude-agent-sdk';
import { z } from 'zod';

export interface WeatherMcpContext {
  defaultLocation: string;
  apiKey: string;
}

export function createWeatherMcp(ctx: WeatherMcpContext) {
  return createSdkMcpServer({
    name: 'weather',
    version: '1.0.0',
    tools: [
      tool(
        'get_weather',
        `Get current weather for a location.
         
         Returns temperature, humidity, and conditions.`,
        {
          location: z.string()
            .optional()
            .describe('City name or coordinates. Defaults to configured location.')
        },
        async (args) => {
          const location = args.location || ctx.defaultLocation;
          
          try {
            // 调用天气 API
            const response = await fetch(
              `https://api.weather.com/current?location=${encodeURIComponent(location)}&key=${ctx.apiKey}`
            );
            
            if (!response.ok) {
              return {
                content: [{
                  type: 'text',
                  text: `Failed to fetch weather: ${response.status}`
                }],
                isError: true
              };
            }
            
            const data = await response.json();
            
            return {
              content: [{
                type: 'text',
                text: `Weather in ${location}:
• Temperature: ${data.temp}°C
• Humidity: ${data.humidity}%
• Conditions: ${data.conditions}`
              }]
            };
          } catch (err) {
            return {
              content: [{
                type: 'text',
                text: `Error fetching weather: ${err instanceof Error ? err.message : String(err)}`
              }],
              isError: true
            };
          }
        }
      ),

      tool(
        'get_forecast',
        'Get 7-day weather forecast for a location.',
        {
          location: z.string().optional().describe('City name. Defaults to configured location.')
        },
        async (args) => {
          const location = args.location || ctx.defaultLocation;
          
          // 类似实现...
          return {
            content: [{
              type: 'text',
              text: `7-day forecast for ${location}...`
            }]
          };
        }
      )
    ]
  });
}
```

### 6.2 注册到 Agent

```typescript
// index.ts
import { query } from '@anthropic-ai/claude-agent-sdk';
import { createWeatherMcp } from './weather-mcp.js';

const weatherMcp = createWeatherMcp({
  defaultLocation: 'San Francisco',
  apiKey: process.env.WEATHER_API_KEY!
});

for await (const message of query({
  prompt: "What's the weather like?",
  options: {
    mcpServers: {
      weather: weatherMcp
    },
    allowedTools: [
      'mcp__weather__*'  // 允许所有 weather 工具
    ]
  }
})) {
  // ...
}
```

### 6.3 Agent 调用示例

```
User: What's the weather in Tokyo?

Agent: [调用 mcp__weather__get_weather({ location: "Tokyo" })]

Result: Weather in Tokyo:
• Temperature: 22°C
• Humidity: 65%
• Conditions: Partly cloudy

Agent: The current weather in Tokyo is 22°C with partly cloudy skies and 65% humidity.
```

---

## 七、IPC 通信机制

### 7.1 IPC 文件写入

```typescript
function writeIpcFile(dir: string, data: object): string {
  fs.mkdirSync(dir, { recursive: true });

  // 唯一文件名
  const filename = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}.json`;
  const filepath = path.join(dir, filename);

  // 原子写入: 先写临时文件，再重命名
  const tempPath = `${filepath}.tmp`;
  fs.writeFileSync(tempPath, JSON.stringify(data, null, 2));
  fs.renameSync(tempPath, filepath);

  return filename;
}
```

### 7.2 Host 端轮询处理

```typescript
// src/index.ts - IPC Watcher
function startIpcWatcher(): void {
  const ipcBaseDir = path.join(DATA_DIR, 'ipc');

  const processIpcFiles = async () => {
    const groupFolders = fs.readdirSync(ipcBaseDir);

    for (const sourceGroup of groupFolders) {
      const messagesDir = path.join(ipcBaseDir, sourceGroup, 'messages');
      
      if (fs.existsSync(messagesDir)) {
        const files = fs.readdirSync(messagesDir).filter(f => f.endsWith('.json'));
        
        for (const file of files) {
          const data = JSON.parse(fs.readFileSync(path.join(messagesDir, file)));
          
          // 权限验证
          if (authorized(data, sourceGroup)) {
            await sock.sendMessage(data.chatJid, { text: data.text });
          }
          
          fs.unlinkSync(path.join(messagesDir, file));
        }
      }
    }

    setTimeout(processIpcFiles, IPC_POLL_INTERVAL);
  };

  processIpcFiles();
}
```

---

## 八、最佳实践

### 8.1 工具设计原则

| 原则 | 描述 |
|------|------|
| **单一职责** | 每个工具只做一件事 |
| **详细描述** | 描述中包含使用示例和注意事项 |
| **参数验证** | 使用 Zod 进行类型和格式验证 |
| **错误友好** | 返回清晰的错误信息 |
| **幂等性** | 相同输入产生相同结果 |

### 8.2 安全考虑

```typescript
// 1. 权限检查
if (!isMain) {
  return {
    content: [{ type: 'text', text: 'Permission denied' }],
    isError: true
  };
}

// 2. 输入验证
if (args.schedule_type === 'cron') {
  try {
    CronExpressionParser.parse(args.schedule_value);
  } catch {
    return {
      content: [{ type: 'text', text: 'Invalid cron expression' }],
      isError: true
    };
  }
}

// 3. 数据过滤
const tasks = isMain
  ? allTasks
  : allTasks.filter(t => t.groupFolder === groupFolder);
```

### 8.3 上下文传递

```typescript
// 通过 Context 传递运行时信息
export interface IpcMcpContext {
  chatJid: string;      // 当前聊天 JID
  groupFolder: string;  // 当前群组文件夹
  isMain: boolean;      // 是否是主群组
}

export function createIpcMcp(ctx: IpcMcpContext) {
  const { chatJid, groupFolder, isMain } = ctx;
  
  // 工具可以访问这些上下文
  return createSdkMcpServer({
    name: 'nanoclaw',
    tools: [
      tool('send_message', '...', { text: z.string() }, async (args) => {
        // 使用 chatJid 发送到正确的群组
        writeIpcFile(MESSAGES_DIR, {
          chatJid,  // 来自 context
          text: args.text
        });
        // ...
      })
    ]
  });
}
```

---

## 九、总结

### 9.1 MCP Server 核心要素

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MCP Server 核心要素                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. createSdkMcpServer({ name, version, tools })                   │
│     • name: Server 名称 (用于工具调用前缀)                            │
│     • version: 版本号                                                │
│     • tools: 工具数组                                                │
│                                                                      │
│  2. tool(name, description, schema, handler)                        │
│     • name: 工具名称                                                 │
│     • description: 详细描述 (给 LLM 看)                              │
│     • schema: Zod 定义的参数 Schema                                  │
│     • handler: async (args) => { content: [...] }                   │
│                                                                      │
│  3. 注册到 Agent SDK                                                 │
│     query({ options: { mcpServers: { name: server } } })            │
│                                                                      │
│  4. 工具调用格式                                                     │
│     mcp__{server_name}__{tool_name}                                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 9.2 NanoClaw MCP 工具列表

| 工具 | 用途 | 权限 |
|------|------|------|
| `send_message` | 发送 WhatsApp 消息 | 所有群组 |
| `schedule_task` | 创建定时任务 | 所有群组 |
| `list_tasks` | 列出任务 | 过滤后 |
| `pause_task` | 暂停任务 | 自己的任务 |
| `resume_task` | 恢复任务 | 自己的任务 |
| `cancel_task` | 取消任务 | 自己的任务 |
| `register_group` | 注册群组 | Main Only |
