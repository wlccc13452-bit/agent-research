# D022-D027: Feishu Integration Architecture

**Date**: 2026-03-15 to 2026-03-16
**Status**: Active

This document consolidates Feishu integration architectural decisions.

---

## Overview

Feishu bot integration enables stock queries via messaging platform with WebSocket real-time updates.

---

## D022: Feishu Bot Integration for Stock Queries

### Decision
Integrate Feishu bot to enable stock queries via messaging platform.

### Reason
- Convenient access to stock information via chat interface
- Real-time notifications and alerts
- Mobile-friendly interaction
- Seamless integration with existing stock data services

### Commands Supported
- `查询 [股票名称或代码]` - Query stock information
- `行情 [股票名称或代码]` - Query stock quotes
- `股票 [股票名称或代码]` - Query stock details
- `帮助` / `help` - Show help message

### Files Created
- `backend/services/feishu_bot.py` - Bot service logic
- `backend/routers/feishu.py` - Webhook router
- `backend/routers/feishu_chat.py` - Chat history API
- `frontend/src/components/BotChatTab.tsx` - Frontend UI

---

## D023: WebSocket Broadcast for Feishu Chat

### Decision
Add WebSocket broadcast in both user message and bot message handlers.

### Reason
- Frontend needs real-time conversation updates
- User messages must be visible immediately after sending
- Bot responses must appear without manual refresh
- Consistent with other real-time features in the project

### Implementation
```python
# backend/routers/feishu.py:144-155
async def handle_user_message(message: FeishuMessage):
    # Save message to database
    await save_chat_message(message)
    
    # Broadcast to all WebSocket clients
    await manager.broadcast({
        "type": "feishu_chat",
        "data": message.dict()
    })

# backend/services/feishu_bot.py:287-300
async def send_bot_reply(message_id: str, content: str):
    # Send reply via Feishu API
    await reply_message(message_id, content)
    
    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "feishu_chat",
        "data": {"role": "bot", "content": content}
    })
```

### Impact
- Real-time conversation updates enabled
- No need for polling or manual refresh
- Better user experience for Bot chat

---

## D024: Async SQLAlchemy Query Pattern

### Decision
Use `select()` + `execute()` pattern instead of `db.query()` for all database operations.

### Reason
- Project uses AsyncSession throughout backend
- `db.query()` is synchronous SQLAlchemy 1.x syntax
- `select()` + `execute()` is async-compatible SQLAlchemy 2.0 syntax
- Prevents "AsyncSession object has no attribute 'query'" errors

### Pattern
```python
# Correct (SQLAlchemy 2.0 async)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_messages(db: AsyncSession):
    result = await db.execute(select(ChatMessage))
    messages = result.scalars().all()
    return messages

# Count query
total = await db.scalar(
    select(func.count()).select_from(ChatMessage)
)
```

### Prohibition
❌ Never use `db.query()` with AsyncSession
❌ Never use `async for session in db` in FastAPI routes

### Files Modified
- `backend/routers/feishu_chat.py` - Updated all queries to async pattern

---

## D025: Feishu Timestamp String Handling

### Decision
Always convert Feishu timestamp fields to integer before arithmetic operations.

### Reason
- Feishu webhook sends `create_time` as string type (e.g., "1712345678901")
- Direct division operation causes TypeError
- Function crashes before WebSocket broadcast is sent
- Type conversion must be wrapped in try-except for robustness

### Implementation
```python
# backend/routers/feishu.py:135-145
def parse_feishu_timestamp(timestamp_str: str) -> datetime:
    try:
        timestamp_ms = int(timestamp_str)
        timestamp_sec = timestamp_ms / 1000
        return datetime.fromtimestamp(timestamp_sec)
    except (ValueError, TypeError):
        # Fallback to current time
        return datetime.now()
```

### Impact
- All Feishu timestamp fields must use `int(timestamp_str)` before division
- Added fallback to current time if conversion fails
- WebSocket broadcasts now execute successfully

---

## D026: Feishu API Data Source Priority

### Decision
Database-first for `/api/feishu-chat/recent` endpoint.

### Reason
- Previous implementation returned log file data first, missing new messages in database
- Frontend refresh triggered by WebSocket but API returned stale data
- Database is the authoritative source of truth for chat messages

### Implementation
```python
# backend/routers/feishu_chat.py:166-211
async def get_recent_chat_messages(limit: int = 50):
    # Step 1: Query database first
    db_messages = await get_messages_from_db(limit)
    
    if db_messages:
        return db_messages
    
    # Step 2: Fallback to log file only if database is empty
    log_messages = parse_messages_from_log()
    return log_messages
```

### Impact
- Real-time message updates now work correctly after WebSocket broadcast
- Ensures consistency between WebSocket notifications and API responses

---

## D027: Feishu Long Connection Thread Isolation Pattern

### Decision
Run Feishu long connection service in isolated thread with independent event loop.

### Reason
- FastAPI runs in asyncio event loop
- Feishu SDK's `ws_client.start()` internally calls `loop.run_until_complete()`
- Cannot call `run_until_complete()` inside an already-running event loop (nested event loop error)
- SDK caches event loop at module import time via `asyncio.get_event_loop()`

### Solution Architecture
```python
# backend/services/feishu_long_connection_service.py
def start_in_thread(self, main_loop: asyncio.AbstractEventLoop) -> None:
    """Start long connection in dedicated thread"""
    self._main_loop = main_loop  # Store reference to main loop
    self._thread = threading.Thread(target=self._run_in_thread, daemon=True)
    self._thread.start()

def _run_in_thread(self) -> None:
    """Run in dedicated thread with independent event loop"""
    # Step 1: Create and set thread event loop
    thread_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(thread_loop)
    
    # Step 2: Force re-import WebSocket module (CRITICAL!)
    import sys
    modules_to_reload = [k for k in sys.modules.keys() 
                         if k.startswith('lark_oapi.ws')]
    for mod in modules_to_reload:
        del sys.modules[mod]
    
    # Step 3: Import and create client
    from lark_oapi.ws import Client as WSClient
    self._ws_client = WSClient(...)
    
    # Step 4: Start client (uses thread's event loop)
    self._ws_client.start()

def _run_async_task(self, coro) -> None:
    """Schedule coroutine in main loop from thread"""
    future = asyncio.run_coroutine_threadsafe(coro, self._main_loop)
```

### Async Processing Enhancement
```python
def _handle_message_receive(self, data: Any) -> None:
    # ... parse message ...
    if self._needs_async_processing(cmd):
        # Quick reply to user
        self._send_quick_reply(message.message_id, "⏳ 正在处理，请稍候...")
        
        # Process asynchronously in main loop
        self._run_async_task(
            self._process_command_async(chat_id, message.message_id, user_text, sender_id)
        )
    else:
        # Simple command: reply immediately
        reply_content = self._build_simple_reply(cmd)
        self._send_reply_and_broadcast(chat_id, message.message_id, reply_content)
```

### Impact
- Eliminates "This event loop is already running" error
- Enables coexistence of FastAPI event loop and Feishu long connection
- Supports async task processing without blocking message handler
- Complex commands can reply quickly and process in background

### Files Modified
- `backend/services/feishu_long_connection_service.py` - Refactored to thread-isolated architecture
- `backend/main.py` - Updated startup logic to pass main loop reference

### Key Learning
Many Python SDKs cache event loop at module import time. When running in multi-threaded async environments, this can cause subtle bugs. Solution: Force module re-import after setting thread's event loop using `del sys.modules['module_name']`.

---

## Lessons Learned

1. **SDK Module-Level Caching Trap**: Always check SDK source code for module-level state caching
2. **Thread Isolation Pattern**: Essential for SDKs that call `run_until_complete()` internally
3. **Cross-Thread Communication**: `asyncio.run_coroutine_threadsafe()` is the bridge between threads
4. **Type Safety**: Feishu webhook data types can be unexpected (string timestamps)
5. **Database First**: Always query database for authoritative data, fallback to files/logs

---

## Related Documents

- `reference/debugging/feishu-event-loop-conflict.md` - Detailed debugging record
- `session-summaries/2026-03-16-feishu-event-loop-fix.md` - Session summary
- `memory/core-facts.md` - Environment constraints (ports, runtime)
