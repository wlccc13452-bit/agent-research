# Kilocode 架构与框架研究

## 一、项目概述

**Kilocode** 是一个开源的 VS Code AI 编程助手扩展，支持 500+ AI 模型，提供代码生成、任务自动化、自动补全等功能。

**仓库地址**: https://github.com/Kilo-Org/kilocode

**关键数据**:
- OpenRouter 排名 #1
- 1.5M+ 用户
- 25T+ tokens 处理量

---

## 二、计算架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          VS Code Extension Host                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                        Extension Core                              │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│  │  │ ClineProvider│ │   Task      │ │   Tools     │ │   Modes     │ │ │
│  │  │ (State Mgr) │ │ (Execution) │ │ (Actions)   │ │ (Architect/ │ │ │
│  │  │             │ │             │ │             │ │ Code/Debug) │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                   │                                     │
│                                   ▼                                     │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                        Services Layer                              │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│  │  │     MCP     │ │   Browser   │ │ Code Index  │ │ Checkpoints │ │ │
│  │  │  (Protocol) │ │  (Puppeteer)│ │ (Tree-sitter)│ │  (Restore)  │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│  │  │ Autocomplete│ │  Telemetry  │ │ Settings Sync│ │ Marketplace │ │ │
│  │  │  (Inline)   │ │  (PostHog)  │ │   (Cloud)   │ │    (MCP)    │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                   │                                     │
│                                   ▼                                     │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                         API Layer                                  │ │
│  │  ┌─────────────────────────────────────────────────────────────┐  │ │
│  │  │              50+ AI Providers                                │  │ │
│  │  │  Anthropic │ OpenAI │ Google │ OpenRouter │ ...            │  │ │
│  │  └─────────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Webview UI (React)                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │    Chat     │ │   History   │ │   Settings  │ │   Marketplace│       │
│  │    View     │ │    View     │ │     View    │ │     View    │       │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Monorepo 结构

```
kilocode/
├── src/                      # VS Code 扩展核心
│   ├── api/                  # 50+ AI 提供商实现
│   │   └── providers/        # Anthropic, OpenAI, Google, etc.
│   ├── core/                 # 核心逻辑
│   │   ├── tools/            # 工具实现 (27个工具)
│   │   ├── task/             # 任务执行引擎
│   │   ├── prompts/          # System prompts
│   │   └── config/           # 配置管理
│   ├── services/             # 服务层
│   │   ├── mcp/              # MCP 协议
│   │   ├── browser/          # 浏览器自动化
│   │   ├── autocomplete/     # 代码补全
│   │   └── code-index/       # 代码索引
│   └── integrations/         # VS Code 集成
│       ├── terminal/         # 终端集成
│       └── editor/           # 编辑器集成
├── webview-ui/               # React 前端
├── packages/                 # 共享包
│   ├── types/                # 类型定义
│   ├── ipc/                  # 进程间通信
│   ├── telemetry/            # 遥测
│   ├── cloud/                # 云服务
│   └── agent-runtime/        # 独立 Agent 运行时
└── jetbrains/                # JetBrains 插件
```

### 2.3 核心组件详解

#### 2.3.1 Task 执行引擎

```typescript
// src/core/task/Task.ts
class Task {
  // 任务状态
  state: "idle" | "executing" | "waiting" | "completed"
  
  // 工具调用循环
  async executeLoop() {
    while (!this.shouldAbort) {
      // 1. 获取 LLM 响应
      const response = await this.api.createMessage(messages)
      
      // 2. 处理文本内容
      for (const block of response.content) {
        if (block.type === "text") {
          await this.handleTextBlock(block)
        }
      }
      
      // 3. 处理工具调用
      for (const block of response.content) {
        if (block.type === "tool_use") {
          await this.handleToolUse(block)
        }
      }
      
      // 4. 检查是否完成
      if (this.isComplete) break
    }
  }
}
```

#### 2.3.2 Tools 系统

```typescript
// 工具基类
abstract class BaseTool<TName extends ToolName> {
  abstract name: TName
  abstract parseLegacy(params: Partial<Record<string, string>>): ToolParams<TName>
  abstract execute(params: ToolParams<TName>, task: Task, callbacks: ToolCallbacks): Promise<void>
  
  async handle(task: Task, block: ToolUse<TName>, callbacks: ToolCallbacks): Promise<void> {
    // 1. 处理流式部分消息
    if (block.partial) {
      await this.handlePartial(task, block)
      return
    }
    
    // 2. 解析参数
    const params = block.nativeArgs ?? this.parseLegacy(block.params)
    
    // 3. 执行工具
    await this.execute(params, task, callbacks)
  }
}
```

**核心工具列表：**

| 工具 | 功能 | 文件大小 |
|------|------|----------|
| `read_file` | 读取文件 | 32KB |
| `write_to_file` | 写入文件 | 10KB |
| `edit_file` | 编辑文件 | 22KB |
| `apply_diff` | 应用差异 | 11KB |
| `apply_patch` | 应用补丁 | 15KB |
| `execute_command` | 执行命令 | 13KB |
| `browser_action` | 浏览器操作 | 10KB |
| `codebase_search` | 代码搜索 | 9KB |
| `use_mcp_tool` | MCP 工具 | 10KB |

#### 2.3.3 Modes 系统

```typescript
// 三种模式
type Mode = "architect" | "code" | "debug"

// 模式切换工具
class SwitchModeTool extends BaseTool<"switch_mode"> {
  async execute(params: { mode: Mode }, task: Task, callbacks: ToolCallbacks) {
    // 切换模式会改变 system prompt
    task.mode = params.mode
    task.systemPrompt = buildSystemPrompt(params.mode)
  }
}
```

**模式说明：**
- **Architect**: 规划和设计模式，专注于架构设计
- **Code**: 编码模式，专注于代码实现
- **Debug**: 调试模式，专注于问题诊断

---

## 三、Agent Runtime 架构

### 3.1 独立运行时

Kilocode 提供了一个独立的 Agent 运行时，可以在没有 VS Code 的情况下运行：

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Agent Runtime Architecture                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐     fork()      ┌─────────────────────┐  │
│  │   Agent Manager     │ ───────────────▶│   Agent Process     │  │
│  │                     │◀───── IPC ─────▶│  (extension host)   │  │
│  └─────────────────────┘                 └─────────────────────┘  │
│                                                                     │
│  ExtensionHost: VS Code API Mock                                    │
│  MessageBridge: 双向 IPC 通信                                       │
│  ExtensionService: 生命周期管理                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Agent 启动配置

```typescript
import { fork } from "child_process"

const agent = fork(require.resolve("@kilocode/agent-runtime/process"), [], {
  env: {
    AGENT_CONFIG: JSON.stringify({
      workspace: "/path/to/project",
      providerSettings: { apiProvider: "anthropic", apiKey: "..." },
      mode: "code",
      autoApprove: false,
    }),
  },
  stdio: ["pipe", "pipe", "pipe", "ipc"],
})

agent.on("message", (msg) => {
  if (msg.type === "ready") {
    agent.send({ type: "sendMessage", payload: { type: "newTask", text: "Fix the bug" } })
  }
})
```

### 3.3 消息协议

| 方向 | 类型 | 描述 |
|------|------|------|
| Parent → Agent | `sendMessage` | 发送用户消息到扩展 |
| Parent → Agent | `injectConfig` | 更新扩展配置 |
| Parent → Agent | `shutdown` | 优雅终止 Agent |
| Agent → Parent | `ready` | Agent 初始化完成 |
| Agent → Parent | `message` | 扩展消息 |
| Agent → Parent | `stateChange` | 状态更新 |

---

## 四、API 提供商架构

### 4.1 多提供商支持

```
┌─────────────────────────────────────────────────────────────────────┐
│                      API Provider Architecture                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                      ┌─────────────────┐                            │
│                      │   BaseHandler   │                            │
│                      └────────┬────────┘                            │
│                               │                                     │
│           ┌───────────────────┼───────────────────┐                 │
│           │                   │                   │                 │
│  ┌────────▼────────┐ ┌────────▼────────┐ ┌───────▼────────┐       │
│  │ AnthropicHandler│ │  OpenAIHandler  │ │  GoogleHandler │       │
│  └─────────────────┘ └─────────────────┘ └────────────────┘       │
│           │                   │                   │                 │
│           └───────────────────┼───────────────────┘                 │
│                               │                                     │
│                      ┌────────▼────────┐                            │
│                      │   OpenRouter    │                            │
│                      │   (Aggregator)  │                            │
│                      └─────────────────┘                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 提供商实现

```typescript
// src/api/providers/anthropic.ts
export class AnthropicHandler implements ApiHandler {
  async createMessage(params: ApiHandlerMessageOptions): Promise<ApiStream> {
    const response = await this.client.messages.create({
      model: params.modelId,
      messages: params.messages,
      tools: params.tools,
      system: params.systemPrompt,
      // ... 其他参数
    })
    return response
  }
}
```

### 4.3 模型缓存

```typescript
// 自动缓存模型列表
export async function initializeModelCacheRefresh() {
  // 定期刷新模型列表
  setInterval(async () => {
    await refreshModels()
  }, 1000 * 60 * 60) // 每小时刷新
}
```

---

## 五、服务层架构

### 5.1 MCP (Model Context Protocol)

```typescript
// MCP 服务器管理
export class McpServerManager {
  private servers: Map<string, McpServer> = new Map()
  
  async connectServer(name: string, config: McpServerConfig) {
    const server = await McpServer.create(config)
    this.servers.set(name, server)
  }
  
  async listTools(serverName: string): Promise<Tool[]> {
    const server = this.servers.get(serverName)
    return server?.listTools() ?? []
  }
  
  async callTool(serverName: string, toolName: string, args: any) {
    const server = this.servers.get(serverName)
    return server?.callTool(toolName, args)
  }
}
```

### 5.2 代码索引

```typescript
// Tree-sitter 代码索引
export class CodeIndexManager {
  private parsers: Map<string, Parser> = new Map()
  
  async indexFile(filePath: string): Promise<IndexEntry[]> {
    const parser = this.getParser(filePath)
    const tree = parser.parse(await fs.readFile(filePath, "utf-8"))
    
    // 提取符号定义
    const definitions = this.extractDefinitions(tree)
    
    return definitions
  }
}
```

### 5.3 自动补全

```typescript
// 内联代码补全
export class AutocompleteProvider {
  async provideInlineCompletionItems(
    document: vscode.TextDocument,
    position: vscode.Position
  ): Promise<vscode.InlineCompletionItem[]> {
    // 1. 获取上下文
    const context = this.getContext(document, position)
    
    // 2. 调用 LLM
    const completion = await this.getCompletion(context)
    
    // 3. 返回补全项
    return [new vscode.InlineCompletionItem(completion)]
  }
}
```

---

## 六、关键源文件

| 文件/目录 | 功能 | 文件数 |
|-----------|------|--------|
| `src/api/providers/` | AI 提供商实现 | 216 |
| `src/core/tools/` | 工具实现 | 27 |
| `src/services/` | 服务层 | 500+ |
| `src/core/prompts/` | System Prompts | 95 |
| `webview-ui/` | React UI | - |
| `packages/` | 共享包 | 96 |

---

## 七、与其他项目对比

| 维度 | Kilocode | OpenClaw | Agentic Finance Review |
|------|----------|----------|------------------------|
| 平台 | VS Code Extension | CLI + 多通道 | CLI |
| 验证机制 | ❌ 无 | ❌ 无 | ✅ Hook 验证 |
| 迭代模式 | 任务驱动 | 单轮对话 | 流水线 |
| 工具数量 | 27 | ~10 | 验证器 8 |
| AI 提供商 | 50+ | 50+ | 1 (Opus) |
| 运行时 | VS Code / 独立 | CLI | CLI |

---

## 八、总结

### 8.1 核心架构特点

1. **Monorepo 结构** - 清晰的模块划分
2. **插件化工具** - 基于 BaseTool 的工具系统
3. **多提供商支持** - 统一的 API 抽象
4. **独立运行时** - 可脱离 VS Code 运行
5. **MCP 协议** - 标准化的工具扩展

### 8.2 技术栈

| 层级 | 技术 |
|------|------|
| 扩展框架 | VS Code Extension API |
| 前端 | React + Tailwind CSS |
| 后端 | TypeScript |
| 构建工具 | esbuild + Turbo |
| 测试 | Vitest |
| 通信 | IPC + JSON-RPC |
