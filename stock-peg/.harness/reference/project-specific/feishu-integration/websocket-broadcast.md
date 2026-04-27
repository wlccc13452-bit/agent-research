# WebSocket Broadcast Implementation

**Priority**: Standard
**Category**: Project-Specific / Feishu Integration
**Last Updated**: 2026-03-16
**Reusable**: Limited (pattern reusable, implementation project-specific)
**Decision**: D023

---

## TL;DR

**Purpose**: Real-time conversation updates in frontend BotChatTab.
**Challenge**: Both user messages and bot messages need broadcasting.
**Solution**: Broadcast in both webhook handler and bot service.

---

## Architecture

### Broadcast Points

```
User Message:
  Feishu Webhook → backend/routers/feishu.py → WebSocket Broadcast

Bot Reply:
  Bot Service → backend/services/feishu_bot.py → WebSocket Broadcast
```

---

## Implementation

### WebSocket Manager

**File**: `backend/services/websocket_manager.py`

```python
from fastapi import WebSocket
from typing import List
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection might be closed
                pass

manager = ConnectionManager()
```

---

### User Message Broadcast

**File**: `backend/routers/feishu.py`

```python
from services.websocket_manager import manager

@router.post("/api/feishu/webhook")
async def handle_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    # ... parse message ...

    # Save to database
    await save_chat_message(db, message)

    # Broadcast to all WebSocket clients
    await manager.broadcast({
        "type": "feishu_chat",
        "data": {
            "role": "user",
            "message_id": message.message_id,
            "chat_id": message.chat_id,
            "content": message.content,
            "sender_id": message.sender_id,
            "timestamp": message.timestamp.isoformat()
        }
    })

    return {"status": "ok"}
```

---

### Bot Message Broadcast

**File**: `backend/services/feishu_bot.py`

```python
from services.websocket_manager import manager

async def send_bot_reply(chat_id: str, message_id: str, content: str):
    # Send via Feishu API
    await reply_message(message_id, content)

    # Save to database
    bot_message = ChatMessage(
        message_id=f"bot_{message_id}",
        chat_id=chat_id,
        content=content,
        role="bot",
        timestamp=datetime.now()
    )
    await save_chat_message(db, bot_message)

    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "feishu_chat",
        "data": {
            "role": "bot",
            "message_id": bot_message.message_id,
            "chat_id": chat_id,
            "content": content,
            "timestamp": bot_message.timestamp.isoformat()
        }
    })
```

---

### Frontend Listener

**File**: `frontend/src/components/BotChatTab.tsx`

```typescript
import { useEffect, useState } from 'react'

interface Message {
  role: 'user' | 'bot'
  content: string
  timestamp: string
}

export function BotChatTab() {
  const [messages, setMessages] = useState<Message[]>([])

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws')

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'feishu_chat') {
        setMessages(prev => [...prev, data.data])
      }
    }

    return () => ws.close()
  }, [])

  return (
    <div>
      {messages.map((msg, idx) => (
        <div key={idx} className={msg.role === 'bot' ? 'bot-message' : 'user-message'}>
          {msg.content}
        </div>
      ))}
    </div>
  )
}
```

---

## Message Format

### WebSocket Message Structure

```typescript
{
  "type": "feishu_chat",
  "data": {
    "role": "user" | "bot",
    "message_id": string,
    "chat_id": string,
    "content": string,  // Markdown format
    "sender_id": string,  // For user messages
    "timestamp": string  // ISO format
  }
}
```

---

## Key Learnings

### 1. Always Broadcast (D023 Fix)

**Problem**: Only broadcast when `save_ok=True`, but duplicates return `False`

**Wrong Pattern**:
```python
save_ok = await save_chat_message(db, message)
if save_ok:  # ❌ Won't broadcast duplicates
    await manager.broadcast(...)
```

**Correct Pattern**:
```python
await save_chat_message(db, message)
# Always broadcast, regardless of save status
await manager.broadcast(...)  # ✅
```

### 2. Message Deduplication at Save, Not Broadcast

**Pattern**:
- Database: Check for duplicates, don't save duplicates
- WebSocket: Always broadcast, frontend handles duplicates via message_id

### 3. Cross-Thread Broadcasting

**From Long Connection Thread**:
```python
def _run_async_task(self, coro):
    """Schedule in main loop from thread"""
    future = asyncio.run_coroutine_threadsafe(coro, self._main_loop)
```

**Usage**:
```python
# In long connection thread
self._run_async_task(
    manager.broadcast({
        "type": "feishu_chat",
        "data": message.dict()
    })
)
```

---

## Performance Considerations

### Connection Management

- Keep connections list small (< 100 connections)
- Remove closed connections promptly
- Handle connection errors gracefully

### Broadcasting

- Non-blocking: Use `asyncio.create_task()` if needed
- Error handling: Don't let one failed send break others
- Message size: Keep < 10KB per message

---

## Related Resources

**Project-Specific**:
- `project-specific/feishu-integration/bot-architecture.md` - Overall architecture

**Architecture Decision**:
- D023: WebSocket Broadcast for Feishu Chat

---

## Version

- **Created**: 2026-03-16
- **Debugging Time**: 1 hour
- **Version**: 1.0
- **Reusable**: Limited (pattern reusable, implementation specific)
