# NanoBot 对话迭代机制分析

## 核心迭代流程

NanoBot 的对话迭代由 `AgentLoop` 类驱动，采用 **Tool-Call 循环** 模式。

```
用户消息 → 消息总线 → AgentLoop → LLM → Tool 执行 → LLM → ... → 最终响应
```

## 迭代流程详解

### 1. 消息接收

```python
# nanobot/agent/loop.py

async def run(self):
    """主循环：从消息总线接收消息"""
    while self._running:
        msg = await self.bus.consume_inbound()  # 阻塞等待
        response = await self._process_message(msg)
        await self.bus.publish_outbound(response)
```

### 2. 上下文构建

```python
async def _process_message(self, msg):
    # 获取或创建会话
    session = self.sessions.get_or_create(msg.session_key)
    
    # 构建消息列表
    history = session.get_history(max_messages=self.memory_window)
    messages = self.context.build_messages(
        history=history,
        current_message=msg.content,
        channel=msg.channel,
        chat_id=msg.chat_id,
    )
```

### 3. Tool-Call 循环 (核心)

```python
async def _run_agent_loop(self, initial_messages, on_progress=None):
    messages = initial_messages
    iteration = 0
    final_content = None
    tools_used = []
    
    while iteration < self.max_iterations:  # 默认 40 次
        iteration += 1
        
        # 调用 LLM
        response = await self.provider.chat(
            messages=messages,
            tools=self.tools.get_definitions(),
            model=self.model,
        )
        
        if response.has_tool_calls:
            # 有工具调用，继续迭代
            for tool_call in response.tool_calls:
                result = await self.tools.execute(tool_call.name, tool_call.arguments)
                messages = self.context.add_tool_result(messages, tool_call.id, tool_call.name, result)
        else:
            # 无工具调用，返回最终结果
            final_content = response.content
            break
    
    return final_content, tools_used, messages
```

### 4. 会话持久化

```python
# 保存对话轮次
self._save_turn(session, all_msgs, 1 + len(history))
self.sessions.save(session)
```

## 对话迭代案例

### 场景：用户请求创建 Python 项目

```
用户: "帮我创建一个 Python 项目 myapp，添加 requests 库，并写一个获取天气的函数"
```

### 迭代过程

#### 迭代 1：理解请求

```
LLM 调用工具:
  read_file(path="workspace/skills/python-project/SKILL.md")

工具返回:
  Skill 内容（项目结构、命令等）

LLM 思考:
  用户要创建项目，需要：
  1. 创建目录结构
  2. 初始化虚拟环境
  3. 安装 requests
  4. 编写天气函数
```

#### 迭代 2：创建目录

```
LLM 调用工具:
  exec(command="mkdir -p myapp/src myapp/tests")

工具返回:
  目录创建成功
```

#### 迭代 3：初始化虚拟环境

```
LLM 调用工具:
  exec(command="cd myapp && python3 -m venv .venv")

工具返回:
  虚拟环境创建成功
```

#### 迭代 4：安装依赖

```
LLM 调用工具:
  exec(command="cd myapp && .venv/bin/pip install requests")

工具返回:
  Successfully installed requests-2.31.0
```

#### 迭代 5：创建源文件

```
LLM 调用工具:
  write_file(path="myapp/src/weather.py", content="...")

工具返回:
  文件写入成功
```

#### 迭代 6：最终响应

```
LLM 响应:
  "我已经创建了 myapp 项目，包含以下结构：
   
   myapp/
   ├── .venv/
   ├── src/
   │   └── weather.py    # 获取天气的函数
   └── tests/
   
   requests 库已安装。使用方法：
   ```python
   from src.weather import get_weather
   weather = get_weather("London")
   ```"
```

## 会话记忆机制

### 双层记忆

```
workspace/memory/
├── MEMORY.md      # 长期记忆（重要事实）
└── HISTORY.md     # 历史日志（可 grep 搜索）
```

### 记忆整合

```python
async def _consolidate_memory(self, session):
    """将旧消息整合到记忆文件"""
    # 当未整合消息超过阈值时触发
    if len(session.messages) - session.last_consolidated >= self.memory_window:
        # 调用 LLM 总结
        response = await provider.chat(
            messages=[...],
            tools=_SAVE_MEMORY_TOOL,  # save_memory 工具
        )
        # 写入 MEMORY.md 和 HISTORY.md
```

### 对话历史窗口

```python
# 只保留最近的 N 条消息在上下文中
history = session.get_history(max_messages=100)  # 默认 100 条

# 旧消息通过记忆整合保留在 MEMORY.md 中
```

## 进度反馈机制

```python
async def _bus_progress(content: str, *, tool_hint: bool = False):
    """发送进度消息到消息总线"""
    meta = {"_progress": True, "_tool_hint": tool_hint}
    await self.bus.publish_outbound(OutboundMessage(
        channel=msg.channel,
        chat_id=msg.chat_id,
        content=content,  # 如 "正在执行命令..."
        metadata=meta,
    ))
```

用户看到：

```
用户: 创建项目
Agent: 让我检查一下现有的 skill...
Agent: exec("mkdir -p myapp")
Agent: 项目已创建完成！
```

## 迭代控制

### 最大迭代次数

```python
max_iterations: int = 40  # 防止无限循环

if iteration >= self.max_iterations:
    final_content = "I reached the maximum number of tool call iterations..."
```

### 工具结果截断

```python
_TOOL_RESULT_MAX_CHARS = 500

# 截断过长的工具结果，避免上下文膨胀
if len(content) > self._TOOL_RESULT_MAX_CHARS:
    entry["content"] = content[:500] + "\n... (truncated)"
```

## 与 NanoClaw 对比

| 维度 | NanoBot | NanoClaw |
|------|---------|----------|
| 迭代引擎 | 自实现 AgentLoop | Claude Agent SDK |
| 工具定义 | Python ToolRegistry | MCP Server |
| 会话存储 | JSONL 文件 | SDK 内置 |
| 记忆机制 | 双层记忆 | 自动 compaction |
| 最大迭代 | 40 次 | SDK 配置 |
