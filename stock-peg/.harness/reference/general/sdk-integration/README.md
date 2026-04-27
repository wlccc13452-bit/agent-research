# General SDK Integration Patterns

This directory contains **reusable SDK integration patterns** applicable to any project.

---

## Core Principle

**Reusable Knowledge**: Independent of specific SDK, focuses on integration patterns.

---

## Documents

### Module-Level Caching Trap
**File**: `module-level-caching.md`
**Problem**: SDKs cache event loop at import time, using wrong loop in multi-threaded environments
**Solution**: Delete from `sys.modules` and re-import after setting correct context
**Usage**: Integrating any SDK with module-level state

---

## Quality Standards

- ✅ Document < 300 lines
- ✅ Code examples < 50 lines
- ✅ English only
- ✅ Debugging time > 30 minutes
- ✅ Reusable in other projects

---

## Related Categories

- `general/async-patterns/` - Async programming patterns
- `project-specific/` - Project-specific SDK implementations

---

## Version

- **Created**: 2026-03-16
- **Version**: 1.0
