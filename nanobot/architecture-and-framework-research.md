# NanoBot 架构与框架研究

## 项目概述

**NanoBot** 是一个**超轻量级**个人 AI 助手，由香港大学数据科学研究院 (HKUDS) 开发。

| 维度 | 数据 |
|------|------|
| **核心代码行数** | ~4,000 行 (99% 小于 Clawdbot 的 430k+ 行) |
| **语言** | Python ≥3.11 |
| **消息渠道** | 9 种 (Telegram, Discord, WhatsApp, Feishu, Slack, Email, QQ, DingTalk, Mochat) |
| **LLM Provider** | 16+ 种 (OpenRouter, Anthropic, OpenAI, DeepSeek, Gemini 等) |
| **特性** | MCP 支持、定时任务、记忆系统、多模态 |

---

## 核心架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              NanoBot                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                        Chat Channels (9)                           │ │
│  │  Telegram │ Discord │ WhatsApp │ Feishu │ Slack │ Email │ QQ ...  │ │
│  └─────────────────────────────┬──────────────────────────────────────┘ │
│                                │                                         │
│                                ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     Message Bus (bus/queue.py)                     │ │
│  │              Inbound Queue ←──────→ Outbound Queue                 │ │
│  └─────────────────────────────┬──────────────────────────────────────┘ │
│                                │                                         │
│                                ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                   Agent Loop (agent/loop.py)                       │ │
│  │    _run_agent_loop() → provider.chat() → tool.execute()           │ │
│  └─────────────────────────────┬──────────────────────────────────────┘ │
│                                │                                         │
│                                ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                  Context Builder (agent/context.py)                │ │
│  │     build_system_prompt() + build_messages()                       │ │
│  └─────────────────────────────┬──────────────────────────────────────┘ │
│                                │                                         │
│          ┌─────────────────────┼─────────────────────┐                  │
│          ▼                     ▼                     ▼                  │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐             │
│  │   Session   │      │   Memory    │      │   Skills    │             │
│  │  (JSONL)    │      │ (MD Files)  │      │  (SKILL.md) │             │
│  └─────────────┘      └─────────────┘      └─────────────┘             │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      Tools (agent/tools/)                          │ │
│  │  exec │ read_file │ write_file │ web_search │ message │ spawn ... │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │               Providers (providers/) + MCP Servers                 │ │
│  │        LiteLLM → Anthropic/OpenAI/DeepSeek/Gemini/...             │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 子系统详解

### 1. Agent Loop (核心引擎)

**文件**: `nanobot/agent/loop.py`

核心处理引擎，负责消息处理和工具调用：

```python
class AgentLoop:
    """The agent loop is the core processing engine.
    
    It:
    1. Receives messages from the bus
    2. Builds context with history, memory, skills
    3. Calls the LLM
    4. Executes tool calls
    5. Sends responses back
    """
    
    def __init__(
        self,
        bus: MessageBus,
        provider: LLMProvider,
        workspace: Path,
        max_iterations: int = 40,  # 最大迭代次数
        memory_window: int = 100,   # 记忆窗口
        ...
    ):
        self.context = ContextBuilder(workspace)
        self.sessions = SessionManager(workspace)
        self.tools = ToolRegistry()
        self.subagents = SubagentManager(...)
```

**核心循环**:

```python
async def _run_agent_loop(
    self,
    initial_messages: list[dict],
    on_progress: Callable[..., Awaitable[None]] | None = None,
) -> tuple[str | None, list[str], list[dict]]:
    """Run the agent iteration loop."""
    messages = initial_messages
    iteration = 0
    final_content = None
    tools_used: list[str] = []

    while iteration < self.max_iterations:
        iteration += 1
        
        # 1. 调用 LLM
        response = await self.provider.chat(
            messages=messages,
            tools=self.tools.get_definitions(),
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        # 2. 处理工具调用
        if response.has_tool_calls:
            # 添加 assistant 消息
            messages = self.context.add_assistant_message(
                messages, response.content, tool_call_dicts,
                reasoning_content=response.reasoning_content,
            )
            
            # 执行每个工具
            for tool_call in response.tool_calls:
                result = await self.tools.execute(tool_call.name, tool_call.arguments)
                messages = self.context.add_tool_result(messages, tool_call.id, tool_call.name, result)
        else:
            final_content = self._strip_think(response.content)
            break

    return final_content, tools_used, messages
```

### 2. Context Builder (上下文构建器)

**文件**: `nanobot/agent/context.py`

构建系统提示和消息列表：

```python
class ContextBuilder:
    BOOTSTRAP_FILES = ["AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md", "IDENTITY.md"]
    
    def build_system_prompt(self, skill_names: list[str] | None = None) -> str:
        parts = []
        
        # 1. 核心身份
        parts.append(self._get_identity())
        
        # 2. Bootstrap 文件
        bootstrap = self._load_bootstrap_files()
        if bootstrap:
            parts.append(bootstrap)
        
        # 3. 记忆上下文
        memory = self.memory.get_memory_context()
        if memory:
            parts.append(f"# Memory\n\n{memory}")
        
        # 4. 技能 (渐进式加载)
        always_skills = self.skills.get_always_skills()
        if always_skills:
            parts.append(f"# Active Skills\n\n{always_content}")
        
        return "\n\n---\n\n".join(parts)
    
    def build_messages(
        self,
        history: list[dict],
        current_message: str,
        media: list[str] | None = None,
        channel: str | None = None,
        chat_id: str | None = None,
    ) -> list[dict]:
        messages = []
        
        # 1. 系统提示
        messages.append({"role": "system", "content": self.build_system_prompt()})
        
        # 2. 历史消息
        messages.extend(history)
        
        # 3. 当前消息 (含运行时上下文)
        user_content = self._build_user_content(current_message, media)
        user_content = self._inject_runtime_context(user_content, channel, chat_id)
        messages.append({"role": "user", "content": user_content})
        
        return messages
```

### 3. Memory System (记忆系统)

**文件**: `nanobot/agent/memory.py`

双层记忆架构：

```
memory/
├── MEMORY.md     # 长期记忆 (事实、偏好)
└── HISTORY.md    # 历史日志 (可 grep 搜索)
```

**记忆压缩流程**:

```python
class MemoryStore:
    async def consolidate(
        self,
        session: Session,
        provider: LLMProvider,
        model: str,
        *,
        archive_all: bool = False,
        memory_window: int = 50,
    ) -> bool:
        """通过 LLM 工具调用压缩记忆"""
        
        # 1. 准备待压缩消息
        old_messages = session.messages[session.last_consolidated:-keep_count]
        
        # 2. 调用 LLM 执行压缩
        response = await provider.chat(
            messages=[...],
            tools=_SAVE_MEMORY_TOOL,  # save_memory 工具定义
            model=model,
        )
        
        # 3. 提取压缩结果
        args = response.tool_calls[0].arguments
        
        # 4. 写入文件
        if entry := args.get("history_entry"):
            self.append_history(entry)
        if update := args.get("memory_update"):
            self.write_long_term(update)
        
        # 5. 更新会话状态
        session.last_consolidated = len(session.messages) - keep_count
```

**save_memory 工具定义**:

```python
_SAVE_MEMORY_TOOL = [{
    "type": "function",
    "function": {
        "name": "save_memory",
        "description": "Save the memory consolidation result to persistent storage.",
        "parameters": {
            "type": "object",
            "properties": {
                "history_entry": {
                    "type": "string",
                    "description": "A paragraph (2-5 sentences) summarizing key events..."
                },
                "memory_update": {
                    "type": "string",
                    "description": "Full updated long-term memory as markdown..."
                },
            },
            "required": ["history_entry", "memory_update"],
        },
    },
}]
```

### 4. Session Manager (会话管理)

**文件**: `nanobot/session/manager.py`

JSONL 格式持久化：

```python
@dataclass
class Session:
    key: str  # channel:chat_id
    messages: list[dict] = field(default_factory=list)
    last_consolidated: int = 0  # 已压缩的消息数
    
    def get_history(self, max_messages: int = 500) -> list[dict]:
        """返回未压缩的消息"""
        unconsolidated = self.messages[self.last_consolidated:]
        sliced = unconsolidated[-max_messages:]
        return sliced


class SessionManager:
    def save(self, session: Session) -> None:
        """保存到 JSONL 文件"""
        with open(path, "w") as f:
            # 元数据行
            f.write(json.dumps({
                "_type": "metadata",
                "key": session.key,
                "last_consolidated": session.last_consolidated,
                ...
            }) + "\n")
            # 消息行
            for msg in session.messages:
                f.write(json.dumps(msg) + "\n")
```

### 5. Message Bus (消息总线)

**文件**: `nanobot/bus/queue.py`

异步解耦消息传递：

```python
class MessageBus:
    """Async message bus that decouples chat channels from the agent core."""
    
    def __init__(self):
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()
    
    async def publish_inbound(self, msg: InboundMessage) -> None:
        """发布消息到 Agent"""
        await self.inbound.put(msg)
    
    async def consume_inbound(self) -> InboundMessage:
        """消费消息 (阻塞)"""
        return await self.inbound.get()
```

### 6. Tools System (工具系统)

**目录**: `nanobot/agent/tools/`

| 文件 | 工具 | 功能 |
|------|------|------|
| `shell.py` | `exec` | Shell 命令执行 |
| `filesystem.py` | `read_file`, `write_file`, `edit_file`, `list_dir` | 文件操作 |
| `web.py` | `web_search`, `web_fetch` | Web 搜索和获取 |
| `message.py` | `message` | 发送消息到频道 |
| `spawn.py` | `spawn` | 创建子 Agent |
| `cron.py` | `cron` | 定时任务管理 |
| `mcp.py` | MCP 连接 | 外部 MCP 服务器 |

**工具基类**:

```python
class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def description(self) -> str: ...
    
    @property
    @abstractmethod
    def parameters(self) -> dict: ...
    
    @abstractmethod
    async def execute(self, **kwargs: Any) -> str: ...
```

---

## 数据流

### 消息处理流程

```
用户消息 (Telegram)
    │
    ▼
┌──────────────────┐
│ Telegram Channel │
│   (Adapter)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Message Bus     │
│  (Inbound Queue) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Agent Loop     │
│  (consume msg)   │
└────────┬─────────┘
         │
         ├─→ ContextBuilder.build_messages()
         │       │
         │       ├─→ Session.get_history()
         │       ├─→ MemoryStore.get_memory_context()
         │       └─→ SkillsLoader.load_skills()
         │
         ▼
┌──────────────────┐
│   LLM Provider   │
│   (LiteLLM)      │
└────────┬─────────┘
         │
         ├─→ Tool Execution Loop
         │       │
         │       ├─→ exec command
         │       ├─→ read/write file
         │       └─→ web_search
         │
         ▼
┌──────────────────┐
│  Message Bus     │
│ (Outbound Queue) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Telegram Channel │
│   (send reply)   │
└──────────────────┘
```

---

## Provider 系统

### Provider 注册表

```python
# nanobot/providers/registry.py
PROVIDERS = [
    ProviderSpec(
        name="openrouter",
        keywords=("openrouter",),
        env_key="OPENROUTER_API_KEY",
        litellm_prefix="openrouter",
        is_gateway=True,
        detect_by_key_prefix="sk-or-",
    ),
    ProviderSpec(
        name="anthropic",
        keywords=("anthropic", "claude"),
        env_key="ANTHROPIC_API_KEY",
        litellm_prefix="anthropic",
    ),
    # ... 16+ providers
]
```

### 模型自动匹配

```python
# 用户配置 model: "claude-opus-4-5"
# 系统自动:
# 1. 检测到 "claude" 关键词
# 2. 匹配到 anthropic provider
# 3. 自动添加前缀: "anthropic/claude-opus-4-5"
# 4. 设置 ANTHROPIC_API_KEY 环境变量
# 5. 调用 LiteLLM
```

---

## MCP 集成

### 配置格式

```json
{
  "tools": {
    "mcpServers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
      },
      "remote": {
        "url": "https://example.com/mcp/",
        "headers": { "Authorization": "Bearer xxx" }
      }
    }
  }
}
```

### 连接流程

```python
async def _connect_mcp(self) -> None:
    """Connect to configured MCP servers."""
    self._mcp_stack = AsyncExitStack()
    await self._mcp_stack.__aenter__()
    await connect_mcp_servers(self._mcp_servers, self.tools, self._mcp_stack)
    self._mcp_connected = True
```

---

## 项目结构

```
nanobot/
├── agent/          # 🧠 核心代理逻辑
│   ├── loop.py     #    Agent 循环 (LLM ↔ 工具执行)
│   ├── context.py  #    提示构建器
│   ├── memory.py   #    持久化记忆
│   ├── skills.py   #    技能加载器
│   ├── subagent.py #    后台任务执行
│   └── tools/      #    内置工具 (spawn, exec, web...)
├── skills/         # 🎯 打包技能 (github, weather, tmux...)
├── channels/       # 📱 聊天渠道集成
├── bus/            # 🚌 消息路由
├── cron/           # ⏰ 定时任务
├── heartbeat/      # 💓 主动唤醒
├── providers/      # 🤖 LLM 提供者
├── session/        # 💬 会话管理
├── config/         # ⚙️ 配置
└── cli/            # 🖥️ 命令行
```

---

## 与其他项目对比

| 维度 | NanoBot | NanoClaw | TinyClaw |
|------|---------|----------|----------|
| **语言** | Python | TypeScript | TypeScript |
| **代码规模** | ~4,000 行 | ~2,000 行 | ~11,000 行 |
| **消息渠道** | 9 种 | WhatsApp | 4 种 |
| **LLM Provider** | 16+ | Anthropic | 4+ |
| **MCP 支持** | ✅ Stdio + HTTP | ✅ SDK 内置 | ❌ |
| **记忆系统** | 双层 MD 文件 | 容器隔离 | JSONL + SQLite |
| **会话持久化** | JSONL | SQLite | JSONL |
| **验证机制** | ❌ | ❌ | ❌ |

---

## 总结

### NanoBot 特点

1. **超轻量**: 4,000 行核心代码，易于理解和修改
2. **多渠道**: 9 种消息平台完整实现
3. **多 Provider**: 16+ LLM 提供者，LiteLLM 统一接口
4. **MCP 支持**: Stdio + HTTP 双模式
5. **渐进式技能加载**: 按需加载，减少上下文占用

### 设计亮点

- **双层记忆**: MEMORY.md (事实) + HISTORY.md (日志)
- **消息追加模式**: 保持 LLM 缓存效率
- **Provider 注册表**: 2 步添加新 Provider
- **异步消息总线**: 解耦渠道与核心
