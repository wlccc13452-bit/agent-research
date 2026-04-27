# Feishu Bot Integration Architecture

**Priority**: Standard
**Category**: Project-Specific / Feishu Integration
**Last Updated**: 2026-03-16
**Reusable**: No (Feishu-specific, requires Feishu account configuration)
**Decision**: D022-D027

---

## TL;DR (Core Insight)

**Goal**: Enable stock queries via Feishu messaging platform with real-time WebSocket updates.
**Challenge**: SDK event loop conflicts, message duplication, WebSocket broadcast consistency.
**Solution**: Webhook + Long connection hybrid architecture with thread-isolated long connection.

---

## Architecture Overview

```
Feishu Cloud
    ↓ (Webhook POST)
FastAPI Backend
    ↓ (save to DB)
SQLite Database
    ↓ (WebSocket broadcast)
Frontend BotChatTab
    ↑ (Real-time updates)

Feishu Cloud
    ↔ (Long Connection WebSocket)
Long Connection Service (Thread)
    ↓ (cross-thread task scheduling)
FastAPI Main Loop
```

---

## Components

### 1. Webhook Router (Primary)

**Purpose**: Receive Feishu message events via HTTP POST

**File**: `backend/routers/feishu.py`

**Key Features**:
- Signature verification (security)
- Message parsing and routing
- WebSocket broadcast to frontend
- Save to database

**Code Pattern**:
```python
@router.post("/api/feishu/webhook")
async def handle_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    # 1. Verify signature
    body = await request.body()
    signature = request.headers.get("X-Lark-Signature")
    if not verify_signature(body, signature):
        raise HTTPException(401)

    # 2. Parse event
    event = json.loads(body)
    message = parse_message(event)

    # 3. Save to database
    await save_chat_message(db, message)

    # 4. Broadcast to frontend
    await manager.broadcast({
        "type": "feishu_chat",
        "data": message.dict()
    })

    return {"status": "ok"}
```

---

### 2. Long Connection Service (Secondary)

**Purpose**: Maintain persistent WebSocket connection for real-time bidirectional communication

**File**: `backend/services/feishu_long_connection_service.py`

**Architecture**: Thread-isolated (see `general/async-patterns/thread-isolation-pattern.md`)

**Key Features**:
- Runs in dedicated thread with independent event loop
- Handles message receive events
- Cross-thread task scheduling to main loop
- Async command processing

**Code Pattern**:
```python
def start_in_thread(self, main_loop: asyncio.AbstractEventLoop) -> None:
    self._main_loop = main_loop
    self._thread = threading.Thread(target=self._run_in_thread, daemon=True)
    self._thread.start()

def _handle_message_receive(self, data: Any) -> None:
    # Parse message
    message = parse_feishu_message(data)

    # Quick reply for complex commands
    if self._needs_async_processing(message.content):
        self._send_quick_reply(message.message_id, "⏳ Processing...")
        self._run_async_task(
            self._process_command_async(message)
        )
    else:
        reply = self._build_reply(message.content)
        self._send_reply_and_broadcast(message, reply)
```

---

### 3. Bot Service (Core Logic)

**Purpose**: Process user commands and generate responses

**File**: `backend/services/feishu_bot.py`

**Supported Commands**:
- `查询 [股票]` - Query stock information
- `行情 [股票]` - Query real-time quotes
- `股票 [股票]` - Query stock details
- `帮助` - Show help message

**Stock Query Flow**:
```python
async def process_stock_query(self, stock_input: str) -> str:
    # 1. Resolve stock code
    stock_code = self._resolve_stock_code(stock_input)

    # 2. Fetch data
    quote = await self.akshare_service.get_quote(stock_code)
    kline = await self.akshare_service.get_kline(stock_code)

    # 3. Format response
    response = self._format_stock_response(stock_code, quote, kline)

    return response
```

---

### 4. Chat History API

**Purpose**: Provide chat history for frontend display

**File**: `backend/routers/feishu_chat.py`

**Key Endpoints**:
- `GET /api/feishu-chat/recent` - Get recent messages (database-first)
- `POST /api/feishu/send-to-recent-chat` - Send message to recent chat

**Database-First Strategy** (D026):
```python
async def get_recent_messages(db: AsyncSession, limit: int = 50):
    # Priority 1: Database (authoritative)
    db_messages = await get_messages_from_db(db, limit)
    if db_messages:
        return db_messages

    # Priority 2: Log file (fallback)
    log_messages = parse_messages_from_log()
    return log_messages
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# Feishu App Configuration
FEISHU_APP_ID=cli_xxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxx
FEISHU_VERIFICATION_TOKEN=xxxxxxxxxxxxxxxx

# Feishu Bot Configuration
FEISHU_BOT_NAME=StockBot

# Long Connection (Optional)
FEISHU_LONG_CONNECTION_ENABLED=true
```

### Feishu Developer Console Setup

1. Create Feishu app at https://open.feishu.cn/
2. Enable bot capability
3. Configure webhook URL: `http://your-server:8000/api/feishu/webhook`
4. Subscribe to events: `im.message.receive_v1`
5. Get app credentials (APP_ID, APP_SECRET)

---

## Data Flow

### User Message Flow

```
1. User sends message in Feishu app
   ↓
2. Feishu cloud POSTs to webhook endpoint
   ↓
3. Backend verifies signature
   ↓
4. Parse message content
   ↓
5. Save to database (SQLite)
   ↓
6. Broadcast to frontend via WebSocket
   ↓
7. Frontend displays in BotChatTab
```

### Bot Reply Flow

```
1. Bot service processes command
   ↓
2. Query stock data from akshare_service
   ↓
3. Format response (Markdown)
   ↓
4. Send via Feishu API
   ↓
5. Save bot message to database
   ↓
6. Broadcast to frontend via WebSocket
```

---

## Security

### Signature Verification

**Purpose**: Verify webhook requests are from Feishu

**Algorithm**: HMAC-SHA256

```python
import hmac
import hashlib

def verify_signature(body: bytes, signature: str) -> bool:
    expected = hmac.new(
        FEISHU_APP_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)
```

### Timestamp Handling (D025)

**Problem**: Feishu sends timestamps as strings

**Solution**: Always convert to int before arithmetic

```python
def parse_feishu_timestamp(timestamp_str: str) -> datetime:
    try:
        timestamp_ms = int(timestamp_str)  # Convert to int
        timestamp_sec = timestamp_ms / 1000
        return datetime.fromtimestamp(timestamp_sec)
    except (ValueError, TypeError):
        return datetime.now()  # Fallback
```

---

## Message Format

### User Message (from Feishu)

```json
{
  "message_id": "om_xxxxxxxxx",
  "chat_id": "oc_xxxxxxxxx",
  "sender": {
    "sender_id": {
      "user_id": "ou_xxxxxxxxx"
    }
  },
  "create_time": "1712345678901",  // String timestamp
  "content": "查询 平安银行"
}
```

### Bot Reply (Markdown)

```markdown
**平安银行 (000001)**

📈 **行情信息**
- 现价: **12.50** (+0.80% ↑)
- 成交量: 1.23亿
- 成交额: 15.4亿

📊 **技术指标**
- Force Index: 买入信号 (强度: 7.5)
- 趋势: 上涨趋势
```

---

## Troubleshooting

### Issue 1: Duplicate Messages

**Cause**: Both webhook and long connection receive same message

**Solution**: Check for duplicates in `save_chat_message()`

```python
async def save_chat_message(db: AsyncSession, message: Message) -> bool:
    # Check if exists
    existing = await db.execute(
        select(ChatMessage).where(ChatMessage.message_id == message.message_id)
    )
    if existing.scalar_one_or_none():
        return False  # Duplicate

    # Save new message
    db.add(ChatMessage(**message.dict()))
    await db.commit()
    return True
```

### Issue 2: WebSocket Broadcast Not Received

**Cause**: Broadcast only on `save_ok=True`, but duplicates return `False`

**Solution**: Always broadcast, regardless of save status

```python
# Always broadcast
await manager.broadcast({
    "type": "feishu_chat",
    "data": message.dict()
})
```

### Issue 3: Event Loop Already Running

**Cause**: Long connection SDK uses FastAPI's event loop

**Solution**: Thread isolation + module re-import (see `general/async-patterns/thread-isolation-pattern.md`)

---

## Related Resources

**General Patterns Used**:
- `general/async-patterns/thread-isolation-pattern.md` - Long connection thread isolation
- `general/sdk-integration/module-level-caching.md` - SDK cache bypass
- `general/database-patterns/async-sqlalchemy-2.0.md` - Database queries

**Architecture Decisions**:
- D022: Feishu Bot Integration
- D023: WebSocket Broadcast
- D024: Async SQLAlchemy Pattern
- D025: Timestamp String Handling
- D026: Database-First API
- D027: Long Connection Thread Isolation

---

## Version

- **Created**: 2026-03-16
- **Debugging Time**: 4 hours total (event loop, duplicate messages, broadcast, API)
- **Version**: 1.0
- **Reusable**: No (Feishu-specific, requires project configuration)
