# NanoBot 思维模式与 LLM 交互分析

## 概述

NanoBot 使用 **LiteLLM** 作为统一 LLM 接口，支持 16+ 种 Provider。本文分析其思维模式和 LLM 交互设计。

---

## LLM 交互架构

### 1. Provider 抽象层

```python
# nanobot/providers/base.py
class LLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> LLMResponse: ...

# nanobot/providers/litellm_provider.py
class LiteLLMProvider(LLMProvider):
    async def chat(self, messages, tools, model, temperature, max_tokens):
        # 统一调用 LiteLLM
        response = await acompletion(
            model=model,  # 自动添加前缀: "anthropic/claude-..."
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return self._parse_response(response)
```

### 2. 响应解析

```python
@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall]
    has_tool_calls: bool
    reasoning_content: str | None  # 思维链输出 (DeepSeek-R1, Kimi 等)

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]
```

---

## 思维链处理

### 1. 思维块提取

```python
# nanobot/agent/loop.py
@staticmethod
def _strip_think(text: str | None) -> str | None:
    """Remove <think>…</think> blocks that some models embed in content."""
    if not text:
        return None
    return re.sub(r", "", text).strip() or None
```

### 2. 推理内容保留

```python
def add_assistant_message(
    self,
    messages: list[dict],
    content: str | None,
    tool_calls: list[dict] | None = None,
    reasoning_content: str | None = None,  # ← 思维链内容
) -> list[dict]:
    msg = {"role": "assistant", "content": content}
    
    if tool_calls:
        msg["tool_calls"] = tool_calls
    
    # 保留思维链 (DeepSeek-R1, Kimi 等需要)
    if reasoning_content is not None:
        msg["reasoning_content"] = reasoning_content
    
    messages.append(msg)
    return messages
```

### 3. 支持的思维链模式

| 模式 | Provider | 处理方式 |
|------|----------|---------|
| `<think>...</think>` | 多种模型 | 正则提取并移除 |
| `reasoning_content` 字段 | DeepSeek-R1, Kimi | 作为消息属性保留 |
| 流式思维 | 部分模型 | 通过 SSE 事件传递 |

---

## 迭代控制

### 最大迭代次数

```python
class AgentLoop:
    def __init__(self, ..., max_iterations: int = 40):
        self.max_iterations = max_iterations
    
    async def _run_agent_loop(self, initial_messages, on_progress):
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            response = await self.provider.chat(...)
            
            if response.has_tool_calls:
                # 执行工具，继续循环
                for tool_call in response.tool_calls:
                    result = await self.tools.execute(tool_call.name, tool_call.arguments)
                    messages = self.context.add_tool_result(...)
            else:
                # 无工具调用，结束循环
                break
        
        if iteration >= self.max_iterations:
            logger.warning("Max iterations ({}) reached", self.max_iterations)
            final_content = "I reached the maximum number of tool call iterations..."
```

### 进度反馈

```python
async def _run_agent_loop(self, initial_messages, on_progress):
    while iteration < self.max_iterations:
        response = await self.provider.chat(...)
        
        if response.has_tool_calls:
            if on_progress:
                # 1. 发送思维内容 (如果有)
                clean = self._strip_think(response.content)
                if clean:
                    await on_progress(clean)
                
                # 2. 发送工具提示
                await on_progress(
                    self._tool_hint(response.tool_calls), 
                    tool_hint=True
                )

@staticmethod
def _tool_hint(tool_calls: list) -> str:
    """Format tool calls as concise hint, e.g. 'web_search("query")'."""
    def _fmt(tc):
        val = next(iter(tc.arguments.values()), None)
        if not isinstance(val, str):
            return tc.name
        return f'{tc.name}("{val[:40]}…")' if len(val) > 40 else f'{tc.name}("{val}")'
    return ", ".join(_fmt(tc) for tc in tool_calls)
```

---

## 上下文管理

### 1. 运行时上下文注入

```python
@staticmethod
def _inject_runtime_context(
    user_content: str | list[dict],
    channel: str | None,
    chat_id: str | None,
) -> str | list[dict]:
    """Append dynamic runtime context to the tail of the user message."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M (%A)")
    tz = time.strftime("%Z") or "UTC"
    lines = [f"Current Time: {now} ({tz})"]
    if channel and chat_id:
        lines += [f"Channel: {channel}", f"Chat ID: {chat_id}"]
    block = "[Runtime Context]\n" + "\n".join(lines)
    
    if isinstance(user_content, str):
        return f"{user_content}\n\n{block}"
    return [*user_content, {"type": "text", "text": block}]
```

### 2. 系统提示构建

```python
def build_system_prompt(self, skill_names: list[str] | None = None) -> str:
    parts = []
    
    # 1. 核心身份
    parts.append(self._get_identity())  # 包含 runtime, workspace, memory 路径
    
    # 2. Bootstrap 文件 (AGENTS.md, SOUL.md, USER.md...)
    parts.append(self._load_bootstrap_files())
    
    # 3. 长期记忆
    memory = self.memory.get_memory_context()
    if memory:
        parts.append(f"# Memory\n\n{memory}")
    
    # 4. 技能 (渐进式)
    # - always_skills: 完整内容
    # - available_skills: 仅摘要 (Agent 用 read_file 加载)
    
    return "\n\n---\n\n".join(parts)
```

### 3. 多模态支持

```python
def _build_user_content(self, text: str, media: list[str] | None) -> str | list[dict]:
    """Build user message content with optional base64-encoded images."""
    if not media:
        return text
    
    images = []
    for path in media:
        p = Path(path)
        mime, _ = mimetypes.guess_type(path)
        if p.is_file() and mime and mime.startswith("image/"):
            b64 = base64.b64encode(p.read_bytes()).decode()
            images.append({
                "type": "image_url", 
                "image_url": {"url": f"data:{mime};base64,{b64}"}
            })
    
    return images + [{"type": "text", "text": text}]
```

---

## 记忆压缩机制

### 触发条件

```python
async def _process_message(self, msg: InboundMessage, ...):
    session = self.sessions.get_or_create(key)
    
    # 检查是否需要压缩
    unconsolidated = len(session.messages) - session.last_consolidated
    if (unconsolidated >= self.memory_window and session.key not in self._consolidating):
        # 异步执行压缩，不阻塞当前请求
        async def _consolidate_and_unlock():
            async with lock:
                await self._consolidate_memory(session)
        
        _task = asyncio.create_task(_consolidate_and_unlock())
        self._consolidation_tasks.add(_task)
```

### 压缩流程

```python
async def consolidate(self, session, provider, model, ...):
    # 1. 提取待压缩消息
    keep_count = memory_window // 2
    old_messages = session.messages[session.last_consolidated:-keep_count]
    
    # 2. 构建压缩提示
    lines = []
    for m in old_messages:
        tools = f" [tools: {', '.join(m['tools_used'])}]" if m.get("tools_used") else ""
        lines.append(f"[{m.get('timestamp', '?')[:16]}] {m['role'].upper()}{tools}: {m['content']}")
    
    prompt = f"""Process this conversation and call the save_memory tool.

## Current Long-term Memory
{current_memory or "(empty)"}

## Conversation to Process
{chr(10).join(lines)}"""
    
    # 3. LLM 调用 save_memory 工具
    response = await provider.chat(
        messages=[...],
        tools=_SAVE_MEMORY_TOOL,  # save_memory 工具定义
        model=model,
    )
    
    # 4. 写入文件
    args = response.tool_calls[0].arguments
    self.append_history(args["history_entry"])
    self.write_long_term(args["memory_update"])
    
    # 5. 更新会话状态
    session.last_consolidated = len(session.messages) - keep_count
```

---

## 斜杠命令

```python
async def _process_message(self, msg: InboundMessage, ...):
    cmd = msg.content.strip().lower()
    
    if cmd == "/new":
        # 压缩所有消息并清空会话
        await self._consolidate_memory(session, archive_all=True)
        session.clear()
        return OutboundMessage(..., content="New session started.")
    
    if cmd == "/help":
        return OutboundMessage(..., content="""🐈 nanobot commands:
/new — Start a new conversation
/help — Show available commands""")
```

---

## 子 Agent 系统

### Spawn 工具

```python
# nanobot/agent/tools/spawn.py
class SpawnTool(Tool):
    @property
    def name(self) -> str:
        return "spawn"
    
    @property
    def description(self) -> str:
        return "Spawn a background agent to work on a task independently."
    
    async def execute(self, prompt: str, **kwargs) -> str:
        # 创建后台 Agent
        result = await self.manager.spawn(prompt)
        return f"Spawned agent completed: {result}"
```

### SubagentManager

```python
# nanobot/agent/subagent.py
class SubagentManager:
    def __init__(
        self,
        provider: LLMProvider,
        workspace: Path,
        bus: MessageBus,
        ...
    ):
        self.provider = provider
        self.workspace = workspace
        self.bus = bus
    
    async def spawn(self, prompt: str) -> str:
        """创建并运行后台 Agent"""
        agent = AgentLoop(
            bus=self.bus,
            provider=self.provider,
            workspace=self.workspace,
            ...
        )
        
        result = await agent.process_direct(
            content=prompt,
            session_key=f"spawn:{uuid4()}",
            channel="system",
        )
        return result
```

---

## 潜在问题与不足

### 1. 无验证机制

**问题**: 没有工具调用验证或结果验证

```python
# 工具直接执行，无验证
result = await self.tools.execute(tool_call.name, tool_call.arguments)
# ❌ 没有检查 result 是否合理
```

### 2. 记忆压缩依赖 LLM

**问题**: 记忆压缩完全依赖 LLM 的 `save_memory` 工具调用

```python
if not response.has_tool_calls:
    logger.warning("Memory consolidation: LLM did not call save_memory, skipping")
    return False  # 压缩失败
```

**影响**: 如果 LLM 不调用工具，记忆无法压缩，可能导致上下文溢出

### 3. 无错误恢复机制

```python
except Exception as e:
    logger.error("Error processing message: {}", e)
    await self.bus.publish_outbound(OutboundMessage(
        channel=msg.channel,
        chat_id=msg.chat_id,
        content=f"Sorry, I encountered an error: {str(e)}"
    ))
    # ❌ 没有重试机制
```

### 4. 最大迭代硬编码

```python
def __init__(self, ..., max_iterations: int = 40):
    # ❌ 无法通过配置调整
```

### 5. 会话状态不一致风险

```python
# 压缩是异步的
_task = asyncio.create_task(_consolidate_and_unlock())

# 如果用户在压缩完成前发送新消息
# session.last_consolidated 可能还未更新
```

---

## 与其他项目对比

| 维度 | NanoBot | NanoClaw | TinyClaw |
|------|---------|----------|----------|
| **思维链处理** | ✅ 多模式 | ✅ SDK 内置 | ✅ SDK 内置 |
| **记忆系统** | 双层 MD + LLM 压缩 | 容器隔离 | SQLite + FTS |
| **错误重试** | ❌ | ❌ | ✅ 5 种分类 |
| **子 Agent** | ✅ spawn 工具 | ✅ | ✅ |
| **进度反馈** | ✅ 流式工具提示 | ✅ | ✅ |
| **验证机制** | ❌ | ❌ | ❌ |

---

## 总结

### 优点

1. **多 Provider 支持**: 16+ LLM，LiteLLM 统一接口
2. **思维链兼容**: 支持多种思维链格式
3. **双层记忆**: 事实 + 日志分离，grep 可搜索
4. **渐进式技能**: 按需加载，减少上下文占用
5. **进度反馈**: 实时工具调用提示

### 不足

1. **无验证机制**: 工具调用和结果缺乏验证
2. **压缩依赖 LLM**: 如果 LLM 不调用工具则压缩失败
3. **无错误恢复**: 异常后直接返回错误，不重试
4. **异步状态风险**: 压缩期间会话状态可能不一致
