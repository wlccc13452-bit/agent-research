# NanoClaw Container 对话迭代机制分析

## 核心架构

NanoClaw 的对话迭代由 **Claude Agent SDK** 驱动，运行在 Docker 容器中。

```
WhatsApp → SQLite → Polling Loop → Container (Agent SDK) → Response
```

## 迭代流程详解

### 1. 消息接收（宿主机）

```typescript
// nanoclaw/src/main.ts

// WhatsApp 消息监听
sock.ev.on('messages.upsert', async ({ messages }) => {
    for (const msg of messages) {
        if (shouldProcess(msg)) {
            // 存入 SQLite
            await db.run(`
                INSERT INTO messages (jid, content, timestamp)
                VALUES (?, ?, ?)
            `, [jid, content, Date.now()]);
        }
    }
});
```

### 2. 轮询循环（宿主机）

```typescript
// nanoclaw/src/polling-loop.ts

async function startPollingLoop() {
    while (true) {
        // 查询未处理消息
        const messages = await db.all(`
            SELECT * FROM messages 
            WHERE processed = 0 
            ORDER BY timestamp ASC
        `);
        
        for (const msg of messages) {
            // 调用容器
            const result = await runContainer(msg);
            
            // 标记已处理
            await db.run(`UPDATE messages SET processed = 1 WHERE id = ?`, [msg.id]);
            
            // 发送响应
            await sendWhatsAppResponse(result);
        }
        
        await sleep(1000);  // 1秒轮询间隔
    }
}
```

### 3. 容器执行（核心迭代）

```typescript
// container/agent-runner/src/index.ts

async function main() {
    const input: ContainerInput = JSON.parse(await readStdin());
    
    // 创建 IPC MCP Server
    const ipcMcp = createIpcMcp({
        chatJid: input.chatJid,
        groupFolder: input.groupFolder,
        isMain: input.isMain
    });
    
    let result: string | null = null;
    
    // Agent SDK 查询循环
    for await (const message of query({
        prompt: input.prompt,
        options: {
            cwd: '/workspace/group',
            resume: input.sessionId,  // 恢复会话
            allowedTools: [
                'Bash',
                'Read', 'Write', 'Edit', 'Glob', 'Grep',
                'WebSearch', 'WebFetch',
                'mcp__nanoclaw__*'
            ],
            permissionMode: 'bypassPermissions',
            mcpServers: {
                nanoclaw: ipcMcp
            },
            hooks: {
                PreCompact: [{ hooks: [createPreCompactHook()] }]
            }
        }
    })) {
        // 处理不同消息类型
        if (message.type === 'system' && message.subtype === 'init') {
            // 保存会话 ID
            newSessionId = message.session_id;
        }
        
        if ('result' in message) {
            result = message.result;
        }
    }
    
    // 输出结果
    writeOutput({
        status: 'success',
        result,
        newSessionId
    });
}
```

## 对话迭代案例

### 场景：定时任务 + 消息通知

```
用户: "每天早上 9 点提醒我查看天气"
```

### 迭代过程

#### 迭代 1：理解请求并创建任务

```
LLM 思考:
用户想要定时任务，我需要调用 schedule_task MCP 工具。

工具调用:
mcp__nanoclaw__schedule_task({
    prompt: "查看天气并发送提醒",
    schedule_type: "cron",
    schedule_value: "0 9 * * *",
    context_mode: "group"
})

IPC 文件写入:
/workspace/ipc/tasks/1738123456-abc123.json
{
    "type": "schedule_task",
    "prompt": "查看天气并发送提醒",
    "schedule_type": "cron",
    "schedule_value": "0 9 * * *",
    "context_mode": "group",
    "groupFolder": "family-chat",
    "chatJid": "120363336345536173@g.us"
}

宿主机读取:
- 解析 cron 表达式
- 创建定时任务
- 返回确认
```

#### 迭代 2：任务执行（第二天 9:00）

```
定时触发:
- 宿主机检测到任务到期
- 启动容器执行任务

容器内 Agent:
prompt = "[SCHEDULED TASK - You are running automatically...]
         查看天气并发送提醒"

工具调用:
WebSearch("今天广州天气")

LLM 响应:
"今天广州天气：晴，气温 18-25°C..."

工具调用:
mcp__nanoclaw__send_message({
    text: "早安！今天广州天气：晴，气温 18-25°C，适合外出。"
})

WhatsApp 发送:
宿主机读取 IPC 文件，发送消息到群组
```

## 会话持久化

### SDK 内置会话

```typescript
// 会话 ID 由 SDK 管理
for await (const message of query({
    options: {
        resume: input.sessionId,  // 恢复已有会话
    }
})) {
    if (message.type === 'system' && message.subtype === 'init') {
        newSessionId = message.session_id;
    }
}
```

### 会话压缩 (Compaction)

```typescript
// 压缩前的钩子
function createPreCompactHook(): HookCallback {
    return async (input) => {
        const transcriptPath = input.transcript_path;
        
        // 归档完整对话到 conversations/ 目录
        const content = fs.readFileSync(transcriptPath, 'utf-8');
        const messages = parseTranscript(content);
        
        const filePath = path.join('/workspace/group/conversations', 
            `${date}-${summary}.md`);
        fs.writeFileSync(filePath, formatTranscriptMarkdown(messages));
        
        return {};
    };
}
```

### 对话归档格式

```markdown
# Daily Weather Reminder

Archived: Feb 26, 2026, 9:00 AM

---

**User**: 每天早上 9 点提醒我查看天气

**Andy**: 我已经为您创建了每天早上 9 点的定时任务...

**User**: 太好了，谢谢！

**Andy**: 不客气！任务会在每天早上 9 点自动执行...
```

## IPC 通信机制

### 消息队列

```
/workspace/ipc/
├── messages/           # 出站消息队列
│   ├── 1738123456-abc123.json
│   └── 1738123457-def456.json
└── tasks/              # 任务控制队列
    ├── schedule_task_xxx.json
    └── pause_task_xxx.json
```

### 原子写入

```typescript
function writeIpcFile(dir: string, data: object): string {
    const filename = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}.json`;
    const filepath = path.join(dir, filename);
    
    // 原子写入：先写临时文件，再重命名
    const tempPath = `${filepath}.tmp`;
    fs.writeFileSync(tempPath, JSON.stringify(data, null, 2));
    fs.renameSync(tempPath, filepath);
    
    return filename;
}
```

## 与 NanoBot 对比

| 维度 | NanoClaw | NanoBot |
|------|----------|---------|
| 迭代引擎 | Claude Agent SDK | 自实现 AgentLoop |
| 会话管理 | SDK 内置 | SessionManager + JSONL |
| 工具调用 | MCP Server | ToolRegistry |
| 消息通信 | IPC 文件 | asyncio.Queue |
| 记忆压缩 | SDK compaction | LLM 整合 |
| 容器隔离 | Docker | 无 |
| 最大迭代 | SDK 配置 | 40 次 |

## 容器输入输出

### 输入格式

```json
{
    "prompt": "帮我创建一个 Python 项目",
    "sessionId": "abc123",
    "groupFolder": "family-chat",
    "chatJid": "120363336345536173@g.us",
    "isMain": true,
    "isScheduledTask": false
}
```

### 输出格式

```json
{
    "status": "success",
    "result": "我已经创建了项目...",
    "newSessionId": "def456"
}
```

### 输出标记

```
---NANOCLAW_OUTPUT_START---
{"status":"success","result":"...","newSessionId":"..."}
---NANOCLAW_OUTPUT_END---
```

这样设计是为了从容器日志中精确提取 JSON 输出。

## 错误处理

```typescript
try {
    for await (const message of query({...})) {
        // 处理消息
    }
} catch (err) {
    writeOutput({
        status: 'error',
        result: null,
        error: err.message
    });
    process.exit(1);
}
```

## 定时任务上下文

```typescript
let prompt = input.prompt;
if (input.isScheduledTask) {
    prompt = `[SCHEDULED TASK - You are running automatically, not in response to a user message. Use mcp__nanoclaw__send_message if needed to communicate with the user.]\n\n${input.prompt}`;
}
```

这样 Agent 知道这是自动任务，可以通过 `send_message` 主动发送消息。
