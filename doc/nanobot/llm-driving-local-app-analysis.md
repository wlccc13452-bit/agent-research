# NanoBot LLM 驱动本地 APP 分析

## 概述

NanoBot 通过多种方式驱动本地应用：Shell 执行、文件操作、Web 访问、子 Agent 等。本文详细分析其实现机制。

---

## 核心驱动方式

### 1. Shell 执行 (Exec Tool)

**文件**: `nanobot/agent/tools/shell.py`

```python
class ExecTool(Tool):
    def __init__(
        self,
        timeout: int = 60,
        working_dir: str | None = None,
        deny_patterns: list[str] | None = None,
        allow_patterns: list[str] | None = None,
        restrict_to_workspace: bool = False,
    ):
        self.timeout = timeout
        self.deny_patterns = deny_patterns or [
            r"\brm\s+-[rf]{1,2}\b",          # rm -r, rm -rf
            r"\bdel\s+/[fq]\b",              # del /f, del /q
            r"\b(mkfs|diskpart)\b",          # 磁盘操作
            r"\bdd\s+if=",                   # dd
            r">\s*/dev/sd",                  # 写入磁盘
            r"\b(shutdown|reboot|poweroff)\b",  # 系统电源
            r":\(\)\s*\{.*\};\s*:",          # fork bomb
        ]
        self.restrict_to_workspace = restrict_to_workspace
    
    @property
    def name(self) -> str:
        return "exec"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command"},
                "working_dir": {"type": "string", "description": "Working directory"}
            },
            "required": ["command"]
        }
    
    async def execute(self, command: str, working_dir: str | None = None) -> str:
        cwd = working_dir or self.working_dir or os.getcwd()
        
        # 1. 安全检查
        guard_error = self._guard_command(command, cwd)
        if guard_error:
            return guard_error
        
        # 2. 异步执行
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        
        # 3. 超时控制
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            return f"Error: Command timed out after {self.timeout} seconds"
        
        # 4. 结果处理
        result = self._format_output(stdout, stderr, process.returncode)
        
        # 5. 输出截断
        if len(result) > 10000:
            result = result[:10000] + f"\n... (truncated, {len(result) - 10000} more chars)"
        
        return result
```

### 安全守卫

```python
def _guard_command(self, command: str, cwd: str) -> str | None:
    """Best-effort safety guard for potentially destructive commands."""
    
    # 1. 检查拒绝模式
    for pattern in self.deny_patterns:
        if re.search(pattern, command.lower()):
            return "Error: Command blocked by safety guard (dangerous pattern detected)"
    
    # 2. 检查允许列表 (如果配置)
    if self.allow_patterns:
        if not any(re.search(p, command.lower()) for p in self.allow_patterns):
            return "Error: Command blocked by safety guard (not in allowlist)"
    
    # 3. 工作区限制
    if self.restrict_to_workspace:
        # 路径遍历检测
        if "..\\" in command or "../" in command:
            return "Error: Command blocked by safety guard (path traversal detected)"
        
        # 绝对路径检测
        for path in self._extract_paths(command):
            if path.is_absolute() and cwd not in path.parents:
                return "Error: Command blocked by safety guard (path outside working dir)"
    
    return None
```

---

## 文件操作工具

### 文件系统工具集

**文件**: `nanobot/agent/tools/filesystem.py`

```python
class ReadFileTool(Tool):
    @property
    def name(self) -> str:
        return "read_file"
    
    async def execute(self, path: str, **kwargs) -> str:
        # 路径安全检查
        safe_path = self._validate_path(path)
        if isinstance(safe_path, str) and safe_path.startswith("Error:"):
            return safe_path
        
        # 读取文件
        content = safe_path.read_text(encoding="utf-8")
        
        # 截断大文件
        if len(content) > 50000:
            return content[:50000] + "\n... (truncated)"
        return content


class WriteFileTool(Tool):
    @property
    def name(self) -> str:
        return "write_file"
    
    async def execute(self, path: str, content: str, **kwargs) -> str:
        safe_path = self._validate_path(path)
        if isinstance(safe_path, str) and safe_path.startswith("Error:"):
            return safe_path
        
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} characters to {path}"


class EditFileTool(Tool):
    @property
    def name(self) -> str:
        return "edit_file"
    
    async def execute(
        self, 
        path: str, 
        old_text: str, 
        new_text: str, 
        **kwargs
    ) -> str:
        safe_path = self._validate_path(path)
        if isinstance(safe_path, str) and safe_path.startswith("Error:"):
            return safe_path
        
        content = safe_path.read_text(encoding="utf-8")
        
        # 检查唯一性
        if content.count(old_text) > 1:
            return f"Error: Found {content.count(old_text)} occurrences. Please provide more context."
        
        if old_text not in content:
            return "Error: Text not found in file"
        
        new_content = content.replace(old_text, new_text, 1)
        safe_path.write_text(new_content, encoding="utf-8")
        return f"Edited {path}"


class ListDirTool(Tool):
    @property
    def name(self) -> str:
        return "list_dir"
    
    async def execute(self, path: str, **kwargs) -> str:
        safe_path = self._validate_path(path)
        if isinstance(safe_path, str) and safe_path.startswith("Error:"):
            return safe_path
        
        entries = []
        for entry in safe_path.iterdir():
            prefix = "[DIR] " if entry.is_dir() else "[FILE] "
            entries.append(f"{prefix}{entry.name}")
        return "\n".join(sorted(entries))
```

### 路径验证

```python
def _validate_path(self, path: str) -> Path | str:
    """Validate and resolve path within allowed directory."""
    try:
        resolved = Path(path).resolve()
    except Exception:
        return f"Error: Invalid path: {path}"
    
    # 检查是否在允许目录内
    if self.allowed_dir:
        try:
            resolved.relative_to(self.allowed_dir)
        except ValueError:
            return f"Error: Path outside workspace: {path}"
    
    # 路径遍历检查
    if ".." in Path(path).parts:
        return f"Error: Path traversal detected: {path}"
    
    return resolved
```

---

## Web 工具

### WebSearchTool

```python
# nanobot/agent/tools/web.py
class WebSearchTool(Tool):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
    
    async def execute(self, query: str, **kwargs) -> str:
        if not self.api_key:
            return "Error: Brave API key not configured"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": self.api_key},
                params={"q": query, "count": 10}
            ) as response:
                data = await response.json()
        
        results = []
        for item in data.get("web", {}).get("results", []):
            results.append(f"- [{item['title']}]({item['url']})\n  {item['description']}")
        
        return "\n\n".join(results)
```

### WebFetchTool

```python
class WebFetchTool(Tool):
    @property
    def name(self) -> str:
        return "web_fetch"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"}
            },
            "required": ["url"]
        }
    
    async def execute(self, url: str, **kwargs) -> str:
        # 获取网页
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                html = await response.text()
        
        # 提取文本
        text = self._extract_text(html)
        
        # 截断
        if len(text) > 20000:
            text = text[:20000] + "\n... (truncated)"
        
        return text
```

---

## 消息发送工具

### MessageTool

```python
# nanobot/agent/tools/message.py
class MessageTool(Tool):
    def __init__(self, send_callback: Callable):
        self.send_callback = send_callback
        self._channel: str | None = None
        self._chat_id: str | None = None
        self._message_id: str | None = None
        self._sent_in_turn = False
    
    @property
    def name(self) -> str:
        return "message"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Message content"},
                "channel": {"type": "string", "description": "Target channel (optional)"},
                "chat_id": {"type": "string", "description": "Target chat ID (optional)"}
            },
            "required": ["content"]
        }
    
    def set_context(self, channel: str, chat_id: str, message_id: str | None = None):
        """Set routing context for the current turn."""
        self._channel = channel
        self._chat_id = chat_id
        self._message_id = message_id
    
    def start_turn(self):
        """Reset turn state."""
        self._sent_in_turn = False
    
    async def execute(
        self, 
        content: str, 
        channel: str | None = None, 
        chat_id: str | None = None,
        **kwargs
    ) -> str:
        target_channel = channel or self._channel
        target_chat_id = chat_id or self._chat_id
        
        if not target_channel or not target_chat_id:
            return "Error: No target channel/chat_id set"
        
        msg = OutboundMessage(
            channel=target_channel,
            chat_id=target_chat_id,
            content=content
        )
        
        await self.send_callback(msg)
        self._sent_in_turn = True
        
        return f"Message sent to {target_channel}:{target_chat_id}"
```

---

## 子 Agent 工具

### SpawnTool

```python
# nanobot/agent/tools/spawn.py
class SpawnTool(Tool):
    def __init__(self, manager: SubagentManager):
        self.manager = manager
        self._channel: str | None = None
        self._chat_id: str | None = None
    
    @property
    def name(self) -> str:
        return "spawn"
    
    @property
    def description(self) -> str:
        return """Spawn a background agent to work on a task independently.
        
Use this when you need to:
- Perform a long-running task without blocking the conversation
- Work on a parallel task while continuing the main conversation
- Isolate a task with its own session context"""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Task for the spawned agent"}
            },
            "required": ["prompt"]
        }
    
    def set_context(self, channel: str, chat_id: str):
        self._channel = channel
        self._chat_id = chat_id
    
    async def execute(self, prompt: str, **kwargs) -> str:
        result = await self.manager.spawn(
            prompt=prompt,
            reply_channel=self._channel,
            reply_chat_id=self._chat_id
        )
        return result
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
    
    async def spawn(
        self,
        prompt: str,
        reply_channel: str | None = None,
        reply_chat_id: str | None = None
    ) -> str:
        """创建并运行子 Agent"""
        
        # 创建独立会话
        session_key = f"spawn:{uuid4().hex[:8]}"
        
        # 创建 Agent
        agent = AgentLoop(
            bus=self.bus,
            provider=self.provider,
            workspace=self.workspace,
            ...
        )
        
        # 执行任务
        result = await agent.process_direct(
            content=prompt,
            session_key=session_key,
            channel="system",  # 系统消息
        )
        
        # 如果指定回复渠道，发送结果
        if reply_channel and reply_chat_id:
            await self.bus.publish_outbound(OutboundMessage(
                channel=reply_channel,
                chat_id=reply_chat_id,
                content=f"[Spawned Agent] {result}"
            ))
        
        return result
```

---

## MCP 工具集成

### MCP 连接

```python
# nanobot/agent/tools/mcp.py
async def connect_mcp_servers(
    mcp_servers: dict,
    tool_registry: ToolRegistry,
    stack: AsyncExitStack
) -> None:
    """Connect to MCP servers and register their tools."""
    
    for name, config in mcp_servers.items():
        if "command" in config:
            # Stdio 模式
            server = await connect_stdio(name, config, stack)
        elif "url" in config:
            # HTTP 模式
            server = await connect_http(name, config, stack)
        
        # 注册工具
        for tool in server.list_tools():
            tool_registry.register(MCPToolWrapper(server, tool))
```

### MCP 工具包装

```python
class MCPToolWrapper(Tool):
    def __init__(self, server, tool_def):
        self.server = server
        self._def = tool_def
    
    @property
    def name(self) -> str:
        return self._def.name
    
    @property
    def description(self) -> str:
        return self._def.description
    
    @property
    def parameters(self) -> dict:
        return self._def.inputSchema
    
    async def execute(self, **kwargs) -> str:
        result = await self.server.call_tool(self._def.name, kwargs)
        return result.content
```

---

## 渠道集成

### 渠道适配器接口

```python
# nanobot/channels/base.py
class ChannelAdapter(ABC):
    @abstractmethod
    async def start(self) -> None:
        """Start the channel."""
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the channel."""
    
    @abstractmethod
    async def send_message(self, chat_id: str, content: str, **kwargs) -> None:
        """Send a message."""
    
    @abstractmethod
    def parse_incoming(self, raw: Any) -> InboundMessage | None:
        """Parse incoming message."""
```

### Telegram 渠道

```python
# nanobot/channels/telegram.py
class TelegramChannel(ChannelAdapter):
    def __init__(self, token: str, allow_from: list[str] | None = None):
        self.bot = Bot(token=token)
        self.dispatcher = Dispatcher()
        self.allow_from = allow_from or []
    
    async def start(self) -> None:
        self.dispatcher.message.register(self._handle_message)
        await self.dispatcher.start_polling(self.bot)
    
    async def _handle_message(self, message: types.Message):
        # 权限检查
        if self.allow_from and str(message.from_user.id) not in self.allow_from:
            return
        
        # 转换为 InboundMessage
        msg = InboundMessage(
            channel="telegram",
            sender_id=str(message.from_user.id),
            chat_id=str(message.chat.id),
            content=message.text or "",
            metadata={"message_id": str(message.message_id)}
        )
        
        # 发布到消息总线
        await self.bus.publish_inbound(msg)
    
    async def send_message(self, chat_id: str, content: str, **kwargs) -> None:
        await self.bot.send_message(chat_id=int(chat_id), text=content, parse_mode="Markdown")
```

---

## 安全机制

### 1. 命令过滤

```python
DENY_PATTERNS = [
    r"\brm\s+-[rf]{1,2}\b",          # rm -rf
    r"\b(mkfs|diskpart)\b",          # 磁盘操作
    r"\b(shutdown|reboot)\b",        # 系统命令
    r":\(\)\s*\{.*\};\s*:",          # fork bomb
]
```

### 2. 工作区限制

```python
# 配置
{
  "tools": {
    "restrictToWorkspace": true
  }
}

# 效果
# ✅ exec("ls /workspace")  # 允许
# ❌ exec("ls /etc")        # 拒绝
# ❌ exec("cat ../secret")  # 拒绝 (路径遍历)
```

### 3. 渠道白名单

```python
# 配置
{
  "channels": {
    "telegram": {
      "allowFrom": ["123456789"]  # 只有此用户可访问
    }
  }
}
```

---

## 完整驱动流程示例

### 场景: 用户请求分析代码并定时报告

```
1. 用户消息 (Telegram)
   "@nanobot 分析 src/ 目录，每天早上9点发报告"
   
2. Telegram Channel 接收
   → 转换为 InboundMessage
   → 发布到 MessageBus.inbound

3. Agent Loop 处理
   → 消费 InboundMessage
   → 构建上下文 (Session + Memory + Skills)
   → 调用 LLM

4. LLM 决策
   → 调用 list_dir(path="src/")
   → 调用 read_file(path="src/main.py")
   → 调用 cron_add(name="daily_report", cron="0 9 * * *", message="...")

5. 工具执行
   → list_dir: 返回目录列表
   → read_file: 返回文件内容
   → cron_add: 注册定时任务

6. 响应发送
   → 发布到 MessageBus.outbound
   → Telegram Channel 发送消息
```

---

## 与其他项目对比

| 维度 | NanoBot | NanoClaw | TinyClaw |
|------|---------|----------|----------|
| **Shell 执行** | ✅ 本地 (带安全守卫) | ✅ 仅容器 | ✅ 本地 + Docker |
| **文件操作** | ✅ 路径验证 | ✅ 容器内 | ✅ 工作区限制 |
| **Web 工具** | ✅ Brave Search | ✅ 内置 | ✅ Brave Search |
| **消息发送** | ✅ 9 种渠道 | WhatsApp | 4 种 |
| **子 Agent** | ✅ spawn | ✅ | ✅ |
| **MCP 支持** | ✅ Stdio + HTTP | ✅ SDK 内置 | ❌ |
| **执行审批** | ❌ | ❌ | ✅ 自动白名单 |

---

## 总结

### NanoBot 驱动本地 APP 的特点

1. **多工具支持**: 10+ 内置工具 + MCP 扩展
2. **安全守卫**: 命令过滤 + 工作区限制 + 渠道白名单
3. **多渠道**: 9 种消息平台完整实现
4. **子 Agent**: 后台任务独立执行
5. **MCP 集成**: 外部工具服务器无缝接入

### 关键实现亮点

- **异步架构**: asyncio 贯穿整个系统
- **工具上下文**: 动态设置路由信息
- **渐进式加载**: 技能按需加载
- **统一消息总线**: 解耦渠道与核心
