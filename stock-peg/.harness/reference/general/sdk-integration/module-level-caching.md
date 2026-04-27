# Module-Level Event Loop Caching Trap

**Priority**: Critical
**Category**: General / SDK Integration
**Last Updated**: 2026-03-16
**Reusable**: Yes (applicable to any project)
**Decision**: D027

---

## TL;DR (Core Insight)

**Problem**: SDK caches event loop at module import time, using wrong loop in multi-threaded async environments.
**Discovery**: `asyncio.get_event_loop()` at module level caches the event loop of the importing context.
**Solution**: Delete module from `sys.modules` and re-import after setting correct event loop.

---

## Problem Pattern

### When It Occurs
- SDK uses `asyncio.get_event_loop()` at module level
- Module imported in one context (e.g., FastAPI main loop)
- Used in another context (e.g., separate thread)
- SDK uses cached loop from wrong context

### Symptoms
```python
# Error scenario
import sdk_module  # Imported while FastAPI running

def run_in_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # SDK still uses FastAPI's loop (cached at import)
    sdk_module.start()  # ❌ RuntimeError: event loop already running
```

### Identification
1. Check SDK source code for module-level code
2. Look for `asyncio.get_event_loop()` outside functions
3. Look for `loop = ...` at module top level
4. Test: import in different contexts, check behavior

---

## Root Cause Analysis

### SDK Module Pattern (Common)

```python
# sdk_module/client.py (line 1-10)
import asyncio

# Module-level initialization
try:
    loop = asyncio.get_event_loop()  # ❌ Caches at import time
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Later in code
class Client:
    def start(self):
        self.loop.run_until_complete(...)  # Uses cached loop
```

### Why It's a Problem

```
Time T0: FastAPI starts, creates event loop (loop_A)
Time T1: Import sdk_module
         → asyncio.get_event_loop() returns loop_A
         → sdk_module.loop = loop_A (cached)

Time T2: Create new thread
Time T3: In thread, create new event loop (loop_B)
Time T4: Call sdk_module.start()
         → Uses loop_A (cached), not loop_B (thread's loop)
         → loop_A is running in FastAPI
         → ❌ RuntimeError: This event loop is already running
```

---

## Solution Pattern

### Module Cache Bypass

```python
import sys
import asyncio

def reinit_sdk_in_thread() -> None:
    """Force SDK to use thread's event loop"""

    # Step 1: Set thread's event loop
    thread_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(thread_loop)

    # Step 2: Delete SDK module from cache (CRITICAL!)
    modules_to_reload = [k for k in sys.modules.keys()
                         if k.startswith('sdk.module')]
    for mod in modules_to_reload:
        del sys.modules[mod]

    # Step 3: Re-import SDK module
    from sdk_module import Client  # Now caches thread_loop

    # Step 4: Use SDK (it now uses thread's loop)
    client = Client(...)
    client.start()  # ✅ Uses thread_loop
```

### Why It Works

1. `del sys.modules['module']` removes cached module
2. Next `import` triggers module-level code again
3. Module-level `asyncio.get_event_loop()` now returns thread's loop
4. SDK caches correct loop for this context

---

## Code Pattern (Essential)

```python
import sys
import asyncio
from typing import List

def force_module_reimport(module_prefix: str) -> None:
    """Force re-import of modules matching prefix"""
    modules_to_reload: List[str] = [
        k for k in sys.modules.keys()
        if k.startswith(module_prefix)
    ]
    for mod in modules_to_reload:
        del sys.modules[mod]

def setup_sdk_with_correct_loop() -> None:
    """Setup SDK in new event loop context"""
    # Create new loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Force re-import
    force_module_reimport('sdk.ws')

    # Import SDK (caches new loop)
    from sdk.ws import Client
    return Client
```

---

## Lessons Learned

### 1. Always Check Module-Level Code
**Pattern**: SDK initialization at module level is common
**Check**: `grep -n "get_event_loop" sdk_module/*.py | head -20`
**Action**: If found, plan for re-import strategy

### 2. Module Cache is Both Feature and Trap
**Feature**: Speed optimization (no re-execution of module code)
**Trap**: Stale state when context changes
**Solution**: Explicit cache bypass when needed

### 3. Context Matters for Imports
**Pattern**: Import context affects module-level initialization
**Rule**: Import in the context where SDK will be used
**Example**: Import async SDK in thread, not at module top

### 4. Prevention Measures
- Document SDK event loop behavior
- Create wrapper that handles re-import
- Test SDK in multi-threaded environment early
- Check SDK updates for loop handling changes

---

## SKILL Integration

**Extracted SKILL**: `skills/utils/module-cache-bypass/SKILL.md` (to be created)
**Usage**: Use SKILL when integrating SDKs with module-level state

---

## Related Resources

**Related Pattern**:
- `general/async-patterns/thread-isolation-pattern.md` - Full solution with thread isolation

**Architecture Decision**:
- D027: Feishu Long Connection Thread Isolation Pattern

**Similar Issues**:
- Database connection pools at module level
- HTTP client sessions cached globally
- Configuration objects initialized at import

---

## Version

- **Created**: 2026-03-16
- **Debugging Time**: 1.5 hours (discovered during D027 debugging)
- **Version**: 1.0
- **Reusable**: Yes (applicable to any SDK with module-level state)
