# Update Memory SKILL (Unified)

**Trigger**: User types `/update-memory`, "update memory", "save session", or "session end"
**Purpose**: Automated memory update with intelligent compression. Maintains decisions.md, progress.md, and session summaries with zero manual effort.

## Execution Workflow

### Phase 1: Context Loading (Mandatory)
**CRITICAL**: Read in strict order before any updates:

1. `.harness/memory/core-facts.md` - Eternal facts & style preferences
2. `.harness/decisions.md` - Existing decisions (avoid duplicates)
3. `.harness/progress.md` - Current completion status
4. `.harness/AGENTS.md` - Global rules & prohibitions

**Robustness Check** (Step 0):
- If files missing, create with defaults:
  - `progress.md`: `# Project Progress\n\n## Recent Completions\n\n## Pending Tasks\n`
  - `decisions.md`: `# Technical Decisions\n\n`
  - `memory/session-summaries/`: Create directory if needed

---

### Phase 2: Session Analysis
**Review current session work**:
- Tasks completed (from conversation history)
- Problems encountered & solutions
- Technical decisions made
- Files modified
- Knowledge discovered

**Extract new decisions**:
- Architecture choices
- Technology selections
- Pattern adoptions
- Process changes

**Check for duplicates**: Scan decisions.md for similar decisions before appending.

---

### Phase 3: Memory Updates

#### 3.1: Update progress.md
Navigate to "Recent Completions" section, add entry:

```markdown
### YYYY-MM-DD
- [x] **[TASK TYPE]**: Task Name
  - **Decision**: D0XX - Decision Name (if applicable)
  - **Summary**: One-line description
  - **Key Changes**: Bullet list
  - **Files**: List of modified files
  - **Verification Evidence**: (See AGENTS.md Validation Gate)
```

**Update System State table**:
- Last Validated Commit (if code changed)
- Last Maintenance date
- Session Status

#### 3.2: Append to decisions.md
For each NEW decision, use template:

```markdown
### D0XX: Decision Title
**Date**: YYYY-MM-DD
**Summary**: One-line summary
**Details**: `.harness/reference/path/to/details.md` (if applicable)

**Rationale**:
- Reason 1
- Reason 2

**Impact**:
- Impact 1
- Impact 2

**Files**:
- `path/to/file1.py`
- `path/to/file2.ts`
```

**Deduplication**: Check for keywords in existing decisions before adding.

#### 3.3: Write Session Summary
Create/append `.harness/memory/session-summaries/YYYY-MM-DD-topic.md`:

```markdown
# Session Summary: [Topic]

**Date**: YYYY-MM-DD
**Session Type**: [Feature/Bugfix/Refactor/Documentation]

---

## Executive Summary
[2-3 sentences on what was accomplished]

---

## Session Tasks
[List of completed tasks with details]

---

## Key Decisions
- **D0XX**: Decision Title - Brief rationale
- **D0YY**: Decision Title - Brief rationale

---

## Technical Changes
[Architecture changes, new patterns, modifications]

---

## Files Modified
- `path/to/file1.py` - Brief description
- `path/to/file2.ts` - Brief description

---

## Lessons Learned
[Insights, gotchas, best practices discovered]

---

## Recommendations
[Next steps, follow-up tasks, monitoring needs]

---

## Verification Evidence
### Data Flow Trace
- Source: [Where data originated]
- Processing: [What transformations occurred]
- Storage: [Where data was stored]
- **Status**: ✅/❌

### Test Output
[Paste relevant test results]

### Environment Compliance
- **UV Execution**: ✅ All Python via `uv run`
- **sys.path**: ✅ NO hacks used
- **Temp Files**: ✅ Located in `test/temp/<task>/`

### Professional Handover
- **What Changed**: [Summary]
- **Why Stable**: [Confidence reasoning]
- **Risk Assessment**: [Risk level and mitigation]
```

**Append vs Create**:
- If file exists for today with different topic: Append new section
- If file exists for today with same topic: Update existing content
- If no file: Create new file

---

### Phase 4: System Memory (Optional)
**When to use update_memory tool**:
- Cross-project technical patterns
- Platform-specific issues (e.g., Windows URL handling)
- Recurring bugs with solutions
- SDK integration patterns

**Format**: Title + concise paragraph (< 150 words)

**Example**:
```
Title: Windows execute_command URL encoding
Content: Windows execute_command fails with exit code 3 for quoted URLs containing Chinese characters. Use unquoted URLs or stock codes instead. Example: curl -s http://localhost:8000/api/indicators/中煤能源 works, quoted version fails.
```

---

### Phase 5: Intelligent Compression (Auto-Trigger)

#### 5.1: Progress Archive
**Trigger**: `progress.md` > 200 lines

**Action**:
1. Keep last 30 days in "Recent Completions"
2. Move older entries to `.harness/memory/archives/progress-archive-YYYY-QN.md`
3. Add archive link to progress.md:
   ```markdown
   ## Archived Completions
   - [2026 Q1 Archive](./archives/progress-archive-2026-Q1.md)
   ```

#### 5.2: Session Summary Compression
**Trigger**: > 7 files in `session-summaries/`

**Action**:
1. **Days 0-7**: Keep detailed summaries
2. **Days 8-30**: Compress to weekly summary
   - Create `memory/summaries/weekly-summary-YYYY-WNN.md`
   - Extract: key tasks, decisions, files modified
   - Remove individual day files
3. **Days 31+**: Compress to monthly summary
   - Create `memory/summaries/monthly-summary-YYYY-MM.md`
   - Extract: critical decisions, major milestones
   - Remove weekly summaries

#### 5.3: Decision Deduplication
**Trigger**: `decisions.md` > 50 entries

**Action**:
1. Detect similar decisions by keywords
2. Group related decisions
3. Add cross-reference links:
   ```markdown
   ### D005: API Design Pattern
   See also: D008 (API versioning), D012 (API security)
   ```

---

### Phase 6: Final Verification
**Checklist**:
- ✅ Mandatory files read (core-facts.md, decisions.md, progress.md, AGENTS.md)
- ✅ progress.md updated with completion entry
- ✅ decisions.md updated (if new decisions)
- ✅ Session summary written
- ✅ System memory updated (if applicable)
- ✅ Compression executed (if triggered)
- ✅ No duplicates in decisions.md
- ✅ English only in all documentation files

---

## Output Format

```
## Phase 1: Context Loading
✅ Read: core-facts.md, decisions.md, progress.md, AGENTS.md

## Phase 2: Session Analysis
- Tasks completed: X
- New decisions: Y
- Files modified: Z

## Phase 3: Memory Updates
✅ progress.md: Added completion entry
✅ decisions.md: Added D0XX, D0YY
✅ Session summary: .harness/memory/session-summaries/YYYY-MM-DD-topic.md

## Phase 4: System Memory
✅ Created: [Title] (ID: XXXXXX)

## Phase 5: Compression
⚠️ Progress: 210 lines → Archived to progress-archive-2026-Q1.md
✅ Sessions: 8 files → Compressed to weekly-summary-2026-W12.md

## Phase 6: Verification
✅ All checks passed

✅ Memory Update Complete
- Updated files: progress.md, decisions.md, session summary
- System memory: 1 entry created
- Compression: Progress archived, sessions compressed
- Ready for next task
```

---

## Prohibitions (Hard Rules)

### Memory Management
- ❌ NEVER skip reading mandatory files
- ❌ NEVER duplicate decisions in decisions.md
- ❌ NEVER overwrite existing session summaries (append/update)
- ❌ NEVER update progress.md without reading current state
- ❌ NEVER create multiple session files for same date+topic

### Language (CRITICAL)
- ❌ NEVER write non-English text in documentation files
- ✅ Chinese ALLOWED in: UI text references, user-facing messages

### Quality
- ❌ NEVER create empty or placeholder summaries
- ❌ NEVER compress without preserving essential information
- ❌ NEVER delete archived files (move to archives/)

---

## Compression Retention Policy

| Time Range | Detail Level | What to Keep |
|------------|--------------|--------------|
| **0-7 days** | Full detail | All tasks, decisions, files, issues |
| **8-30 days** | Compressed | Key tasks, major decisions, critical files |
| **31-90 days** | Weekly summary | Milestones, major decisions, blockers |
| **> 90 days** | Monthly summary | Critical decisions, major releases |

---

## Allowed Tools

- `read_file` - Read memory files
- `replace_in_file` - Update existing files
- `write_to_file` - Create new session summaries
- `update_memory` - Create system-level memories
- `list_dir` - Verify directory structure
- `execute_command` - Get current date/time

---

## Edge Cases

### Case 1: Empty Session
If no meaningful work completed:
- Still create minimal session summary
- Note "Session ended with no major changes"
- Update only if progress.md needs adjustment

### Case 2: Multiple Summaries Same Day
- Append timestamp to filename: `YYYY-MM-DD-HHMM-topic.md`
- Or append to existing daily summary with separator

### Case 3: Missing Files
- Use robustness check defaults
- Create files with minimal templates
- Continue with available context

---

## Why This Skill Exists

**Problem**: AI agents forget to update project memory → lost decisions, inconsistent progress, duplicate work

**Solution**: Automated memory updates → continuous knowledge, reliable tracking, zero manual effort

**Without it**: Project memory degrades, decisions lost, progress unclear

**With it**: Every session builds on the last, knowledge compounds, project stays on track

---

## Related Files

- `.harness/progress.md` - Task tracking
- `.harness/decisions.md` - Decision records
- `.harness/memory/core-facts.md` - Eternal facts
- `.harness/memory/session-summaries/` - Session histories
- `.harness/memory/archives/` - Archived progress
- `.harness/memory/summaries/` - Compressed summaries
