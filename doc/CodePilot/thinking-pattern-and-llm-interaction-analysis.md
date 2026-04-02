# CodePilot 思维模式与 LLM 交互分析

## 1. 核心功能与迭代机制

### 1.1 会话管理

CodePilot 的核心功能围绕会话 (Session) 展开：

- **会话创建**: 用户可以创建新聊天会话
- **会话持久化**: 所有会话存储在 SQLite 数据库中 `~/.codepilot/codepilot.db`
- **会话恢复**: 支持通过 `sdk_session_id` 恢复之前的对话上下文
- **会话模式**: 支持 Code、Plan、Ask 三种交互模式

### 1.2 消息迭代机制

#### 对话流程

```
用户输入 → API /api/chat → streamClaude() → Claude Agent SDK query()
                                                      ↓
                                              SSE 流式响应
                                                      ↓
前端渲染 ← useSSEStream() ← stream-session-manager ← 事件处理
```

#### 消息类型

1. **用户消息 (user)**
   - 文本内容
   - 文件/图像附件（多模态）
   
2. **助手消息 (assistant)**
   - 文本块 (`text`)
   - 工具调用块 (`tool_use`)
   
3. **工具结果消息 (tool_result)**
   - 工具执行结果
   - 错误标志

### 1.3 会话恢复机制

```typescript
// 尝试恢复会话
let conversation = query({
  prompt: finalPrompt,
  options: { resume: sdkSessionId }
});

// 如果恢复失败，自动降级为全新会话
if (shouldResume) {
  try {
    const iter = conversation[Symbol.asyncIterator]();
    const first = await iter.next();
    // 验证恢复是否成功
  } catch (resumeError) {
    delete queryOptions.resume;
    conversation = query({
      prompt: buildFinalPrompt(true),
      options: queryOptions
    });
  }
}
```

会话恢复失败时，系统会：
1.日志
2. 记录警告 更新数据库清除 `sdk_session_id`
3. 向前端发送通知
4. 自动降级为使用历史上下文的全新会话

## 2. 思维模式分析

### 2.1 Claude Code 的内置思维链

CodePilot 基于 Claude Code (Claude Agent SDK)，其思维模式继承自 Claude AI：

- **推理过程**: 通过 `reasoning` 块展示思考过程
- **工具使用**: AI 自主决定何时调用工具
- **逐步执行**: 复杂任务分解为多个步骤

### 2.2 思维链维持机制

#### 2.2.1 会话上下文

```typescript
// 构建最终提示词时包含历史消息
const buildFinalPrompt = (includeHistory: boolean) => {
  const messages = includeHistory ? getMessages(sessionId) : [];
  const historyText = messages.map(m => 
    `${m.role}: ${m.content}`
  ).join('\n\n');
  
  return `${systemPrompt}\n\n${historyText}\n\nuser: ${currentMessage}`;
};
```

#### 2.2.2 流式事件处理

Claude Agent SDK 返回的事件流维持思维链：

```
assistant (thinking) → stream_event (delta) → tool_use → user (tool_result) → assistant → ...
```

### 2.3 交互模式

CodePilot 支持三种交互模式，通过 `/api/chat/mode` 切换：

| 模式 | 描述 | 权限级别 |
|---|---|---|
| `code` | 代码模式，允许所有工具 | 最高 |
| `plan` | 计划模式，只读工具 | 中等 |
| `ask` | 问答模式，禁止工具 | 最低 |

模式变更会实时发送到正在进行的会话中：

```typescript
controller.enqueue(formatSSE({
  type: 'mode_changed',
  data: permissionMode
}));
```

## 3. LLM 交互设计

### 3.1 交互架构

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   前端 UI    │ ←→  │  Next.js API │ ←→  │Claude Agent  │
│  (React)     │ SSE │  (SSE Stream)│     │   SDK        │
└──────────────┘     └──────────────┘     └──────────────┘
       ↓                     ↓                     ↓
  ChatView           route.ts           query() 函数
  MessageInput       streamClaude()     CLI 进程
  ToolCallBlock      SSE 格式化          工具执行
```

### 3.2 核心交互特点

#### 3.2.1 SSE 流式传输

- 实时流式响应，无需等待完整响应
- 支持多种事件类型（文本、工具调用、进度等）
- 事件缓冲区处理不完整的 SSE 数据

```typescript
// 客户端 SSE 处理
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';  // 处理不完整的行
  
  for (const line of lines) {
    if (!line.startsWith('data: ')) continue;
    const event = JSON.parse(line.slice(6));
    accumulated = handleSSEEvent(event, accumulated, callbacks);
  }
}
```

#### 3.2.2 工具调用可视化

```typescript
// 工具调用事件
case 'tool_use': {
  controller.enqueue(formatSSE({
    type: 'tool_use',
    data: JSON.stringify({
      id: block.id,
      name: block.name,
      input: block.input
    })
  }));
}

// 工具结果事件
case 'tool_result': {
  controller.enqueue(formatSSE({
    type: 'tool_result',
    data: JSON.stringify({
      tool_use_id: block.tool_use_id,
      content: resultContent,
      is_error: block.is_error
    })
  }));
}
```

#### 3.2.3 Token 使用统计

每个响应都包含详细的 token 使用信息：

```typescript
interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  cache_read_input_tokens: number;
  cache_creation_input_tokens: number;
  cost_usd?: string;
}
```

### 3.3 权限审批系统

CodePilot 实现了完整的权限审批流程：

```
LLM 请求工具 → permission_request 事件 → 用户审批 → allow/deny → 工具执行
```

```typescript
// 注册待处理权限
export function registerPendingPermission(
  id: string,
  toolInput: Record<string, unknown>,
  abortSignal?: AbortSignal
): Promise<PermissionResult> {
  // 5 分钟超时自动拒绝
  const timer = setTimeout(() => {
    resolve({ behavior: 'deny', message: 'Permission request timed out' });
  }, TIMEOUT_MS);
  
  map.set(id, { resolve, timer, toolInput, ... });
}

// 用户响应权限请求
export function resolvePendingPermission(
  id: string,
  result: PermissionResult
): boolean {
  // 双重写入：先持久化到数据库，再解决内存 Promise
  dbResolvePermission(id, dbStatus, {...});
  entry.resolve(result);
}
```

### 3.4 系统提示词管理

```typescript
// 预设追加模式 - 保留 Claude Code 默认系统提示词
queryOptions.systemPrompt = {
  type: 'append',
  data: systemPromptAppend
};
```

支持：
- 项目级提示词
- 会话级提示词
- 动态追加

## 4. 系统潜在问题与不足

### 4.1 会话恢复限制

- 依赖 Claude Code CLI 的会话文件
- CLI 版本不匹配会导致恢复失败
- 恢复失败需要完整重建上下文

### 4.2 并发限制

- 使用数据库锁防止并发，但单个会话同时只能处理一个请求
- 锁超时时间固定为 600 秒

### 4.3 权限系统限制

- 权限请求存储在内存中，服务器重启会丢失待处理请求
- 权限历史记录在数据库中，但无法设置"记住此决定"

### 4.4 SSE 可靠性

- 客户端断开连接时，后端可能继续处理
- 需要依赖 AbortSignal 终止处理

### 4.5 MCP 集成限制

- MCP 服务器配置需要手动管理
- 不支持 MCP 服务器动态发现

### 4.6 跨平台问题

- Windows 上 CLI 路径解析复杂
- 环境变量需要特殊处理
- 交叉编译需要 Wine

### 4.7 前端状态管理

- 使用 `globalThis` 模式在开发环境下保持状态
- HMR 可能导致状态不一致
- 需要手动清理状态

## 5. 改进建议

### 5.1 会话管理

- 实现会话快照功能，支持手动保存/恢复
- 增加会话标签和搜索功能

### 5.2 权限系统

- 支持"记住决定"功能
- 权限规则可配置化

### 5.3 性能优化

- 实现消息分页加载
- 优化大文件处理

### 5.4 可靠性

- 增加离线模式支持
- 实现消息队列重试机制
