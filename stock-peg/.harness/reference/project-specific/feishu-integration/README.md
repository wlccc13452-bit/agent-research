# Project-Specific: Feishu Integration

This directory contains **Feishu-specific integration knowledge** tied to this project.

---

## Core Principle

**Project-Specific Knowledge**: Tied to business requirements, contains project configuration.

---

## Documents

### Bot Architecture
**File**: `bot-architecture.md`
**Purpose**: Overall Feishu bot integration architecture
**Components**: Webhook router, long connection service, bot service, chat API

### WebSocket Broadcast
**File**: `websocket-broadcast.md`
**Purpose**: Real-time conversation updates in frontend
**Implementation**: Broadcast in both webhook and bot service

### Long Connection Thread Isolation
**File**: `long-connection-thread-isolation.md` (to be created)
**Purpose**: Run long connection in thread-isolated event loop
**Pattern**: See `general/async-patterns/thread-isolation-pattern.md`

---

## Configuration Required

- Feishu app credentials (APP_ID, APP_SECRET)
- Webhook URL configuration
- Bot name and permissions

---

## Quality Standards

- ✅ Document < 400 lines
- ✅ Code examples project-specific
- ✅ English only
- ✅ Debugging time > 30 minutes
- ⚠️ May contain project-specific references

---

## Related Resources

**General Patterns Used**:
- `general/async-patterns/thread-isolation-pattern.md`
- `general/sdk-integration/module-level-caching.md`
- `general/database-patterns/async-sqlalchemy-2.0.md`

---

## Version

- **Created**: 2026-03-16
- **Version**: 1.0
