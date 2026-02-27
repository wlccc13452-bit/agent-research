# OpenClaw MCP Server 使用研究

## 一、核心发现：OpenClaw 使用 ACP 而非 MCP

### 1.1 协议架构对比

| 维度 | MCP (Model Context Protocol) | ACP (Agent Client Protocol) |
|------|------------------------------|-----------------------------|
| **来源** | Anthropic | @agentclientprotocol/sdk |
| **用途** | LLM 与工具交互 | Agent 与 Client 通信 |
| **NanoClaw** | ✅ 直接使用 | ❌ |
| **OpenClaw** | ❌ 通过 mcporter | ✅ 主要协议 |

### 1.2 OpenClaw 对 MCP 的态度

```typescript
// src/acp/translator.ts (第 123-126 行)
async newSession(params: NewSessionRequest): Promise<NewSessionResponse> {
  if (params.mcpServers.length > 0) {
    this.log(`ignoring ${params.mcpServers.length} MCP servers`);
  }
  // ...
}

// src/acp/translator.ts (第 153-156 行)
async loadSession(params: LoadSessionRequest): Promise<LoadSessionResponse> {
  if (params.mcpServers.length > 0) {
    this.log(`ignoring ${params.mcpServers.length} MCP servers`);
  }
  // ...
}
```

**关键结论**：OpenClaw 的 ACP 实现显式忽略 MCP servers，表明两者是独立的协议体系。

---

## 二、ACP (Agent Client Protocol) 详解

### 2.1 ACP 架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ACP Architecture                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────┐                    ┌────────────────┐           │
│  │  Client Side   │                    │  Agent Side    │           │
│  │  Connection    │◄──── ndjson ──────►│  Connection    │           │
│  └───────┬────────┘                    └───────┬────────┘           │
│          │                                     │                     │
│          ▼                                     ▼                     │
│  ┌────────────────┐                    ┌────────────────┐           │
│  │  Client        │                    │  Gateway       │           │
│  │  (CLI/UI)      │                    │  (OpenClaw)    │           │
│  └────────────────┘                    └───────┬────────┘           │
│                                                 │                     │
│                                                 ▼                     │
│                                        ┌────────────────┐           │
│                                        │  LLM Provider  │           │
│                                        │  (Claude/etc)  │           │
│                                        └────────────────┘           │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 ACP 核心类型

```typescript
// 来自 @agentclientprotocol/sdk
type AgentCapabilities = {
  loadSession: boolean;
  promptCapabilities: {
    image: boolean;
    audio: boolean;
    embeddedContext: boolean;
  };
  mcpCapabilities: {
    http: boolean;
    sse: boolean;
  };
  sessionCapabilities: {
    list: {};
  };
};

type SessionUpdate = 
  | { sessionUpdate: "agent_message_chunk"; content: { type: "text"; text: string } }
  | { sessionUpdate: "tool_call"; toolCallId: string; title: string; status: string }
  | { sessionUpdate: "tool_call_update"; toolCallId: string; status: string }
  | { sessionUpdate: "available_commands_update"; availableCommands: Command[] };
```

### 2.3 ACP 客户端实现

```typescript
// src/acp/client.ts
export async function createAcpClient(opts: AcpClientOptions = {}): Promise<AcpClientHandle> {
  // 1. 启动 Agent 进程
  const agent = spawn(serverCommand, effectiveArgs, {
    stdio: ["pipe", "pipe", "inherit"],
    cwd,
  });

  // 2. 创建 ndjson 流
  const input = Writable.toWeb(agent.stdin);
  const output = Readable.toWeb(agent.stdout);
  const stream = ndJsonStream(input, output);

  // 3. 创建客户端连接
  const client = new ClientSideConnection(
    () => ({
      sessionUpdate: async (params: SessionNotification) => {
        printSessionUpdate(params);
      },
      requestPermission: async (params: RequestPermissionRequest) => {
        return resolvePermissionRequest(params);
      },
    }),
    stream,
  );

  // 4. 初始化
  await client.initialize({
    protocolVersion: PROTOCOL_VERSION,
    clientCapabilities: {
      fs: { readTextFile: true, writeTextFile: true },
      terminal: true,
    },
    clientInfo: { name: "openclaw-acp-client", version: "1.0.0" },
  });

  // 5. 创建会话
  const session = await client.newSession({
    cwd,
    mcpServers: [],  // ← MCP servers 被忽略
  });

  return { client, agent, sessionId: session.sessionId };
}
```

### 2.4 ACP 服务端实现

```typescript
// src/acp/translator.ts
export class AcpGatewayAgent implements Agent {
  private connection: AgentSideConnection;
  private gateway: GatewayClient;

  async initialize(_params: InitializeRequest): Promise<InitializeResponse> {
    return {
      protocolVersion: PROTOCOL_VERSION,
      agentCapabilities: {
        loadSession: true,
        promptCapabilities: {
          image: true,
          audio: false,
          embeddedContext: true,
        },
        mcpCapabilities: {
          http: false,  // ← 不支持 MCP HTTP
          sse: false,   // ← 不支持 MCP SSE
        },
        sessionCapabilities: {
          list: {},
        },
      },
      agentInfo: ACP_AGENT_INFO,
      authMethods: [],
    };
  }

  async prompt(params: PromptRequest): Promise<PromptResponse> {
    const session = this.sessionStore.getSession(params.sessionId);
    const userText = extractTextFromPrompt(params.prompt);
    
    // 通过 Gateway 发送消息
    await this.gateway.request("chat.send", {
      sessionKey: session.sessionKey,
      message: userText,
    });
    
    // 等待响应
    return new Promise((resolve) => {
      this.pendingPrompts.set(params.sessionId, { resolve, ... });
    });
  }
}
```

---

## 三、mcporter：OpenClaw 的 MCP 桥接工具

### 3.1 mcporter Skill

```yaml
# skills/mcporter/SKILL.md
---
name: mcporter
description: Use the mcporter CLI to list, configure, auth, and call MCP servers/tools directly
homepage: http://mcporter.dev
---
```

### 3.2 mcporter 使用方式

**安装**：
```bash
npm install -g mcporter
```

**核心命令**：

```bash
# 列出 MCP servers
mcporter list

# 列出 server 的工具 (带 schema)
mcporter list <server> --schema

# 调用工具
mcporter call <server.tool> key=value
mcporter call "linear.create_issue(title: \"Bug\")"

# HTTP URL 调用
mcporter call https://api.example.com/mcp.fetch url:https://example.com

# Stdio 调用
mcporter call --stdio "bun run ./server.ts" scrape url=https://example.com

# JSON 参数
mcporter call <server.tool> --args '{"limit":5}'

# OAuth 认证
mcporter auth <server | url> [--reset]

# 配置管理
mcporter config list|get|add|remove|import|login|logout

# 守护进程
mcporter daemon start|status|stop|restart

# 代码生成
mcporter generate-cli --server <name>
mcporter emit-ts <server> --mode client|types
```

### 3.3 mcporter 配置

```json
// 默认配置位置: ./config/mcporter.json
{
  "servers": {
    "linear": {
      "type": "http",
      "url": "https://api.linear.app/mcp"
    },
    "github": {
      "type": "stdio",
      "command": "npx @github/mcp-server"
    }
  }
}
```

---

## 四、ACP vs MCP 对比

### 4.1 协议层级

```
MCP (Model Context Protocol):
  LLM ↔ Tools/Servers
  
ACP (Agent Client Protocol):
  Client ↔ Agent ↔ Gateway ↔ LLM Provider
```

### 4.2 能力对比

| 能力 | MCP | ACP |
|------|-----|-----|
| 工具调用 | ✅ 核心功能 | ✅ 通过 tool_call |
| 会话管理 | ❌ | ✅ newSession/loadSession |
| 流式响应 | ✅ | ✅ agent_message_chunk |
| 权限请求 | ❌ | ✅ requestPermission |
| 多模态 | ✅ | ✅ promptCapabilities |
| HTTP/SSE | ✅ | ❌ (mcpCapabilities: false) |

### 4.3 工具调用对比

**MCP (NanoClaw)**:
```typescript
// Agent 直接调用 MCP 工具
await mcp__nanoclaw__send_message({ text: "Hello" });
```

**ACP (OpenClaw)**:
```typescript
// 通过 sessionUpdate 接收工具调用事件
await connection.sessionUpdate({
  sessionId,
  update: {
    sessionUpdate: "tool_call",
    toolCallId: "call-123",
    title: "send_message",
    status: "in_progress",
    rawInput: { text: "Hello" },
    kind: "message",
  },
});
```

---

## 五、OpenClaw 工具调用流程

### 5.1 完整流程

```
1. Client 调用 prompt()
   │
   ▼
2. AcpGatewayAgent.prompt()
   │  - 提取文本
   │  - 通过 Gateway 发送
   │
   ▼
3. Gateway 转发到 LLM Provider
   │
   ▼
4. LLM 返回工具调用
   │
   ▼
5. handleAgentEvent() 处理工具事件
   │  - phase: "start" → tool_call
   │  - phase: "result" → tool_call_update
   │
   ▼
6. connection.sessionUpdate() 发送给 Client
   │
   ▼
7. Client 显示工具状态
```

### 5.2 工具事件处理

```typescript
// src/acp/translator.ts
private async handleAgentEvent(evt: EventFrame): Promise<void> {
  const { phase, name, toolCallId } = data;

  if (phase === "start") {
    // 工具开始执行
    await this.connection.sessionUpdate({
      sessionId: pending.sessionId,
      update: {
        sessionUpdate: "tool_call",
        toolCallId,
        title: formatToolTitle(name, args),
        status: "in_progress",
        rawInput: args,
        kind: inferToolKind(name),  // "read", "write", "execute", etc.
      },
    });
  }

  if (phase === "result") {
    // 工具执行完成
    const isError = Boolean(data.isError);
    await this.connection.sessionUpdate({
      sessionId: pending.sessionId,
      update: {
        sessionUpdate: "tool_call_update",
        toolCallId,
        status: isError ? "failed" : "completed",
        rawOutput: data.result,
      },
    });
  }
}
```

### 5.3 权限处理

```typescript
// src/acp/client.ts
function resolvePermissionRequest(
  params: RequestPermissionRequest,
  deps: PermissionResolverDeps = {},
): Promise<RequestPermissionResponse> {
  const toolKind = resolveToolKindForPermission(params, toolName);
  
  // 安全类型自动批准
  const SAFE_AUTO_APPROVE_KINDS = new Set(["read", "search"]);
  const isSafeKind = SAFE_AUTO_APPROVE_KINDS.has(toolKind);
  
  // 危险工具需要确认
  const promptRequired = !toolName || !isSafeKind || DANGEROUS_ACP_TOOLS.has(toolName);

  if (!promptRequired) {
    return selectedPermission(allowOption);  // 自动批准
  }

  // 需要用户确认
  const approved = await prompt(toolName, toolTitle);
  return approved ? selectedPermission(allowOption) : selectedPermission(rejectOption);
}
```

---

## 六、如何在 OpenClaw 中使用 MCP

### 6.1 通过 mcporter 调用 MCP Server

```bash
# 列出可用的 MCP servers
mcporter list

# 调用 Linear MCP 工具
mcporter call linear.list_issues team=ENG limit:5

# 调用 GitHub MCP 工具
mcporter call github.create_issue title="Bug report" body="Description"

# 使用 stdio 启动临时 MCP server
mcporter call --stdio "npx @anthropic/mcp-server" some_tool param=value
```

### 6.2 在 OpenClaw Agent 中集成

```typescript
// 通过 Bash 工具调用 mcporter
async function callMcpTool(server: string, tool: string, args: Record<string, unknown>) {
  const argsStr = Object.entries(args)
    .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
    .join(" ");
  
  const result = await execCommand(`mcporter call ${server}.${tool} ${argsStr}`);
  return JSON.parse(result);
}

// 使用示例
const issues = await callMcpTool("linear", "list_issues", { 
  team: "ENG", 
  limit: 5 
});
```

### 6.3 创建 MCP Server 配置

```json
// config/mcporter.json
{
  "servers": {
    "linear": {
      "type": "http",
      "url": "https://api.linear.app/mcp",
      "auth": {
        "type": "bearer",
        "token": "${LINEAR_API_KEY}"
      }
    },
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["@github/mcp-server"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "custom": {
      "type": "stdio",
      "command": "node",
      "args": ["./my-mcp-server.js"]
    }
  }
}
```

---

## 七、MCP Server 开发规范

### 7.1 Stdio MCP Server 示例

```typescript
// my-mcp-server.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server(
  { name: "my-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// 定义工具
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "hello",
      description: "Say hello",
      inputSchema: {
        type: "object",
        properties: {
          name: { type: "string", description: "Name to greet" }
        },
        required: ["name"]
      }
    }
  ]
}));

// 处理工具调用
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  if (name === "hello") {
    return {
      content: [{
        type: "text",
        text: `Hello, ${args.name}!`
      }]
    };
  }
  
  throw new Error(`Unknown tool: ${name}`);
});

// 启动服务
const transport = new StdioServerTransport();
await server.connect(transport);
```

### 7.2 HTTP MCP Server 示例

```typescript
// my-http-mcp-server.ts
import express from "express";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

const app = express();

app.get("/sse", async (req, res) => {
  const server = new Server(
    { name: "my-http-server", version: "1.0.0" },
    { capabilities: { tools: {} } }
  );
  
  const transport = new SSEServerTransport("/message", res);
  await server.connect(transport);
});

app.post("/message", async (req, res) => {
  // 处理消息
});

app.listen(3000);
```

---

## 八、总结

### 8.1 OpenClaw MCP 使用方式

| 方式 | 说明 |
|------|------|
| **ACP 协议** | OpenClaw 主要使用 ACP，不直接支持 MCP |
| **mcporter** | 通过 mcporter CLI 与 MCP servers 交互 |
| **Skill 集成** | 在 agent 中通过 Bash 调用 mcporter |

### 8.2 ACP vs MCP 选择建议

| 场景 | 推荐 |
|------|------|
| Agent-Client 通信 | ACP |
| LLM-Tool 交互 | MCP |
| 多会话管理 | ACP |
| 工具扩展 | MCP (通过 mcporter) |
| 流式响应 | 两者都支持 |

### 8.3 关键差异

```
NanoClaw:
  MCP Server → 直接集成到 Claude Agent SDK
  工具调用 → mcp__{server}__{tool}

OpenClaw:
  ACP → Agent-Client 通信协议
  MCP → 通过 mcporter CLI 间接使用
  工具调用 → sessionUpdate(tool_call)
```
