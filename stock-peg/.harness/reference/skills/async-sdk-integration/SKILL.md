# Async SDK Integration SKILL

**Priority**: Critical
**Last Updated**: 2026-03-16
**Trigger**: When integrating async SDKs that call `run_until_complete()` internally
**Purpose**: Guide thread isolation pattern implementation for async SDKs

---

## Quick Reference

**Core Pattern** (3 lines):
```
SDK calls run_until_complete() → Can't use in running loop
→ Run in dedicated thread with new event loop
→ Force re-import SDK to cache thread's loop
```

---

## Step-by-Step Execution

### Step 1: Identify SDK Event Loop Behavior

**Check SDK source code**:
```bash
grep -rn "get_event_loop\|run_until_complete" sdk_package/
```

**Red flags**:
- `loop = asyncio.get_event_loop()` at module level
- `loop.run_until_complete()` in SDK methods
- Blocking `start()` or `run()` methods

**Example**:
```python
# sdk_module/client.py (problematic)
try:
    loop = asyncio.get_event_loop()  # ❌ Caches at import
except RuntimeError:
    loop = asyncio.new_event_loop()
```

---

### Step 2: Create Service Class Structure

**Template**:
```python
import asyncio
import threading
import sys
from typing import Any

class SDKLongConnectionService:
    def __init__(self) -> None:
        self._client: Any = None
        self._thread: threading.Thread | None = None
        self._main_loop: asyncio.AbstractEventLoop | None = None
        self._running = False
```

---

### Step 3: Implement Thread Start Method

**Code**:
```python
def start_in_thread(self, main_loop: asyncio.AbstractEventLoop) -> None:
    """Start SDK in dedicated thread with independent event loop"""
    self._main_loop = main_loop  # Store main loop reference
    self._running = True

    self._thread = threading.Thread(
        target=self._run_in_thread,
        daemon=True
    )
    self._thread.start()
```

---

### Step 4: Implement Thread Function with Event Loop Isolation

**Code**:
```python
def _run_in_thread(self) -> None:
    """Run SDK in isolated thread event loop"""
    # Step 4.1: Create and set thread's event loop
    thread_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(thread_loop)

    # Step 4.2: Force re-import SDK module (CRITICAL!)
    modules_to_reload = [k for k in sys.modules.keys()
                         if k.startswith('sdk.module.name')]
    for mod in modules_to_reload:
        del sys.modules[mod]

    # Step 4.3: Import SDK (now caches thread's loop)
    from sdk_module import AsyncClient

    # Step 4.4: Create and start SDK client
    self._client = AsyncClient(...)
    self._client.start()  # Uses thread's loop
```

---

### Step 5: Implement Cross-Thread Task Scheduling

**Code**:
```python
def _run_async_task(self, coro) -> None:
    """Schedule coroutine in main loop from thread"""
    if self._main_loop and not self._main_loop.is_closed():
        future = asyncio.run_coroutine_threadsafe(coro, self._main_loop)
        # Optional: Add timeout
        # try:
        #     future.result(timeout=30)
        # except Exception as e:
        #     logger.error(f"Task failed: {e}")
```

**Usage**:
```python
def _handle_event(self, data: Any) -> None:
    # Process in main loop
    self._run_async_task(
        self._process_event_async(data)
    )
```

---

### Step 6: Update Main Application Startup

**Code**:
```python
# backend/main.py
from services.sdk_long_connection_service import sdk_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Get main loop reference
    main_loop = asyncio.get_running_loop()

    # Start SDK in thread
    sdk_service.start_in_thread(main_loop)

    yield

    # Cleanup
    sdk_service.stop()
```

---

## Validation

- [ ] SDK source code checked for event loop usage
- [ ] Service class created with thread isolation
- [ ] Thread function implements event loop creation
- [ ] SDK module re-imported after setting thread loop
- [ ] Cross-thread task scheduling implemented
- [ ] Main application updated with startup logic
- [ ] Tested: No "event loop is already running" error
- [ ] Tested: SDK methods work correctly in thread

---

## Common Pitfalls

### 1. Forgetting to Re-import SDK

**Pitfall**: Created new event loop but didn't re-import SDK
**Result**: SDK still uses old (main) loop → Error
**Solution**:
```python
# ❌ WRONG
thread_loop = asyncio.new_event_loop()
asyncio.set_event_loop(thread_loop)
from sdk_module import Client  # Caches main loop!

# ✅ CORRECT
thread_loop = asyncio.new_event_loop()
asyncio.set_event_loop(thread_loop)
del sys.modules['sdk_module']  # Force re-import
from sdk_module import Client  # Caches thread loop
```

---

### 2. Not Storing Main Loop Reference

**Pitfall**: Can't schedule tasks back to main loop
**Result**: Lost bidirectional communication
**Solution**:
```python
def start_in_thread(self, main_loop: asyncio.AbstractEventLoop):
    self._main_loop = main_loop  # ✅ Store reference
```

---

### 3. Blocking in Event Handler

**Pitfall**: Long-running task blocks SDK thread
**Result**: SDK becomes unresponsive
**Solution**:
```python
def _handle_event(self, data):
    # Quick reply
    self._send_reply(data.message_id, "Processing...")

    # Process in main loop (non-blocking)
    self._run_async_task(
        self._process_async(data)
    )
```

---

## Code Template

**Full Implementation** (< 50 lines):
```python
import asyncio, threading, sys
from typing import Any

class SDKService:
    def __init__(self): self._client, self._thread, self._main_loop, self._running = None, None, None, False

    def start_in_thread(self, main_loop: asyncio.AbstractEventLoop):
        self._main_loop, self._running = main_loop, True
        self._thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self._thread.start()

    def _run_in_thread(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        for m in [k for k in sys.modules if k.startswith('sdk.ws')]: del sys.modules[m]
        from sdk.ws import Client
        self._client = Client(...)
        self._client.start()

    def _run_async_task(self, coro):
        if self._main_loop: asyncio.run_coroutine_threadsafe(coro, self._main_loop)

    def stop(self):
        self._running = False
        if self._client: self._client.stop()
```

---

## Related Resources

**Reference Document**: `reference/general/async-patterns/thread-isolation-pattern.md`
**Module Caching**: `reference/general/sdk-integration/module-level-caching.md`
**Decision**: D027

---

## Version

- **Created**: 2026-03-16
- **Version**: 1.0
- **Size**: < 200 lines (精华版)
