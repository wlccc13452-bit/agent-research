# Auto Memory and Session Summary / SKILL.md

## Skill Name
auto-memory-and-summary

## Description
Automatically detect session end and update memory files (progress.md, decisions.md) plus write session summary to maintain project knowledge continuity.

## Trigger Phrases
- "done"
- "finish"
- "next"
- "session end"
- "summarize"
- "update memory"
- "auto summary"
- "/update-memory"

## Mandatory Read Order (CRITICAL – Always First)
**MUST read these files before ANY action:**
1. `.harness/memory/core-facts.md` - Eternal facts & environment constraints
2. `.harness/decisions.md` - Existing technical decisions (avoid duplicates)
3. `.harness/progress.md` - Current project completion status
4. `.harness/AGENTS.md` - Global rules, prohibitions, language requirements

---

## Step-by-Step Execution (Strict Order)

### Phase 1: Session Summary Generation
1. **Review current session work**
   - List all tasks completed in this session
   - Identify new features implemented
   - Note any bugs fixed
   - Record test results

2. **Extract technical decisions**
   - Identify new decisions made during session
   - Check if similar decisions already exist in `decisions.md`
   - Format decision using template:
     ```markdown
     ### D0XX: [Decision Title]
     - **Date**: YYYY-MM-DD
     - **Decision**: [Specific decision content]
     - **Reason**:
       - Reason 1
       - Reason 2
     - **Impact**: [Project impact, if any]
     ```

### Phase 2: Memory File Updates
3. **Update progress.md**
   - Navigate to "Recent Completions" section
   - Add new entry under current date:
     ```markdown
     ### YYYY-MM-DD
     - [x] Completed task 1
     - [x] Completed task 2
     - [ ] Task in progress (if any)
     ```
   - Update module completion percentages if applicable
   - Update "Next Steps" if priorities changed

4. **Append to decisions.md**
   - Add new technical decisions (if any)
   - Use next available decision number (D0XX)
   - Avoid duplicates by checking existing entries

### Phase 3: Session Summary File
5. **Create session summary file**
   - Path: `.harness/memory/session-summaries/YYYY-MM-DD.md`
   - Template structure:
     ```markdown
     # Session Summary - YYYY-MM-DD
     
     ## Completed Tasks
     - [Task 1 description]
     - [Task 2 description]
     
     ## Technical Decisions
     - [Decision D0XX: brief description]
     
     ## Lessons Learned
     - [Insight 1]
     - [Insight 2]
     
     ## Files Modified
     - `path/to/file1.ts`
     - `path/to/file2.py`
     
     ## Next Steps
     - [Pending task 1]
     - [Pending task 2]
     ```

### Phase 4: Logging and Confirmation
6. **Log summary generation**
   - Generate unique `trace_id` (format: `summary-YYYYMMDD-HHMMSS`)
   - Log key metrics:
     ```
     [INFO] [{trace_id}] Session summary generated
     [INFO] [{trace_id}] Tasks completed: X
     [INFO] [{trace_id}] Decisions added: Y
     [INFO] [{trace_id}] Files modified: Z
     ```

7. **Output confirmation**
   - Display: "Session summarized and memory updated. Ready for next task."
   - List updated files for transparency

---

## Prohibitions (Hard Rules – Never Violate)

### Memory Management
- ❌ NEVER skip reading mandatory files before updates
- ❌ NEVER duplicate decisions in decisions.md
- ❌ NEVER overwrite existing session summaries (use unique timestamps)
- ❌ NEVER update progress.md without reading current state first

### Language (CRITICAL)
- ❌ NEVER write non-English text in:
  - This SKILL.md file
  - progress.md, decisions.md
  - Session summary files
  - Log messages
- ✅ Chinese ALLOWED in: UI text content references, user-facing messages

### Quality Assurance
- ❌ NEVER proceed without confirming file paths exist
- ❌ NEVER create empty or placeholder session summaries
- ❌ NEVER forget to include trace_id in logs

---

## Allowed Tools
- `read_file` - Read memory files (progress.md, decisions.md, core-facts.md)
- `replace_in_file` - Update progress.md, decisions.md
- `write_to_file` - Create new session summary file
- `list_dir` - Verify directory structure
- `execute_command` - Get current date/time for timestamping

---

## Output Format (Standard Structure)

```
<thinking>
Detecting session end trigger...
Reading mandatory files (core-facts.md, decisions.md, progress.md, AGENTS.md)...
Extracting session accomplishments...
</thinking>

**Step 1:** Review session work → Identified X completed tasks

**Step 2:** Extract technical decisions → Found Y new decisions

**Step 3:** Update progress.md → Added to Recent Completions section

**Step 4:** Append to decisions.md → Added D0XX, D0YY

**Step 5:** Create session summary → `.harness/memory/session-summaries/2026-03-13.md`

**Final:**
- ✅ Session summarized
- ✅ Memory updated (progress.md, decisions.md, session summary)
- ✅ Trace ID: summary-20260313-143022
- Updated files:
  - `.harness/progress.md`
  - `.harness/decisions.md`
  - `.harness/memory/session-summaries/2026-03-13.md`
- Ready for next task
```

---

## Key System Improvements

### 1. Automated Knowledge Capture
- NO manual effort required to update memory
- Consistent format across all sessions
- Prevents knowledge loss between sessions

### 2. Duplicate Prevention
- Mandatory read of decisions.md before appending
- Checks for similar decisions automatically
- Maintains clean decision history

### 3. Traceability
- Every summary has unique trace_id
- Easy to debug and audit session history
- Clear chain of project evolution

### 4. Session Continuity
- Next session starts with updated progress
- Clear record of what was done
- Prevents rework and duplicate efforts

---

## Integration with Other Skills

This skill works closely with:
- `memory-update-protocol` - Delegates detailed update logic
- `harness-loader` - Called at session start to load context
- `full-feature-impl` - Triggers summary at feature completion

---

## Edge Cases

### Case 1: Empty Session
If no meaningful work completed:
- Still create minimal session summary
- Note "Session ended with no major changes"
- Update only if progress.md needs adjustment

### Case 2: Multiple Summaries in One Day
If user triggers summary multiple times:
- Append timestamp to filename: `YYYY-MM-DD-HHMM.md`
- Or append to existing daily summary with clear separator

### Case 3: Missing Files
If mandatory files don't exist:
- Create default template using robustness protocol
- Refer to `memory-update-protocol` for file creation logic

---

## Example Session Summary

```markdown
# Session Summary - 2026-03-13

## Completed Tasks
- Implemented daily watchlist feature with CRUD operations
- Added stock name auto-detection for watchlist
- Fixed stock name mapping loading issue (nested format support)
- Completed comprehensive automated testing (20 test cases, 100% pass rate)

## Technical Decisions
- D012: Daily Watchlist Data Storage - Use SQLite instead of Markdown
- D013: Daily Watchlist Organization - Organize by date only
- D014: Daily Watchlist UI Placement - Display in Holdings page

## Lessons Learned
- Stock name mapping can have multiple formats (direct vs nested)
- Need to support both for backward compatibility
- Test data cleanup is essential for repeatable tests

## Files Modified
- `backend/models/daily_watchlist.py`
- `backend/services/daily_watchlist_manager.py`
- `backend/routers/daily_watchlist.py`
- `frontend/src/services/api.ts`
- `frontend/src/pages/HoldingsPage.tsx`

## Next Steps
- Monitor watchlist usage patterns
- Consider adding sector tags in future
- Optimize query performance for large watchlists
```

---

## Why This Skill Exists

**Problem**: AI agents often forget to update project memory, leading to:
- Lost technical decisions
- Inconsistent progress tracking
- Duplicate work across sessions
- Knowledge fragmentation

**Solution**: Automated memory updates triggered by natural language cues ensure:
- Continuous project knowledge
- Reliable progress tracking
- Clear audit trail
- Zero manual effort

---

## Remember

**This skill is the "closing ceremony" of every session:**
- Captures what was done
- Records why decisions were made
- Prepares context for next session
- Maintains project continuity

**Without it**: Project memory degrades, decisions get lost, progress becomes unclear.

**With it**: Every session builds on the last, knowledge compounds, project stays on track.
