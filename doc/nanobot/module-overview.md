# NanoBot 模块概览

## 模块架构图

```
nanobot/
├── agent/           # 核心智能体
├── bus/             # 消息总线
├── channels/        # 消息渠道
├── cli/             # 命令行接口
├── config/          # 配置管理
├── cron/            # 定时任务
├── heartbeat/       # 心跳服务
├── providers/       # LLM 提供商
├── session/         # 会话管理
├── skills/          # 内置技能
├── templates/       # 模板文件
└── utils/           # 工具函数
```

## 模块详解

---

### 1. agent/ - 核心智能体

**职责**：Agent 的核心逻辑，包括主循环、工具执行、上下文构建。

```
agent/
├── loop.py          # AgentLoop 主循环
├── context.py       # 上下文构建器
├── memory.py        # 记忆管理
├── skills.py        # Skill 加载器
├── subagent.py      # 子智能体管理
└── tools/           # 内置工具
    ├── filesystem.py
    ├── shell.py
    ├── web.py
    ├── message.py
    ├── spawn.py
    ├── cron.py
    └── mcp.py
```

**关键类**：

| 类 | 文件 | 功能 |
|----|------|------|
| `AgentLoop` | loop.py | 主循环，处理消息、调用 LLM、执行工具 |
| `ContextBuilder` | context.py | 构建系统提示和消息列表 |
| `MemoryStore` | memory.py | 双层记忆管理 |
| `SkillsLoader` | skills.py | 加载和管理 Skill |
| `ToolRegistry` | tools/registry.py | 工具注册和执行 |

---

### 2. bus/ - 消息总线

**职责**：异步消息传递，解耦渠道与核心逻辑。

```
bus/
├── queue.py         # MessageBus 消息队列
└── events.py        # 消息事件定义
```

**核心类**：

```python
class MessageBus:
    def __init__(self):
        self._inbound = asyncio.Queue()   # 入站消息
        self._outbound = asyncio.Queue()  # 出站消息
    
    async def publish_inbound(self, msg): ...
    async def consume_inbound(self): ...
    async def publish_outbound(self, msg): ...
    async def consume_outbound(self): ...
```

**消息类型**：

```python
@dataclass
class InboundMessage:
    channel: str       # telegram, whatsapp, discord...
    sender_id: str     # 发送者 ID
    chat_id: str       # 会话 ID
    content: str       # 消息内容
    media: list[str]   # 媒体文件路径

@dataclass
class OutboundMessage:
    channel: str
    chat_id: str
    content: str
    metadata: dict
```

---

### 3. channels/ - 消息渠道

**职责**：对接各种聊天平台，实现消息收发。

```
channels/
├── base.py           # BaseChannel 基类
├── manager.py        # ChannelManager 渠道管理器
├── telegram.py       # Telegram 渠道
├── whatsapp.py       # WhatsApp 渠道
├── discord.py        # Discord 渠道
├── feishu.py         # 飞书渠道
├── mochat.py         # Mochat 渠道
├── dingtalk.py       # 钉钉渠道
├── email.py          # 邮件渠道
├── slack.py          # Slack 渠道
└── qq.py             # QQ 渠道
```

**支持渠道**（9 种）：

| 渠道 | 协议/库 | 特点 |
|------|---------|------|
| Telegram | python-telegram-bot | 官方 API |
| WhatsApp | baileys (via bridge) | 非官方 |
| Discord | discord.py | 官方 API |
| Feishu | 飞书开放平台 | 企业 IM |
| Mochat | 自定义协议 | 企业 IM |
| DingTalk | 钉钉开放平台 | 企业 IM |
| Email | IMAP/SMTP | 传统邮件 |
| Slack | slack-sdk | 企业协作 |
| QQ | nonebot2 | 机器人框架 |

**ChannelManager 工作流程**：

```python
class ChannelManager:
    async def start_all(self):
        # 1. 启动出站分发器
        self._dispatch_task = asyncio.create_task(self._dispatch_outbound())
        
        # 2. 启动所有渠道
        for name, channel in self.channels.items():
            await channel.start()  # 开始监听入站消息
    
    async def _dispatch_outbound(self):
        """将出站消息路由到正确的渠道"""
        while True:
            msg = await self.bus.consume_outbound()
            channel = self.channels.get(msg.channel)
            await channel.send(msg)
```

---

### 4. providers/ - LLM 提供商

**职责**：封装各种 LLM API，提供统一接口。

```
providers/
├── base.py           # LLMProvider 基类
├── openai.py         # OpenAI / Azure
├── anthropic.py      # Anthropic Claude
├── gemini.py         # Google Gemini
├── groq.py           # Groq
├── ollama.py         # Ollama 本地模型
├── openrouter.py     # OpenRouter
├── moonshot.py       # Moonshot Kimi
├── deepseek.py       # DeepSeek
├── zhipu.py          # 智谱 GLM
├── dashscope.py      # 阿里云千问
├── siliconflow.py    # SiliconFlow
├── stepfun.py        # StepFun
└── litellm.py        # LiteLLM 统一网关
```

**Provider 接口**：

```python
class LLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        **kwargs
    ) -> LLMResponse:
        """调用 LLM API"""
    
    @abstractmethod
    def get_default_model(self) -> str:
        """获取默认模型"""
```

**支持的 Provider**（16+ 种）：

| Provider | 特点 |
|----------|------|
| OpenAI | GPT-4, GPT-3.5 |
| Anthropic | Claude 系列 |
| Gemini | Google 最新模型 |
| Groq | 极快推理速度 |
| Ollama | 本地部署 |
| OpenRouter | 多模型网关 |
| Moonshot | 长上下文 (Kimi) |
| DeepSeek | DeepSeek-R1 推理模型 |
| 智谱 | GLM 系列 |
| 千问 | 阿里云 Qwen |
| SiliconFlow | 国内模型托管 |
| StepFun | 阶跃星辰 |

---

### 5. session/ - 会话管理

**职责**：管理对话历史，持久化会话状态。

```
session/
└── manager.py        # Session + SessionManager
```

**Session 数据结构**：

```python
@dataclass
class Session:
    key: str                    # channel:chat_id
    messages: list[dict]        # 消息列表
    created_at: datetime
    updated_at: datetime
    metadata: dict
    last_consolidated: int      # 已整合到记忆的消息数
```

**存储格式**：JSONL（每行一条消息）

```
sessions/telegram_123456.jsonl
├── {"_type": "metadata", "key": "telegram:123456", ...}
├── {"role": "user", "content": "Hello", "timestamp": "..."}
├── {"role": "assistant", "content": "Hi!", "timestamp": "..."}
└── ...
```

---

### 6. config/ - 配置管理

**职责**：解析配置文件，验证配置项。

```
config/
├── schema.py         # 配置 Schema (Pydantic)
└── loader.py         # 配置加载器
```

**配置结构**：

```python
class Config(BaseModel):
    providers: ProvidersConfig      # LLM 提供商配置
    channels: ChannelsConfig        # 消息渠道配置
    agent: AgentConfig              # Agent 配置
    exec: ExecToolConfig            # 命令执行配置
    mcp: MCPConfig                  # MCP 服务器配置
```

---

### 7. cron/ - 定时任务

**职责**：管理和执行定时任务。

```
cron/
├── service.py        # CronService
└── scheduler.py      # 任务调度器
```

**功能**：
- 支持 cron 表达式
- 任务持久化
- 任务状态管理（运行/暂停/取消）

---

### 8. heartbeat/ - 心跳服务

**职责**：监控 Agent 运行状态，提供健康检查。

```
heartbeat/
└── service.py        # HeartbeatService
```

**HTTP 端点**：

```
GET /health           # 健康检查
GET /status           # 详细状态
```

---

### 9. skills/ - 内置技能

**职责**：提供预定义的 Skill。

```
skills/
├── github/           # GitHub CLI 操作
├── weather/          # 天气查询
├── summarize/        # 内容摘要
├── tmux/             # tmux 会话管理
├── clawhub/          # Skill 注册表
├── skill-creator/    # 创建新 Skill
├── cron/             # 定时任务 Skill
├── memory/           # 记忆管理 Skill
└── README.md
```

---

### 10. cli/ - 命令行接口

**职责**：提供命令行入口。

```
cli/
└── main.py           # CLI 入口
```

**命令**：

```bash
nanobot                    # 启动 Agent
nanobot --config my.yaml   # 指定配置文件
nanobot --help             # 帮助信息
```

---

### 11. utils/ - 工具函数

```
utils/
└── helpers.py        # 通用工具函数
```

**函数**：
- `ensure_dir()` - 确保目录存在
- `safe_filename()` - 安全文件名转换

---

## 模块依赖关系

```
CLI (cli/)
    │
    ▼
ChannelManager (channels/)
    │
    ▼
MessageBus (bus/) ←─────────────┐
    │                           │
    ▼                           │
AgentLoop (agent/)              │
    │                           │
    ├── ContextBuilder ─────────┤
    │       │                   │
    │       ├── MemoryStore     │
    │       └── SkillsLoader    │
    │                           │
    ├── SessionManager ─────────┘
    │
    ├── ToolRegistry
    │       │
    │       └── Tools (shell, filesystem, web...)
    │
    └── LLMProvider (providers/)
```

## 与其他项目对比

| 模块 | NanoBot | NanoClaw | TinyClaw |
|------|---------|----------|----------|
| 核心循环 | 自实现 | SDK | SDK |
| 消息渠道 | 9 种 | WhatsApp | 4 种 |
| LLM Provider | 16+ 种 | SDK 内置 | SDK 内置 |
| 会话存储 | JSONL | SDK | JSONL |
| 技能系统 | Markdown | Markdown | Markdown |
| MCP 支持 | Stdio + HTTP | SDK 内置 | ❌ |
