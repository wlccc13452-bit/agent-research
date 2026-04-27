# core-facts.md - Project Ground Truth

**Purpose**: This document defines the immutable principles, data structures, and business logic of the Stock PEG project.

**Status**: Permanent Reference (Read during `/harness`).

---

## 1. Architectural Pillars

These principles govern every decision made in `decisions.md`:

### 1.1 Async-First Backend
All external data fetching (Tencent, EastMoney, Tushare) must be non-blocking.

### 1.2 Environment Integrity
The project is strictly bound to:
- **Python**: 3.13
- **Package Manager**: UV

### 1.3 Strict Typing
- **TypeScript**: No `any` types
- **Python**: Mandatory return annotations

### 1.4 Indicator Uniformity
All financial indicators must be served via the `/api/indicators/` prefix.

---

## 2. Data Ownership & Flow

```
Source: 自持股票.md (Human-readable markdown)
   ↓
Engine: Backend parses markdown → Updates SQLite database
   ↓
Real-time: WebSocket triggers frontend refresh when background tasks complete
   ↓
UI: React frontend displays data strictly via the FastAPI layer
```

---

## 3. Feishu Integration (PegBot)

PegBot is a Feishu (Lark) chatbot that delivers stock analysis to users via messaging platform.

### 3.1 Architecture
```
feishu_sdk/          # Independent SDK (zero application dependencies)
   ↓ (Protocol-based DI)
services/feishu_bot/ # Application layer (domain logic, card builders)
```

### 3.2 Key Features
- **Real-time stock alerts** via Feishu WebSocket
- **Interactive cards** for stock data visualization
- **Multi-tenant support** with user-specific configurations
- **Indicator integration** (Force Index, PEG ratio, trend analysis)

### 3.3 SDK Independence
- **SDK Layer**: `backend/feishu_sdk/` (fully independent, extractable as standalone package)
- **Application Layer**: `backend/services/feishu_bot/` (domain-specific implementations)
- **Dependency Injection**: Protocol-based DI with 6 Protocol interfaces
- **Backward Compatibility**: Redirect layer in `services/feishu/` for legacy imports

---

## 4. Key Project Constraints

| Category | Technology/Pattern |
|----------|-------------------|
| **Database** | SQLite (Local, lightweight, single-file) |
| **Frontend State** | Zustand (global state) + TanStack Query (server state) |
| **Styling** | Tailwind CSS 4 (utility-first design) |
| **Communication** | English (technical artifacts) / Chinese (UI, user-facing data) |

---

## Implementation Notes

- File location: `.harness/memory/core-facts.md`
- Mandatory read order (AGENTS.md): `progress.md → decisions.md → core-facts.md → AGENTS.md`
