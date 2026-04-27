# Workflows Guide

**Priority**: Standard
**Project**: Stock PEG
**Last Updated**: 2026-03-18
**Purpose**: Detailed workflows for development, testing, and validation

---

## Command Routing Contract

- `/harness` is a context loader command routed by `.codebuddy/rules/harness-loader.mdc`
- `/update-memory` is a memory sync command routed by `.codebuddy/rules/update-memory.mdc`
- `/validate` is an Auditor-led quality gate execution command (Stop on Failure)
- `/dispute` forces a deep adversarial debate between Builder and Auditor on complex logic
- `/check-harness` runs Harness health checks (file completeness, routing integrity, and reference validity)
- `/daily-watchlist` is a feature command routed by `.harness/skills/registry.json` to `.harness/skills/daily-watchlist/SKILL.md`
- Skill discovery source of truth: `.harness/skills/registry.json`
- If command routing fails, run fallback manually with the same ordered file workflow

---

## The "Deep-Think" Workflow (Recursive Loop)

For every task, follow this sequence:

1. **SYNC**: Run `/harness` to load `progress.md` → `decisions.md` → `core-facts.md` → `AGENTS.md`.
2. **REFLECT**: Output internal adversarial dialogue (Builder/Auditor/Architect) - **MANDATORY for complex tasks**.
3. **ACT**: Execute the code/data modification.
4. **VALIDATE**: Run mandatory quality gates (tests, linters, or custom scripts).
5. **DISTILL**: Update `progress.md` and log new decisions in `decisions.md`.
6. **ANCHOR**: Conclude with a specific pointer for the next logical action.

### Complexity Threshold Application

**Apply REFLECT step based on task complexity:**

#### Simple Tasks (May Skip REFLECT)

AI can proceed directly to ACT without adversarial dialogue for:

**Category: UI/Visual Changes**
- Text content updates (button labels, error messages, tooltips)
- CSS adjustments (colors, spacing, font sizes, margins)
- Simple layout tweaks (padding, alignment)

**Category: Documentation**
- Typos and grammar fixes
- Minor clarifications without technical implications
- Section reordering

**Category: Configuration**
- Environment variable value changes (non-sensitive)
- Feature flag toggles
- Simple config parameter updates

**Category: Code Style**
- Variable/function renaming in isolated files
- Import statement reorganization
- Comment additions

**Example - Simple Task**:
```
Task: "Change button text from 'Submit' to 'Save Changes'"
→ Skip REFLECT
→ ACT: Update JSX directly
→ VALIDATE: Visual check
→ Done
```

#### Complex Tasks (REFLECT is MANDATORY)

AI MUST perform adversarial dialogue for:

**Category: API & Backend**
- New API endpoints or GraphQL queries
- Request/response schema modifications
- Authentication/authorization logic changes
- Database schema migrations
- New database tables or columns
- Query optimization or indexing changes

**Category: Dependencies & Architecture**
- Adding new npm packages or Python libraries
- Updating major versions of dependencies
- New MCP server integrations
- Cross-layer refactoring (3+ files affected)
- Module restructuring

**Category: Core Business Logic**
- Trading signal algorithms
- Risk calculation formulas
- Data processing pipelines
- Validation logic for critical data
- State management patterns (Zustand stores)

**Category: Performance & Security**
- Caching strategy implementations
- WebSocket connection handling
- Data encryption/decryption
- Rate limiting logic
- SQL injection prevention

**Category: Breaking Changes**
- Deprecating API endpoints
- Removing features
- Database column deletions
- Breaking UI component API changes

**Example - Complex Task**:
```
Task: "Add new technical indicator endpoint /api/indicators/macd"
→ REFLECT:
  🔧 Builder: "Create new endpoint in main.py, add MACD calculation service."
  🔍 Auditor: "Check AGENTS.md line 306-317 - must use INDICATORS_PREFIX constant. Verify path format."
  🛡️ Architect: "Confirm database schema supports MACD storage. Check if existing indicator pattern should be reused."
→ ACT: Implement with validated approach
→ VALIDATE: pytest, curl test, lint
→ DISTILL: Update progress.md
→ Done
```

### Decision Tree

```
Is task complex? 
├─ YES (see Complex Tasks list)
│  → REFLECT (MANDATORY)
│  → ACT
│  → VALIDATE
│
└─ NO (see Simple Tasks list)
   → ACT (skip REFLECT)
   → VALIDATE (simplified)
```

### Ambiguity Resolution

When uncertain about task complexity:

1. **Default to Complex**: Err on the side of caution
2. **Ask Clarifying Questions**: If user intent is unclear
3. **Consider Impact Radius**: How many files/systems could be affected?
4. **Check Dependencies**: Does change require new packages or migrations?

**Rule of Thumb**: If a mistake would require > 10 minutes to fix, treat as Complex.

---

## Session Workflow (Standard Closed-Loop)

```
Session Start
  ↓
/harness (load context via harness-loader.mdc)
  ↓
[User Request]
  ↓
Execute appropriate SKILL
  ↓
[Work Completed]
  ↓
Trigger memory update (auto or manual /update-memory)
  ↓
├─ Update progress.md (add to Recent Completions)
├─ Add decisions to decisions.md (if any)
└─ Create session summary in memory/session-summaries/
  ↓
Session End
```

---

## Feature Development Workflow

**Quick Steps**:
1. Read progress.md to understand current state
2. Follow `skills/cross-layer/full-feature-impl/SKILL.md`
3. Execute implementation
4. **MANDATORY: Perform thorough testing** (see Testing Requirements below)
5. Update progress.md at completion
6. Add decisions to decisions.md (if any)
7. Create session summary

---

## Testing Requirements (CRITICAL)

**Every new feature MUST pass these tests before marking as complete:**

### 1. API Endpoint Testing

- Use `curl` or similar to test actual API calls
- Verify request/response format matches design
- Test error cases (invalid input, missing data)
- Confirm non-blocking behavior (fast response, no hanging)
- **Create test scripts in `test/temp/<task>/` for complex validations**

### 2. Database Integration Testing

- Verify data is correctly saved/updated/deleted
- Check database session usage (MUST use `db: AsyncSession = Depends(get_db)`, NOT `async for session in db`)
- Confirm transaction commit/rollback works
- **Use `uv run python` for all test script execution**

### 3. Frontend Integration Testing

- UI renders without errors
- Data displays correctly from API
- Loading and error states work
- WebSocket updates (if applicable)

### 4. End-to-End Testing

- Complete user flow works
- Cross-browser compatibility (Chrome, Firefox)
- Mobile responsive (if applicable)

### 5. Technical Validation

- **MUST verify technical approach before implementation**
- Create validation scripts in `test/temp/<task>/`
- Test with `uv run python` in backend context
- Document validation results in session summary

---

## Mandatory Validation Command Baseline

Run validation commands based on changed scope before declaring completion:

### Backend Changes

```bash
cd backend && uv run ruff check .
cd backend && uv run mypy .
cd backend && uv run pytest
```

### Frontend Changes

```bash
cd frontend && npm run lint
cd frontend && npm run build
```

### Cross-Layer Changes

- Run both backend and frontend command sets

### Failure Handling

- If any command fails, task remains incomplete until fixed and re-validated

**FAILURE TO TEST = INCOMPLETE FEATURE**
- If any test fails, feature is NOT complete
- Must fix issues and re-test
- Document test results in session summary

---

## Bug Fix Workflow

**Quick Steps**:
1. Locate issue (frontend/backend/cross-layer)
2. Refer to `ARCHITECTURE.md` to understand data flow
3. Fix following coding standards
4. Verify non-blocking principle
5. Update progress.md + create session summary

---

## Dependency Changes Workflow

1. Backend: Modify `pyproject.toml`, run `uv sync`
2. Frontend: Modify `package.json`, run `npm install`
3. **Commit**: Include `pyproject.toml` / `package.json` AND lock files

---

## Long Task Handling Rule (Anti-Thinking-Limit)

1. When a task requires more than 3 major steps or deep thinking:
   - Break it into small steps
   - After each step, output a compact checkpoint summary
   - Continue automatically unless user explicitly redirects
2. This prevents "Model thinking limit reached" error

---

## Output Requirements

### Standard Output Format

1. **Reflection Block**: Before major code blocks or decisions, show the adversarial reasoning (Builder/Auditor/Architect).
2. **Validation Log**: Provide proof of successful gate execution (test results, lint output, etc.).
3. **Next-Step Anchor**: Always conclude with a specific pointer for the next logical action.
4. Provide result summary first, key changes second, validation evidence last.
5. Include traceable file paths and key line references.
6. Explicitly state assumptions when used.
7. Keep output concise, engineering-focused, and auditable.

### MANDATORY: Closure Evidence Block

**For EVERY feature completion or bug fix**, include a Closure Evidence block in the session summary:

```markdown
## Closure Evidence

### 1. Verified Data Path (Source → UI)
- Source: [Data origin, e.g., 自持股票.md / API / Database]
- Processing: [Backend logic, e.g., parsing, validation, transformation]
- Storage: [Database table/collection]
- API: [Endpoint path, e.g., /api/stocks/{id}]
- UI: [Component displaying data, e.g., StockCard.tsx]
- **Status**: ✅ Verified end-to-end OR ❌ Blocked at [step]

### 2. Validation Results
- **pytest**: [Result, e.g., 5/5 passed, 100% coverage]
- **curl**: [API test result, e.g., GET /api/stocks/601898 → 200 OK, correct JSON]
- **Lint**: [Result, e.g., ruff check passed, mypy no errors]
- **Status**: ✅ All tests passed OR ❌ [describe failure]

### 3. Non-Blocking Async Flow
- **API Response Time**: [e.g., < 100ms, immediate return]
- **Background Tasks**: [e.g., data fetch triggered, WebSocket push scheduled]
- **User Experience**: [e.g., UI shows loading → auto-refresh on data arrival]
- **Status**: ✅ Non-blocking confirmed OR ❌ [describe blocking issue]
```

**Purpose**: Ensures System Closure principle is documented, not just checked. This evidence becomes part of the permanent session record.

**Example**:
```markdown
## Closure Evidence

### 1. Verified Data Path (Source → UI)
- Source: 自持股票.md (sector: 科技, stock: 中煤能源)
- Processing: HoldingsParser.parse_holdings() → validated stock codes
- Storage: stock_holdings table (id, code, name, sector, shares)
- API: GET /api/holdings → returns [{code, name, sector, shares}]
- UI: HoldingsTable.tsx displays in holdings management page
- **Status**: ✅ Verified end-to-end

### 2. Validation Results
- **pytest**: backend/tests/test_holdings.py → 8/8 passed
- **curl**: curl http://localhost:8000/api/holdings → 200 OK, correct JSON array
- **Lint**: ruff check . passed, mypy . no errors
- **Status**: ✅ All tests passed

### 3. Non-Blocking Async Flow
- **API Response Time**: GET /api/holdings → 45ms (immediate return from DB)
- **Background Tasks**: None (data already in DB)
- **User Experience**: UI loads instantly, no loading state needed
- **Status**: ✅ Non-blocking confirmed
```

---

## Quick Reference

| Workflow | Key Steps |
|----------|-----------|
| Deep-Think | SYNC → REFLECT → ACT → VALIDATE → DISTILL → ANCHOR |
| Feature Development | Read progress → Execute SKILL → Test → Update docs |
| Testing | API + DB + Frontend + E2E + Technical validation |
| Bug Fix | Locate → Understand → Fix → Verify → Document |
| Dependencies | Modify config → Sync/Install → Commit with lock files |

---

## Related Documents

- `.harness/AGENTS.md` - Global rules and prohibitions
- `.harness/BACKEND.md` - Backend development standards
- `.harness/FRONTEND.md` - Frontend development standards
- `.harness/reference/project-specific/standards/TASK_EXECUTION_STANDARDS.md` - Task execution standards
