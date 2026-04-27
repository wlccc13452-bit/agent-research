# validate SKILL

## Trigger
- User runs `/validate`
- Before marking any feature as complete
- After implementing code changes

## Purpose
Execute Auditor-led quality gate validation with Stop-on-Failure behavior.

## Inputs
- Optional: `scope` (backend/frontend/cross-layer)
- Optional: `verbose` (show detailed output)

## Action

### Step 1: Determine Validation Scope
If no scope provided, analyze recent changes:
- Check modified files in git status
- Categorize as backend/frontend/cross-layer
- If cannot determine, run all validations

### Step 2: Execute Backend Validation (if backend or cross-layer)
```bash
cd backend
uv run ruff check .
uv run mypy .
uv run pytest
```

**Stop on first failure** - Do not proceed to next command if current fails.

### Step 3: Execute Frontend Validation (if frontend or cross-layer)
```bash
cd frontend
npm run lint
npm run build
```

**Stop on first failure** - Do not proceed to next command if current fails.

### Step 4: Report Results
Output format:
```
✅ PASSED: [validation name] - [duration]
❌ FAILED: [validation name] - [error summary]
   Fix required: [specific action]
```

## Validation

### Success Criteria
- All selected validation commands pass without errors
- No warnings treated as errors (based on project config)
- All tests pass

### Failure Handling
1. **STOP immediately** on first failure
2. Report the exact error with file:line reference
3. Suggest specific fix action
4. Do NOT proceed to next validation step
5. Do NOT mark task as complete

## Output

### On Success
```
✅ VALIDATION PASSED

Scope: [backend/frontend/cross-layer]

Results:
- Backend lint: ✅ PASSED (2.3s)
- Backend typecheck: ✅ PASSED (1.8s)
- Backend tests: ✅ PASSED (5.2s, 12 tests)
- Frontend lint: ✅ PASSED (1.1s)
- Frontend build: ✅ PASSED (8.4s)

Total duration: 18.8s
```

### On Failure
```
❌ VALIDATION FAILED

Failed at: Backend typecheck
File: backend/services/stock_service.py:45
Error: Incompatible return type expected "str", got "None"

Fix required:
- Add explicit return statement for edge case
- Or change return type annotation to Optional[str]

STOPPING - Fix the error and re-run /validate
```

## Integration with Deep-Think Workflow

This command is the **VALIDATE** step in the Deep-Think Workflow:
- **SYNC** → **REFLECT** → **ACT** → **VALIDATE** → **DISTILL** → **ANCHOR**

After validation passes:
1. Proceed to **DISTILL** step (update progress.md and decisions.md)
2. Create session summary
3. Mark task as complete in progress.md

## Related Files
- AGENTS.md: Mandatory Validation Command Baseline section
- BACKEND.md: Backend code standards
- FRONTEND.md: Frontend code standards
