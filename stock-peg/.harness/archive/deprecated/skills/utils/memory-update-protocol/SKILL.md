# Memory Update Protocol

## Purpose
Standardized memory update workflow ensuring cross-session knowledge transfer.

## Trigger Conditions
- Auto-triggered by auto-memory-trigger SKILL
- User invokes `/update-memory`
- User says "done" / "finish" / "session end"
- Major task completion detected

---

## Update Process

### Step 0: Robustness Check
Before starting, ensure all required files exist. If not, create them with default headers.
- **Location**: `.harness/progress.md`
  - Default: `# Project Progress\n\n## Recent Completions\n\n## Pending Tasks\n`
- **Location**: `.harness/decisions.md`
  - Default: `# Technical Decisions\n\n`
- **Location**: `.harness/memory/session-summaries/` (directory)
  - Ensure directory exists.

### Step 1: Update progress.md
Location: `.harness/progress.md`

Add entry under "Recent Completions":
```markdown
### YYYY-MM-DD
- [x] Completed task description
- [ ] Task in progress (if any)
```

### Step 2: Update decisions.md (if new decisions)
Location: `.harness/decisions.md`

Add new decision:
```markdown
### D0XX: Decision Title
- **Date**: YYYY-MM-DD
- **Decision**: Specific decision content
- **Reason**:
  - Reason 1
  - Reason 2
- **Alternatives**: Rejected alternatives
- **Impact**: Project impact (if any)
```

### Step 3: Create Session Summary
Location: `.harness/memory/session-summaries/YYYY-MM-DD-brief-description.md`

Template:
```markdown
# Session: YYYY-MM-DD - Brief Description

## Completed Tasks
- Task 1
- Task 2

## Closure Evidence (MANDATORY for feature/bug fix)

### 1. Verified Data Path (Source → UI)
- Source: [Data origin]
- Processing: [Backend logic]
- Storage: [Database table]
- API: [Endpoint path]
- UI: [Component]
- **Status**: ✅ Verified OR ❌ Blocked at [step]

### 2. Validation Results
- **pytest**: [Result]
- **curl**: [API test result]
- **Lint**: [Result]
- **Status**: ✅ Passed OR ❌ [failure]

### 3. Non-Blocking Async Flow
- **API Response Time**: [Time]
- **Background Tasks**: [Description]
- **User Experience**: [Description]
- **Status**: ✅ Confirmed OR ❌ [issue]

## Key Decisions
- Decision 1: Brief description

## Issues Encountered
- Issue 1: Solution applied

## Next Steps
- Pending task 1
- Question to resolve

## Files Modified
- path/to/file1
- path/to/file2
```

**Note**: Closure Evidence block is MANDATORY for all feature completions and bug fixes. See `.harness/reference/project-specific/workflows/WORKFLOWS.md` for detailed template.

---

## When to Update core-facts.md

Only update in these situations:
1. Tech stack has permanent change
2. Project positioning has major adjustment
3. User explicitly requests preference change
4. New eternal fact discovered (e.g., port conflict resolution)

---

## Compression Triggers

### Progress.md Compression
- When > 200 lines → Archive old entries to `memory/archives/progress-history.md`

### Session Summaries Compression
- When > 7 files in `session-summaries/` → Create weekly summary in `memory/summaries/weekly-YYYY-WXX.md`

### Decisions.md Deduplication
- When > 50 entries → Review and deduplicate similar decisions

---

## Example Workflow

```
[Session End Triggered]

1. Check for new decisions → Found: D015
2. Check for completion status → Feature complete
3. Update progress.md:
   - Add "Force Index trend analysis complete"
4. Update decisions.md:
   - Add D015: Use 5-day trend analysis
5. Create session summary:
   - 2026-03-13-force-index-enhancement.md

Memory update complete.
```

---

## Notes

1. Don't over-record, only record important information
2. Keep concise, avoid redundancy
3. Use English for all SKILL files and documentation
4. Use Chinese for user-facing messages and reports
5. Ensure git commit includes memory updates
