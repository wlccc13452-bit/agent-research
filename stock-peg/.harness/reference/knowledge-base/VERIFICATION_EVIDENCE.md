# Verification Evidence Guide

**Priority**: Critical
**Applicable Prohibition**: AGENTS.md Rule #15
**Last Updated**: 2026-03-19

---

## Origin & Enforcement

**Source**: AGENTS.md Validation Gate section
**Enforcement**: Prohibition #15 (NO manual test evidence)
**Why Critical**: Prevents marking tasks complete without concrete proof. Violation = system integrity failure.

---

**Purpose**: Harness Engineering validation process for task completion.

---

## Mandatory Components

### 1. Data Flow Trace
Document complete path: `Source → Processing → Storage → API → UI`

### 2. Test Output
Include actual pytest output with success count.

### 3. Environment Compliance
- [ ] All Python via `uv run`
- [ ] NO `sys.path` hacks
- [ ] Temp files in `test/temp/<task>/`

### 4. Professional Handover
- **What Changed**: Summary
- **Why Stable**: Confidence reasoning
- **Risk Assessment**: Low/Medium/High

---

## Complete Example

```markdown
## Verification Evidence

### 1. Data Flow Trace
- Source: 自持股票.md
- Processing: HoldingsParser.parse()
- Storage: stock_holdings table
- API: GET /api/holdings
- UI: HoldingsTable.tsx
- **Status**: ✅ Verified

### 2. Test Output
```
$ cd backend && uv run pytest
test_missing_methods.py ....                   [100%]
================= 4 passed in 0.12s =================
```

### 3. Environment Compliance
- **UV Execution**: ✅ All via `uv run`
- **sys.path**: ✅ NO hacks
- **Temp Files**: ✅ test/temp/p2-basecard-fix/

### 4. Professional Handover
- **What Changed**: Added helper methods to BaseCardBuilder
- **Why Stable**: 4/4 tests passed, backward compatible
- **Risk Assessment**: Low risk
```

---

**Gate**: Incomplete evidence = task NOT complete
**Decision Link**: D035
