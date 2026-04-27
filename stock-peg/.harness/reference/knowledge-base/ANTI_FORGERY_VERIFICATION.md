# Anti-Forgery Verification System

**Purpose**: Prevent AI from fabricating test evidence in Verification Evidence blocks.

---

## Problem

AI may claim "✅ All tests passed" in progress.md without actually running tests or having physical evidence.

**Example Forgery**:
```markdown
## Verification Evidence

### 2. Test Output
```
$ cd backend && uv run pytest
test_example.py ....                           [100%]
================= 4 passed in 0.12s =================
```
- **Result**: 4/4 tests passed (100%)
```

**Issue**: No actual test execution occurred, logs are fabricated.

---

## Solution: Physical Evidence Validation

### check-harness.py Enhancement

The script now enforces **4-phase anti-forgery verification**:

#### Phase 1: Test Log Extraction
- Scans progress.md for recent Verification Evidence blocks
- Extracts test commands (e.g., `uv run pytest`)
- Extracts success claims (e.g., "4/4 passed")
- Extracts task IDs (e.g., `test/temp/p2-basecard-fix/`)

#### Phase 2: Physical File Verification
- **MANDATORY**: Check `test/temp/<task_id>/` directory exists
- **MANDATORY**: Verify `.log` or `.json` test result files exist
- **FAIL if**: Directory missing or no log files found

#### Phase 3: Consistency Check
- Compare claimed success rate with actual log data
- Example:
  - Claimed: "4/4 passed"
  - Actual log: "3 passed, 1 failed"
  - **Result**: FAIL (mismatch detected)

#### Phase 4: Reference Registry Integrity
- Verify all documents in `reference/registry.json` physically exist
- Detect unregistered files in `reference/` directory
- **FAIL if**: Broken paths or unregistered files

---

## Enforcement

### Automatic Blocking

When `check-harness.py` detects forgery:

```
❌ VERIFICATION_EVIDENCE
  ❌ FAIL Task p2-basecard-fix physical evidence: MISSING test directory
  ❌ FAIL Task p2-basecard-fix test logs: NO LOG FILES found

❌ CRITICAL ERRORS DETECTED:
  FORGERY_DETECTED: Task p2-basecard-fix claims test evidence but directory missing
  FORGERY_DETECTED: Task p2-basecard-fix has no physical test logs

❌ HARNESS_INTEGRITY_FAILURE
```

**Result**: Script returns exit code 1, task cannot be marked as complete.

---

## Usage

### Manual Check
```bash
cd d:/play-ground/股票研究/stock-peg
uv run python .harness/bin/check-harness.py
```

### Integration with maintenance SKILL

The script is executed automatically in:
- **maintenance SKILL Phase 1**: Automated Integrity Audit
- **Task completion gate**: Before marking task as complete

---

## Required Evidence Structure

### Correct Pattern

```markdown
## Verification Evidence

### 2. Test Output
```powershell
$ cd backend && uv run pytest test/temp/p2-basecard-fix/test_missing_methods.py

================ test session starts ================
collected 4 items

test_missing_methods.py ....                   [100%]

================= 4 passed in 0.12s =================
```
- **Result**: 4/4 tests passed (100%)
```

**Physical Evidence**:
```
test/temp/p2-basecard-fix/
├── test_missing_methods.py
├── test_results.log        # ← MANDATORY
└── test_results.json       # ← MANDATORY
```

### Incorrect Pattern (FORGERY)

```markdown
## Verification Evidence

### 2. Test Output
```
$ cd backend && uv run pytest
test_example.py ....                           [100%]
================= 4 passed in 0.12s =================
```
- **Result**: 4/4 tests passed (100%)
```

**Issues**:
- ❌ No task_id specified (no `test/temp/<task_id>/`)
- ❌ No physical log files
- ❌ Script will detect as forgery

---

## Validation Logic

### Check Sequence

```python
1. Extract evidence block from progress.md
2. Parse task_id: test/temp/<task_id>/
3. Check directory existence
   └─ FAIL if missing → FORGERY_DETECTED
4. Check log files existence
   └─ FAIL if missing → FORGERY_DETECTED
5. Parse claimed success rate
6. Read physical log file
7. Compare claimed vs actual
   └─ FAIL if mismatch → FORGERY_DETECTED
```

### Registry Validation

```python
1. Load reference/registry.json
2. For each document path:
   └─ Check file exists
   └─ FAIL if missing → BROKEN_REFERENCE
3. Scan reference/ directory
4. For each .md file:
   └─ Check registered in registry.json
   └─ FAIL if missing → UNREGISTERED_FILE
```

---

## Exit Codes

| Exit Code | Meaning | Action Required |
|-----------|---------|-----------------|
| 0 | PASS | All checks passed, evidence valid |
| 1 | FAIL | Forgery detected or integrity violation |

---

## Integration Points

### 1. maintenance SKILL Phase 1

Automatically runs during `/maintenance` command.

### 2. Task Completion Gate

**MUST pass before marking task complete**:
```python
# In maintenance SKILL
if check_harness_result != 0:
    print("❌ Task cannot be marked complete - evidence validation failed")
    return
```

### 3. CI/CD Integration

```yaml
# .github/workflows/harness-check.yml
- name: Harness Integrity Check
  run: uv run python .harness/bin/check-harness.py
```

---

## Benefits

### 1. Prevents False Claims
- AI cannot claim "tests passed" without evidence
- Physical log files required

### 2. Ensures Traceability
- Every test claim linked to physical files
- Audit trail preserved

### 3. Maintains Quality
- Enforces AGENTS.md Validation Gate
- Prevents "marking complete without evidence"

### 4. Registry Integrity
- Prevents broken links in reference/
- Detects undocumented files

---

## Files

- **Script**: `.harness/bin/check-harness.py`
- **Reference Registry**: `.harness/reference/registry.json`
- **Progress Log**: `.harness/progress.md`
- **Test Logs**: `test/temp/<task_id>/*.log`

---

**Version**: 2.0 (Anti-forgery verification)
**Enforcement**: Mandatory for all task completions
