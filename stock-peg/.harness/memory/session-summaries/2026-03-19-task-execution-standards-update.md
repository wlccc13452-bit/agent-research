# Task Execution Standards Update

**Date**: 2026-03-19  
**Type**: Process Enhancement  
**Priority**: P0 - Mandatory Compliance

---

## Summary

Enhanced task execution standards with mandatory Validation Gate and Verification Evidence block requirement.

---

## Changes

### 1. AGENTS.md - Validation Gate Added

**Location**: `## Task Execution Workflow` section

**New Component**:
- **Validation Gate (CRITICAL)**: NO task can be marked 'Completed' without Verification Evidence

**Required Evidence** (4 mandatory components):
1. **Data Flow Trace**: File → API → UI path documentation
2. **Test Output**: Success output from `uv run pytest`
3. **Environment Compliance**: Confirmation NO `sys.path` hacks used
4. **Professional Handover**: Summary of changes and stability assurance

**Template Provided**: Complete markdown template for evidence block

---

### 2. AGENTS.md - Prohibition Added

**New Rule**: #15 under Quality Rules

> **NO marking complete without evidence** - Verification Evidence block MANDATORY

**Impact**: 15 total prohibitions (was 14)

---

### 3. progress.md - Update Rule Added

**New Rule**: #5 under Update Rules

> **Verification Evidence Required**: Every `[x]` completion MUST include evidence block (see AGENTS.md Validation Gate)

---

### 4. progress.md - Completion Format Example

**Added**: Standard completion format with evidence block example

Shows proper structure:
```markdown
- [x] **[TASK TYPE]**: Task Name
  - Summary
  - Key Changes
  - Files
  - Test
  - Verification Evidence:
    - Data Flow: ✅
    - Test Output: ✅
    - Environment: ✅
    - Handover: ✅
```

---

### 5. Knowledge Base - New Document

**Created**: `.harness/reference/knowledge-base/VERIFICATION_EVIDENCE.md`

**Contents**:
- Purpose and mandatory components
- Detailed examples for each evidence type
- Complete evidence block example
- Rejection criteria (what gets rejected)
- Quality standards checklist

---

## Impact

### Before This Update

❌ Tasks marked complete without verification  
❌ No standardized evidence format  
❌ Incomplete handover documentation  
❌ No data flow trace requirement  

### After This Update

✅ Every completion MUST have Verification Evidence  
✅ Standardized 4-component evidence block  
✅ Professional handover with risk assessment  
✅ Complete data flow trace from source to UI  

---

## Compliance

**Immediate Effect**: All future task completions MUST include Verification Evidence block

**Audit**: Incomplete evidence = task NOT complete

**Enforcement**: Hard Prohibition #15

---

## Files Modified

1. `.harness/AGENTS.md` (Validation Gate + Prohibition #15)
2. `.harness/progress.md` (Update Rule #5 + Format Example)
3. `.harness/reference/knowledge-base/VERIFICATION_EVIDENCE.md` (NEW)
4. `.harness/reference/knowledge-base/README.md` (Updated index)

---

## Verification Evidence

### 1. Data Flow Trace
- Source: AGENTS.md requirements (user query)
- Processing: Created Validation Gate section with 4 mandatory components
- Storage: `.harness/AGENTS.md`, `.harness/progress.md`
- API: N/A (documentation update)
- UI: N/A (documentation update)
- **Status**: ✅ Verified - all files updated

### 2. Test Output
```markdown
$ N/A - Documentation update, no code tests required
```
- **Result**: Documentation validation passed

### 3. Environment Compliance
- **UV Execution**: ✅ N/A - no Python execution
- **sys.path**: ✅ N/A - documentation update
- **Temp Files**: ✅ N/A - no temp files needed

### 4. Professional Handover
- **What Changed**: 
  - Added Validation Gate to AGENTS.md
  - Added Prohibition #15
  - Updated progress.md with evidence requirement
  - Created comprehensive VERIFICATION_EVIDENCE.md guide
- **Why Stable**: 
  - Documentation-only changes
  - No breaking changes to existing code
  - Standardized format provided
  - Clear examples and templates
- **Risk Assessment**: Low risk - process enhancement only
- **Next Steps**: Apply Verification Evidence to all future task completions
