# Task Execution Standards

**Priority**: Critical
**Applicable Prohibition**: AGENTS.md Prohibition #15
**Project**: Stock PEG
**Last Updated**: 2026-03-18
**Purpose**: Comprehensive standards for task execution, validation, and closure verification

---

## 1. Mandatory Verification & Validation

**Before implementing ANY solution, MUST perform**:
- **Technical Validation**: Verify technical approach feasibility
- **Environment Check**: Confirm required dependencies and configurations
- **Data Verification**: Validate data availability and correctness

**Validation Methods**:
1. **Code Verification**: Run linters, type checkers, tests
2. **API Testing**: Use `curl` or test scripts to verify endpoints
3. **Integration Testing**: Verify component interactions work correctly
4. **Performance Testing**: Check response times and resource usage

---

## 2. Python Environment for Server Operations

**When executing Python code in server context**:

**Environment Path**: `backend\.venv\Scripts\python.exe`  
**Package Manager**: UV (mandatory, no exceptions)

**Execution Patterns**:
```powershell
# ✅ CORRECT: Use UV to run Python scripts in backend
Set-Location backend
uv run python ../test/temp/<task>/script.py

# ✅ CORRECT: Use UV from project root
uv run python test/temp/<task>/script.py

# ✅ CORRECT: Use UV for all Python operations
uv run ruff check .
uv run mypy .
uv run pytest

# ❌ WRONG: Direct Python invocation
python <script.py>  # ❌ NEVER do this
..\.venv\Scripts\python.exe <script.py>  # ❌ NEVER do this
```

**CRITICAL: No-Hack Policy for Module Imports**:

❌ **FORBIDDEN Patterns**:
```python
# ❌ NEVER use sys.path hacks in test scripts
import sys
sys.path.insert(0, '/path/to/backend')  # ❌ FORBIDDEN
sys.path.insert(0, '../backend')        # ❌ FORBIDDEN
sys.path.append('/path/to/backend')     # ❌ FORBIDDEN

# ❌ NEVER execute with direct Python
python test/temp/<task>/script.py       # ❌ FORBIDDEN
```

**Rationale**: 
- UV automatically sets PYTHONPATH and activates virtual environment
- sys.path hacks are fragile, platform-specific, and break with directory changes
- UV ensures consistent environment across all machines
- No manual path manipulation needed when using UV correctly

**Why UV?** Automatic venv management, consistent dependency resolution, fast installation

---

## 3. Temporary File Management

**ALL temporary test files and validation scripts MUST be created in**:
- **Location**: `test/temp/<task-specific-subdirectory>/`
- **Purpose**: Keep project structure clean and organized
- **Naming**: Use descriptive subdirectory names (e.g., `test/temp/api-validation/`, `test/temp/feishu-debug/`)

**Examples**:
```
✅ CORRECT:
test/temp/feishu-debug/test_connection.py
test/temp/api-validation/test_endpoints.py
test/temp/data-check/verify_quotes.py

❌ WRONG:
backend/test_script.py  # ❌ Pollutes backend directory
test/test_temp.py       # ❌ No task-specific subdirectory
test/temp/test.py       # ❌ Generic name, no organization
```

**Cleanup**: Delete temporary files after successful validation unless needed for reference.

---

## 4. Validation Workflow

**Standard validation sequence**:
```
1. Create test/temp/<task>/ directory
2. Write validation/test script
3. Execute with UV: cd backend && uv run python ../test/temp/<task>/script.py
4. Analyze results
5. Fix issues if any
6. Re-validate
7. Document results
8. Clean up temporary files (optional)
```

---

## 5. Server-Side Execution Rules (No-Hack Policy)

**CRITICAL**: All test scripts MUST be executed via UV from correct directory.

### Correct Execution Patterns

✅ **From backend directory (RECOMMENDED)**:
```powershell
cd backend
uv run python ../test/temp/<task>/script.py
```

✅ **From project root (ALTERNATIVE)**:
```powershell
uv run python test/temp/<task>/script.py
```

### Forbidden Patterns

❌ **sys.path hacks in test scripts**:
```python
import sys
sys.path.insert(0, '/path/to/backend')  # ❌ FORBIDDEN
sys.path.insert(0, '../backend')        # ❌ FORBIDDEN
```

❌ **Direct Python execution**:
```powershell
python test/temp/<task>/script.py       # ❌ FORBIDDEN
..\backend\.venv\Scripts\python.exe ... # ❌ FORBIDDEN
```

### Server-Side Checklist

**When working with backend/server**:
- ✅ Always use `uv run` for Python execution
- ✅ Always execute from `backend/` or project root
- ✅ Always validate API endpoints with actual requests
- ✅ Always test database operations before deployment
- ✅ Always check environment variables are loaded correctly
- ❌ Never use system Python directly
- ❌ Never use sys.path.insert() or sys.path.append() in test scripts
- ❌ Never skip validation due to time pressure
- ❌ Never create test files outside `test/temp/`

### Why No-Hack Policy?

1. **Consistency**: UV handles PYTHONPATH automatically across all machines
2. **Reliability**: No fragile path manipulations that break with directory changes
3. **Maintainability**: Clear, standardized execution pattern for all scripts
4. **Portability**: Works identically on Windows, Linux, macOS

---

## 6. Ensure System Closure (CRITICAL)

**For ANY refactoring or bug fix, MUST verify complete data flow**:

### Closure Verification Checklist

- [ ] **Source Identified**: Confirmed root cause, not just symptoms
- [ ] **Fix Implemented**: Code changes address the root cause
- [ ] **Data Flow Verified**: Traced data from source to destination
- [ ] **API Contract Validated**: Request/response formats match expectations
- [ ] **Async Handling Correct**: Event loops, threads, callbacks properly managed
- [ ] **Error Handling Complete**: All edge cases have proper error responses
- [ ] **User Feedback Provided**: Toast messages, status updates for UI
- [ ] **Cross-Platform Tested**: Desktop + mobile compatibility verified
- [ ] **Integration Points Checked**: External services, webhooks, WebSocket all functional
- [ ] **Documentation Updated**: Relevant SKILLs and decisions.md updated

### Closure Verification Methods

1. **Trace Data Flow**: Map complete path from user action to system response
   ```
   User Action → Event Handler → Data Processing → Response → User Feedback
   ```

2. **Test Complete Scenarios**: End-to-end testing, not just unit tests
   - Example: For Feishu card interaction, test: mobile tap → SDK event → handler → async task → card send → user sees response

3. **Verify Async Patterns**: Ensure async operations complete successfully
   - Check: event loops, thread communication, async/await chains
   - Validate: callbacks return proper values (e.g., `{"toast": "message"}`)

4. **Validate API Responses**: Test actual HTTP requests/responses
   - Use `curl` for API endpoint validation
   - Verify status codes, response format, error handling

5. **Cross-Platform Testing**: Test on both desktop and mobile
   - UI rendering (e.g., card layouts, input fields)
   - User interactions (e.g., form submissions, button clicks)
   - Error handling (e.g., validation, network failures)

### Closure Failure Penalty

- If ANY closure checkpoint fails, task is INCOMPLETE
- MUST fix all closure issues before marking task as complete
- Document closure verification in session summary

### MANDATORY: Closure Evidence Block

**For EVERY feature completion or bug fix**, create a Closure Evidence block in the session summary:

**Required Components**:
1. **Verified Data Path**: Document complete flow from Source → Processing → Storage → API → UI
2. **Validation Results**: Record pytest results, curl API tests, and lint output
3. **Non-Blocking Async Flow**: Confirm API response time, background tasks, and user experience

**Template**: See `.harness/reference/project-specific/workflows/WORKFLOWS.md` (Output Requirements section)

**Purpose**: Ensures System Closure principle is documented, not just checked. This evidence becomes part of the permanent session record.

### Example: Feishu Card System Closure

```
✅ Source Identified: Mobile error 200671 caused by label format
✅ Fix Implemented: Changed all label from objects to strings
✅ Data Flow Verified: Mobile tap → SDK event → handler → return toast
✅ API Contract Validated: handler returns {"toast": "message"}
✅ Async Handling Correct: Using _run_async_task for business logic
✅ Error Handling Complete: Try-catch with toast error messages
✅ User Feedback Provided: Toast message for every interaction
✅ Cross-Platform Tested: Desktop + mobile card rendering verified
✅ Integration Points Checked: WebSocket + long connection functional
✅ Documentation Updated: D030 decision recorded, progress.md updated
```

### Additional Verification Methods

1. **End-to-End Testing**: Test complete user journey from input to output
2. **API Validation**: Verify all endpoints return expected responses
3. **UI/Notification Check**: Confirm user sees result or error message
4. **Log Verification**: Check logs for complete transaction trace
5. **Cross-Platform Testing**: Test on desktop and mobile (if applicable)

### Example: Feishu Card System Closure Flow

```
User Click (Mobile) 
  → WebSocket Event Received ✅
  → SDK Dispatcher Routes to Handler ✅
  → _on_card_action Extracts Data ✅
  → Async Task Calls Business Logic ✅
  → Card Service Processes Request ✅
  → New Card Sent to User ✅
  → User Sees Result on Mobile ✅
```

### Failure to Ensure Closure = INCOMPLETE TASK

- Must trace complete data flow
- Must verify user receives feedback
- Must document closure verification in session summary

---

## Quick Reference

| Standard | Key Requirement |
|----------|-----------------|
| Validation | Technical + Environment + Data verification before implementation |
| Python Execution | Use `uv run` only, never direct Python |
| Temporary Files | Must be in `test/temp/<task>/` subdirectory |
| Validation Workflow | Create → Write → Execute → Analyze → Fix → Re-validate → Document → Cleanup |
| Server Rules | Always `uv run`, validate APIs, test DB, check env vars |
| System Closure | 10-point checklist + MANDATORY Closure Evidence block in session summary |

---

## Related Documents

- `.harness/AGENTS.md` - Global rules and prohibitions
- `.harness/BACKEND.md` - Backend development standards
- `.harness/memory/core-facts.md` - Environment constraints
