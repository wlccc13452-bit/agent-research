# CodePilot 中 LLM 驱动本地 APP 分析

## 1. 概述

CodePilot 是一个桌面客户端，但它并非直接由 LLM "驱动"，而是通过集成 Claude Agent SDK，让 Claude Code CLI 在本地执行工具操作。LLM 的决策通过工具调用 (Tool Use) 转化为实际的本地操作。

## 2. LLM 驱动架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户界面 (React)                          │
│  ChatView → MessageInput → ToolCallBlock                       │
└────────────────────────┬────────────────────────────────────────┘
                         │ SSE 事件流
┌────────────────────────▼────────────────────────────────────────┐
│                    Next.js API 层                               │
│  /api/chat/route.ts → streamClaude()                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                Claude Agent SDK 集成层                          │
│  claude-client.ts: query() 函数                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │ 子进程
┌────────────────────────▼────────────────────────────────────────┐
│              Claude Code CLI (本地安装)                          │
│  - 执行工具调用                                                 │
│  - 文件系统操作                                                 │
│  - Git 操作                                                    │
│  - 终端命令                                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心驱动机制

LLM 通过以下机制驱动本地应用：

1. **工具调用 (Tool Use)**: LLM 决定需要执行什么操作
2. **工具执行**: Claude Code CLI 执行实际操作
3. **结果返回**: 执行结果返回给 LLM 进行下一步决策
4. **状态更新**: UI 通过 SSE 事件流实时更新

## 3. 工具调用流程

### 3.1 工具调用生命周期

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Assistant  │────▶│  tool_use   │────▶│   Execute   │────▶│ tool_result │
│   Message   │     │   Block     │     │   (CLI)     │     │    Block    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       │                   ▼                   ▼                   ▼
       │            ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
       │            │   SSE:      │     │   SSE:      │     │   SSE:      │
       └───────────▶│  tool_use   │     │ tool_output │     │ tool_result │
                    └─────────────┘     └─────────────┘     └─────────────┘
```

### 3.2 代码实现

#### 3.2.1 工具调用事件发送

```typescript
// claude-client.ts
case 'assistant': {
  const assistantMsg = message as SDKAssistantMessage;
  
  // 检查工具调用块
  for (const block of assistantMsg.message.content) {
    if (block.type === 'tool_use') {
      controller.enqueue(formatSSE({
        type: 'tool_use',
        data: JSON.stringify({
          id: block.id,
          name: block.name,
          input: block.input
        })
      }));
    }
  }
}
```

#### 3.2.2 工具结果处理

```typescript
case 'user': {
  // 工具执行结果作为用户消息返回
  const userMsg = message as SDKUserMessage;
  const content = userMsg.message.content;
  
  for (const block of content) {
    if (block.type === 'tool_result') {
      controller.enqueue(formatSSE({
        type: 'tool_result',
        data: JSON.stringify({
          tool_use_id: block.tool_use_id,
          content: resultContent,
          is_error: block.is_error
        })
      }));
    }
  }
}
```

#### 3.2.3 工具进度追踪

```typescript
case 'tool_progress': {
  const progressMsg = message as SDKToolProgressMessage;
  controller.enqueue(formatSSE({
    type: 'tool_output',
    data: JSON.stringify({
      _progress: true,
      tool_use_id: progressMsg.tool_use_id,
      tool_name: progressMsg.tool_name,
      elapsed_time_seconds: progressMsg.elapsed_time_seconds
    })
  }));
  
  // 工具超时检测
  if (toolTimeoutSeconds > 0 && 
      progressMsg.elapsed_time_seconds >= toolTimeoutSeconds) {
    controller.enqueue(formatSSE({
      type: 'tool_timeout',
      data: JSON.stringify({...})
    }));
    abortController?.abort();
  }
}
```

## 4. 本地操作能力

### 4.1 Claude Code 内置工具

Claude Code CLI 提供以下核心工具：

| 工具类别 | 工具 | 功能 |
|---|---|---|
| 文件操作 | `Read` | 读取文件内容 |
| | `Write` | 写入/覆盖文件 |
| | `Edit` | 编辑文件 |
| | `Bash` | 执行 Shell 命令 |
| | `Glob` | 文件搜索 |
| | `Grep` | 文本搜索 |
| Git 操作 | `Git` | Git 命令执行 |
| | `GitCommit` | 提交更改 |
| | `GitPush` | 推送到远程 |
| Web 操作 | `WebFetch` | 获取网页内容 |
| | `WebSearch` | 网络搜索 |
| 终端操作 | `Terminal` | 终端命令执行 |

### 4.2 MCP 扩展工具

CodePilot 支持通过 MCP (Model Context Protocol) 扩展工具：

```typescript
// MCP 服务器配置
interface MCPServerConfig {
  type: 'stdio' | 'sse' | 'http';
  command?: string;    // stdio 模式命令
  args?: string[];     // 命令参数
  env?: Record<string, string>;  // 环境变量
  url?: string;        // sse/http 模式 URL
  headers?: Record<string, string>;  // HTTP 头
}
```

### 4.3 自定义 Skills

Skills 是基于提示词的可重用人设或任务模板：

```yaml
---
name: 代码审查
description: 对代码进行安全审查
---
你是一个专业的代码审查专家...
```

## 5. 前端交互实现

### 5.1 工具调用 UI 展示

```typescript
// components/ai-elements/tool.tsx
interface ToolCallBlockProps {
  id: string;
  name: string;
  input: Record<string, unknown>;
  isExecuting?: boolean;
  result?: string;
}

// 工具调用卡片展示
<div className="tool-call-block">
  <div className="tool-header">
    <span className="tool-icon">⚙️</span>
    <span className="tool-name">{name}</span>
    {isExecuting && <span className="executing">执行中...</span>}
  </div>
  <pre className="tool-input">{JSON.stringify(input, null, 2)}</pre>
  {result && <pre className="tool-result">{result}</pre>}
</div>
```

### 5.2 实时输出流

```typescript
// stream-session-manager.ts
interface ActiveStream {
  sessionId: string;
  abortController: AbortController;
  snapshot: SessionStreamSnapshot;
  // 实时累积
  accumulatedText: string;
  toolUsesArray: ToolUseInfo[];
  toolResultsArray: ToolResultInfo[];
  toolOutputAccumulated: string;
}

// 工具输出处理
onToolOutput: (data: string) => {
  stream.toolOutputAccumulated += data;
  emitSnapshot();
}
```

### 5.3 权限审批 UI

```typescript
// ChatView.tsx
const pendingPermission = streamSnapshot?.pendingPermission ?? null;

{pendingPermission && (
  <ConfirmationDialog
    title="权限请求"
    tool={pendingPermission.tool_name}
    input={pendingPermission.tool_input}
    onApprove={() => respondToPermission(pendingPermission.id, 'allow')}
    onDeny={() => respondToPermission(pendingPermission.id, 'deny')}
  />
)}
```

## 6. Electron 集成

### 6.1 主进程职责

Electron 主进程负责启动和管理本地 Claude Code CLI：

```typescript
// electron/main.ts
// 1. 启动 Next.js 服务器
const serverProcess = spawn('node', ['dist/server.js'], {
  cwd: app.getAppPath(),
  env: { ...userShellEnv, PORT: String(freePort) }
});

// 2. 窗口管理
const mainWindow = new BrowserWindow({
  webPreferences: {
    preload: path.join(__dirname, 'preload.js'),
    contextIsolation: true
  }
});

// 3. IPC 通信
ipcMain.handle('open-folder-dialog', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  return result.filePaths[0];
});
```

### 6.2 Preload 桥接

```typescript
// electron/preload.ts
contextBridge.exposeInMainWorld('electronAPI', {
  openFolder: () => ipcRenderer.invoke('open-folder-dialog'),
  openFile: (path: string) => ipcRenderer.invoke('open-file', path),
  onMenuAction: (callback) => ipcRenderer.on('menu-action', callback)
});
```

## 7. 数据持久化

### 7.1 SQLite 存储

所有对话数据存储在本地 SQLite 数据库：

```typescript
// db.ts
CREATE TABLE chat_sessions (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  model TEXT,
  working_directory TEXT,
  sdk_session_id TEXT
);

CREATE TABLE messages (
  id TEXT PRIMARY KEY,
  session_id TEXT REFERENCES chat_sessions(id),
  role TEXT CHECK(role IN ('user', 'assistant')),
  content TEXT,
  token_usage TEXT
);
```

### 7.2 文件系统交互

```typescript
// 附件上传处理
const uploadDir = path.join(workDir, '.codepilot-uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// 保存附件
const filePath = path.join(uploadDir, `${Date.now()}-${safeName}`);
fs.writeFileSync(filePath, buffer);
```

## 8. 实现特点与不足

### 8.1 实现特点

1. **间接驱动**: LLM 不直接操作本地资源，而是通过 Claude Code CLI
2. **流式响应**: 实时展示工具执行进度
3. **权限控制**: 用户可以审批或拒绝工具调用
4. **跨平台**: 支持 macOS、Windows、Linux

### 8.2 潜在不足

1. **依赖 CLI**: 严重依赖本地安装的 Claude Code CLI
2. **工具限制**: 受限于 Claude Code 支持的工具集
3. **安全性**: 工具执行权限完全由用户控制，存在误操作风险
4. **离线可用性**: 需要网络连接 Claude API
5. **调试困难**: 工具执行错误难以追溯

### 8.3 改进建议

1. **沙盒执行**: 考虑在沙盒环境中执行敏感工具
2. **操作日志**: 增加更详细的操作审计日志
3. **回滚机制**: 文件修改前自动备份，支持回滚
4. **离线缓存**: 支持基本功能的离线使用
