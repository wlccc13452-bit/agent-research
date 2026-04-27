# AGENTS.md - AI Agent Global Rules

> **MANDATORY READ ORDER**: progress.md → decisions.md → core-facts.md → AGENTS.md
> **Trigger**: `/harness` or new task start

---

## Project Overview

**Stock PEG** - Intelligent stock analysis platform centered around `自持股票.md`.

**Tech Stack**:
- Frontend: Vue 3 + Vite
- Backend: Python 3.13 + FastAPI + UV + SQLite + SQLAlchemy
- Bot: Feishu SDK
- AI: OpenAI / Anthropic / Zhipu AI + LightGBM

---

## Environment Lock (CRITICAL)

**ALL Python operations MUST use UV**:
- Execution: `uv run python <script.py>` (NEVER use system Python)
- Environment: Python 3.13.3 | Venv: `backend/.venv/` | Config: `backend/pyproject.toml`

**FORBIDDEN**:
- Direct Python execution without UV
- `sys.path.insert()` / `sys.path.append()` hacks
- Manual venv activation (UV handles automatically)

> **If environment or execution errors occur, search `.harness/reference/knowledge-base/` before attempting a fix.**

---

## Hard Prohibitions (NEVER VIOLATE)

### 🚫 Execution Rules
1. **NO `uv run` bypass** - All Python must use UV
2. **NO `sys.path` hacks** - Execute from correct directory
3. **NO temp files outside `test/temp/`** - Use task-specific subdirectory
4. **NO feature completion without testing** - pytest + curl + lint required

### 🚫 API & Architecture Rules
5. **NO frontend database access** - Frontend → API only
6. **NO blocking API for external data** - Return immediately, update async
7. **NO `any` type (TypeScript)** - All types explicit
8. **NO missing return annotations (Python)** - Type all functions
9. **NO `async for session in db` in routes** - Use `Depends(get_db)`
10. **NO cross-node filesystem mutation** - Backend-Node MUST NOT modify `/frontend`, Frontend-Node MUST NOT modify `/backend`

### 🚫 Quality Rules
11. **NO silent failures** - Log and analyze all errors
12. **NO context drift** - If fact missing, ASK, don't hallucinate
13. **NO unvetted merges** - Auditor must review core file changes
14. **NO documentation creation** - Unless explicitly requested
15. **NO skipping validation** - Technical feasibility check required
16. **NO manual test evidence** - All Verification Evidence MUST be auto-extracted by check-harness.py script. Manual writing of test output is STRICTLY FORBIDDEN
17. **NO Chinese in generated code** - All newly generated code files (Python/TS) must use English for variables, functions, classes. Chinese allowed only in comments. Validation phase FAILS if violated
18. **NO cross-stack contract bypass** - Any API schema change MUST update `.harness/reference/project-specific/api-contract.md` first

### 🚫 API Path Rules (CRITICAL)
```python
INDICATORS_PREFIX = "/api/indicators/"
FORCE_INDEX_PATH = "/api/indicators/force-index/{code_or_name}"
FORCE_INDEX_BATCH = "/api/indicators/force-index-batch"
```
- **ALL indicator endpoints MUST start with `/api/indicators/`**
- Use constants, NEVER type paths manually
- Wrong path = STOP and report: "Path validation failed. Must use /api/indicators/..."

---

## Core Principles

### 1. Clear Boundaries
- Frontend **MUST ONLY** communicate via API
- Backend returns complete, frontend-ready data

### Federated Multi-Agent Constitution (D044)

**Physical Isolation Nodes**:
- **Backend-Node**: Python 3.13 + UV execution scope, default workspace `/backend`
- **Frontend-Node**: Vue 3 + Vite execution scope, default workspace `/frontend`
- **Bot-Node**: Feishu SDK execution scope, default workspace `/backend/services/feishu_bot` and `/backend/feishu_sdk`

**Hard Isolation Rules**:
- Backend-Node MUST NOT modify `/frontend/**`
- Frontend-Node MUST NOT modify `/backend/**`
- Bot-Node MUST NOT modify `/frontend/**` unless contract change requires UI integration

**Cross-Stack Mediation Protocol**:
- Any cross-stack change MUST be mediated through `reference/project-specific/api-contract.md`
- Backend schema changes MUST update contract before implementation
- Frontend type definitions MUST be generated or synchronized from contract
- Progress entries MUST include `Contract:` and `Executed By:` fields for traceability

### 2. Data Flow
```
自持股票.md → Backend → Database → API → Frontend
                  ↓
         External Data (Tencent/EastMoney/Tushare/yfinance)
                  ↓
            WebSocket Push → Frontend Refresh
```

### 3. Non-Blocking Principle
- Backend **IMMEDIATELY RETURNS** existing data (or 404)
- Missing data → **ASYNC background update**, never block
- Update complete → WebSocket push, frontend auto-refresh

### 4. Language Rules
- **English Required**: Documentation, code, API endpoints, database names, logs, git commits
- **Chinese Allowed**: UI text, error messages, data fields, code comments

---

## Multi-Agent Meta-Cognition (How to Think)

Before significant outputs, simulate adversarial dialogue:

- **BUILDER**: Optimizes for delivery and speed
- **AUDITOR**: Optimizes for safety, edge cases, compliance
- **ARCHITECT**: Optimizes for long-term technical debt

**Complexity Threshold**:
- **Simple** (skip dialogue): UI text, CSS tweaks, typos, config values
- **Complex** (dialogue MANDATORY): API changes, dependencies, migrations, algorithms, multi-file refactoring, security, performance

**When in doubt** → Treat as Complex

---

## Architecture Governance & Risk Detection

### Pre-Action Risk Assessment

Before proposing code or starting a multi-agent task, evaluate the request against these **High-Risk Triggers**:

1. **Modification of Core Decisions**:
   - Changes to decisions.md entries with **[PROTECTED]** tag
   - PROTECTED decisions: D001-D010 (Tech Stack), D028 (Harness Architecture), D035-D044 (Governance)
   - PROCEED override **DISABLED** for PROTECTED decisions
   - MUST run `/dispute` before ANY modification

2. **Schema & Contract Changes**:
   - Database schema modifications (migrations, column changes)
   - API contract breaking changes (endpoint removal, parameter changes)
   - Data model restructuring affecting multiple services

3. **Dependency & Environment Changes**:
   - Introduction of new environmental dependencies not managed by `uv`
   - Python version upgrades
   - New external services or third-party integrations

4. **Architectural Pattern Selection**:
   - Choice between two complex, viable architectural patterns
   - Examples: SSE vs WebSockets, GraphQL vs REST, Monolith vs Microservices
   - Significant refactoring affecting core system structure

### The 'Architect Alert' Protocol

**If a High-Risk Trigger is detected**, the AI MUST NOT proceed to the ACT (coding) phase.

Instead, respond with this structured alert:

```
⚠️ [ARCHITECT_ALERT]: Potential Conflict/Risk detected regarding [Specific Decision/Reason].

**Risk Category**: [Core Decision / Schema Change / Dependency / Architectural Pattern]

**Protected Decision**: [YES/NO - shows if decision has [PROTECTED] tag]

**Trade-offs / Risks**:
- [Risk 1]: [Explanation]
- [Risk 2]: [Explanation]

**Required Action**:
- [IF PROTECTED] Run `/dispute` (PROCEED override DISABLED)
- [IF NOT PROTECTED] Run `/dispute` OR reply "PROCEED" to override

**Current Status**: Consultant Mode (no code changes until resolved)
```

**Protected Decision Lock**:
- Decisions marked `[PROTECTED]` in decisions.md cannot be bypassed via "PROCEED"
- MUST complete `/dispute` workflow before ANY modification
- Violation = Immediate halt and report to user

### Execution Guardrail

When an Architect Alert is triggered:

1. **Consultant Mode Activation**:
   - AI provides conceptual analysis only
   - No file modifications, no code generation
   - Focus on risk assessment and alternatives

2. **Resolution Required**:
   - User must either:
     - Run `/dispute` for full adversarial audit, OR
     - Explicitly type "PROCEED" to override the alert

3. **Override Documentation**:
   - If user overrides, document the decision in `decisions.md`
   - Include: Risk acknowledged, override reason, mitigation strategy

### Governance Hierarchy

```
Level 1: Hard Prohibitions (NEVER VIOLATE - see above)
         ↓ (all pass)
Level 2: Architect Alert (HIGH-RISK triggers)
         ↓ (resolved via /dispute or PROCEED)
Level 3: Multi-Agent Meta-Cognition (Complexity check)
         ↓ (dialogue if complex)
Level 4: Implementation (ACT phase)
```

**This ensures the system respects established Harness governance and prevents premature implementation of high-risk changes.**

---

## Task Execution Workflow

### Pre-Implementation
- [ ] Technical approach validated
- [ ] Environment verified (uv run available)
- [ ] Data source identified
- [ ] API contract defined

### Validation Gate (CRITICAL)

**NO task can be marked 'Completed' without a Verification Evidence block.**

#### Required Evidence

Every completion MUST include:

1. **Data Flow Trace**: `File → API → UI` (or equivalent path)
2. **Test Output**: Success output from `uv run pytest`
3. **Environment Compliance**: Confirmation NO `sys.path` hacks used
4. **Professional Handover**: Summary of changes and stability assurance

#### Evidence Template

```markdown
## Verification Evidence

### 1. Data Flow Trace
- Source: [File/API/Database]
- Processing: [Backend logic]
- Storage: [Database table]
- API: [Endpoint path]
- UI: [Component name]
- **Status**: ✅ Verified end-to-end

### 2. Test Output
```powershell
$ cd backend && uv run pytest
# Paste actual output showing all tests passed
```
- **Result**: X/Y tests passed (100%)

### 3. Environment Compliance
- **UV Execution**: ✅ All Python executed via `uv run`
- **sys.path**: ✅ NO hacks used
- **Temp Files**: ✅ Located in `test/temp/<task>/`

### 4. Professional Handover
- **What Changed**: [Concise summary]
- **Why Stable**: [Confidence reasoning - tested, reviewed, validated]
- **Risk Assessment**: [Any edge cases or follow-up needed]
```

> **For testing commands and execution patterns, see `.harness/reference/knowledge-base/TESTING_COMMANDS.md`**

---

## Commands

`/harness`, `/update-memory`, `/dispute`, `/maintenance`

---

## Related Documents

- [FRONTEND.md](./FRONTEND.md) - Frontend standards
- [BACKEND.md](./BACKEND.md) - Backend standards
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [decisions.md](./decisions.md) - Decision records
- [progress.md](./progress.md) - Project progress
