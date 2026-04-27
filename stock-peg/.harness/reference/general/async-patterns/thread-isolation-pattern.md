# Thread Isolation Pattern for Async SDKs

**Priority**: Critical
**Decision**: D027
**Last Updated**: 2026-03-16

**Category**: General / Async Patterns
**Reusable**: Yes (applicable to any project)
**Decision**: D027

---

## TL;DR (Core Insight)

**Problem**: SDKs that call `loop.run_until_complete()` internally crash when used inside an already-running event loop.
**Discovery**: Many SDKs cache event loop at module import time, causing nested event loop errors.
**Solution**: Run SDK in dedicated thread with independent event loop + force module re-import.

---

## Problem Pattern

### When It Occurs
- Integrating async SDKs with FastAPI/asyncio applications
- SDK internally uses `loop.run_until_complete()`
- SDK caches event loop at module level

### Symptoms
```
RuntimeError: This event loop is already running
```

### Identification
1. Check SDK source code for `asyncio.get_event_loop()` at module level
2. Check if SDK has `start()` or `run()` method that blocks
3. Error occurs when calling SDK methods from async context

---

## Root Cause Analysis

### Multi-Layer Problem

**Layer 1: Nested Event Loop**
```python
# FastAPI already runs event loop
# SDK tries to call:
loop.run_until_complete(coro)  # ❌ Error: can't call in running loop
```

**Layer 2: SDK Module-Level Caching**
```python
# SDK module (e.g., lark_oapi/ws/client.py line 25-29)
try:
    loop = asyncio.get_event_loop()  # Caches at import time
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
```

**Layer 3: Wrong Loop in Thread**
- Module imported while FastAPI running → caches FastAPI's loop
- Later call in separate thread → uses cached FastAPI loop (wrong!)
- Thread tries to use FastAPI's loop → nested event loop error

---

## Solution Pattern

### General Solution

```python
import asyncio
import threading
import sys

def start_sdk_in_thread(main_loop: asyncio.AbstractEventLoop) -> None:
    """Start SDK in dedicated thread with independent event loop"""
    thread = threading.Thread(
        target=_run_sdk_in_thread,
        args=(main_loop,),
        daemon=True
    )
    thread.start()

def _run_sdk_in_thread(main_loop: asyncio.AbstractEventLoop) -> None:
    """Thread function with isolated event loop"""
    # Step 1: Create and set thread's event loop
    thread_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(thread_loop)

    # Step 2: Force re-import SDK module (CRITICAL!)
    modules_to_reload = [k for k in sys.modules.keys()
                         if k.startswith('sdk.module.name')]
    for mod in modules_to_reload:
        del sys.modules[mod]

    # Step 3: Import SDK (now caches thread's loop)
    from sdk_module import AsyncClient

    # Step 4: Create and start SDK client
    client = AsyncClient(...)
    client.start()  # Uses thread's loop, not FastAPI's

def run_async_task(coro, main_loop: asyncio.AbstractEventLoop) -> None:
    """Schedule coroutine in main loop from thread"""
    future = asyncio.run_coroutine_threadsafe(coro, main_loop)
```

### Implementation Checklist

- [ ] Create dedicated thread for SDK
- [ ] Create independent event loop in thread
- [ ] Force re-import SDK module after setting thread loop
- [ ] Store reference to main loop for cross-thread communication
- [ ] Use `asyncio.run_coroutine_threadsafe()` for cross-thread tasks

---

## Code Pattern (Essential)

```python
# backend/services/sdk_long_connection_service.py
import asyncio
import threading
import sys
from typing import Any

class SDKLongConnectionService:
    def __init__(self) -> None:
        self._client: Any = None
        self._thread: threading.Thread | None = None
        self._main_loop: asyncio.AbstractEventLoop | None = None

    def start_in_thread(self, main_loop: asyncio.AbstractEventLoop) -> None:
        self._main_loop = main_loop
        self._thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self._thread.start()

    def _run_in_thread(self) -> None:
        # Step 1: Set thread event loop
        thread_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(thread_loop)

        # Step 2: Force re-import (CRITICAL!)
        modules_to_reload = [k for k in sys.modules.keys()
                             if k.startswith('sdk.ws')]
        for mod in modules_to_reload:
            del sys.modules[mod]

        # Step 3: Import and start
        from sdk.ws import Client as WSClient
        self._client = WSClient(...)
        self._client.start()

    def _run_async_task(self, coro) -> None:
        """Schedule in main loop from thread"""
        if self._main_loop:
            asyncio.run_coroutine_threadsafe(coro, self._main_loop)
```

---

## Lessons Learned

### 1. SDK Module-Level State is a Hidden Trap
**Pattern**: Many SDKs cache global state at import time (event loops, DB connections, HTTP clients)
**Solution**: Always check SDK source for module-level initialization

### 2. Module Cache Bypass is Essential
**Pattern**: Force re-import allows SDK to re-initialize with correct context
**Solution**: `del sys.modules['module']` + re-import after setting new context

### 3. Cross-Thread Communication Bridge
**Pattern**: `asyncio.run_coroutine_threadsafe()` is the bridge between threads
**Solution**: Store main loop reference, use for scheduling tasks in main loop

### 4. Prevention Measures
- Check SDK documentation for event loop usage
- Look for `get_event_loop()` at module level
- Test SDK in isolated thread from the start
- Document SDK event loop behavior in project

---

## SKILL Integration

**Extracted SKILL**: `skills/utils/async-sdk-integration/SKILL.md` (to be created)
**Usage**: Use SKILL for guided implementation when integrating async SDKs

---

## Related Resources

**Project-Specific Example**:
- `project-specific/feishu-integration/long-connection-thread-isolation.md` - Feishu implementation

**Architecture Decision**:
- D027: Feishu Long Connection Thread Isolation Pattern

**Similar Issues**:
- Database connection pooling in async context
- HTTP client session management
- WebSocket client integration

---

## Version

- **Created**: 2026-03-16
- **Debugging Time**: 2 hours
- **Version**: 1.0
- **Reusable**: Yes (applicable to any async SDK integration)
