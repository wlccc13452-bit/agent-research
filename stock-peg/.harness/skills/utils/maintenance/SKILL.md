# Maintenance SKILL (System Entropy & Integrity)

**Trigger**: User command `/maintenance` or auto-triggered after 10 tasks.
**Purpose**: Ensure the Harness remains **Concise, Clean, Correct, and Professional** by removing instructional drift and verifying structural integrity.

---

## Core Principles (MANDATORY COMPLIANCE)

### 1. Preserve Architecture Integrity

**3-Layer Knowledge Architecture** (MUST NOT violate):
```
Layer 1 (Core)         Layer 2 (Reference)      Layer 3 (SKILLs)
AGENTS.md         ←→   reference/          ←→   .harness/skills/
decisions.md           ↓ extraction             (automated)
progress.md       knowledge-base/
core-facts.md
(< 300 lines)         (< 400 lines)            (< 200 lines)
```

**Closed-Loop Flow** (MUST maintain):
- Core ↔ Reference: Expansion/Condensation
- Reference → SKILL: Automation (when pattern is executable)
- NO breaking the loop or creating isolated content

### 2. Prevent Content Overlap

**Single Source of Truth**:
- Each piece of knowledge exists in ONE place only
- Core files contain SUMMARIES only (< 300 lines)
- Reference files contain DETAILS only
- NO duplication between layers

**Validation**:
- Before adding to Core: Check if exists in Reference
- Before adding to Reference: Check if exists in Core or another Reference doc
- If overlap found: Consolidate or create pointer

### 3. Maintain Content Hierarchy & Continuity

**Hierarchy Order** (MUST follow):
```
1. AGENTS.md (Global Rules)
   ↓ references
2. decisions.md (Decision Records)
   ↓ references
3. reference/ (Detailed Knowledge)
   ↓ references
4. .harness/skills/ (Executable Workflows)
```

**Continuity Rules**:
- Lower layers MUST reference upper layers (backward link)
- Upper layers MUST point to lower layers (forward link)
- NO orphaned content (every document must be linked)

**Example**:
```markdown
# In AGENTS.md (Layer 1)
**Validation Gate**: See reference/knowledge-base/VERIFICATION_EVIDENCE.md

# In VERIFICATION_EVIDENCE.md (Layer 2)
**Enforced by**: AGENTS.md Prohibition #15
**Decision Link**: D035
```

---

## Execution Workflow

### Phase 1: Automated Integrity Audit (Correct)
- **Action**: Run the technical validator to find broken links, missing files, or bloat.
- **Command**: `uv run python .harness/bin/check-harness.py`
- **Mandate**: If the script returns `FAIL`, the AI must fix the file structure or JSON syntax before proceeding.

### Phase 2: Standardization Audit (Concise)
- **Action**: Scan `AGENTS.md` for industry-standard coding advice.
- **Target**: Delete generic advice (e.g., "Use clear variable names", "PEP 8", "React best practices").
- **Rationale**: The LLM is a senior expert; keep only project-specific constraints (e.g., UV lock, Seismic PSHA logic).

### Phase 3: Knowledge Layering with Quality Gate (Clean)
- **Action**: Identify environment "hacks" or troubleshooting steps in `AGENTS.md`.
- **CRITICAL**: Before moving ANY content to `reference/`, validate against Quality Gate.

#### Phase 3.1: Quality Gate Check
**Enforce**: `.harness/reference/QUALITY-STANDARDS.md` Quality Gate criteria:
- Debugging time > 30 minutes
- Root cause fully analyzed
- Solution validated in production
- NOT found in LLM training (industry standard)

**Reject if**: Generic advice, copy-paste from docs, undocumented hacks.

#### Phase 3.2: Category Selection
**Follow**: `.harness/reference/index.md` Category Classification:
- **General** (< 300 lines): Universal patterns → `general/<category>/`
- **Project-Specific** (< 400 lines): Domain knowledge → `project-specific/<domain>/`
- **Knowledge-Base** (< 200 lines): Troubleshooting → `knowledge-base/`
- **Architecture** (< 200 lines): Decision records → `architecture/`

#### Phase 3.3: Create & Register
1. Create document in selected category
2. Add entry to `registry.json` with: `quality_gate`, `lines`, `created`, `status`
3. Update `registry.json` statistics
4. Replace moved content in `AGENTS.md` with pointer: *"For [Issue], see .harness/reference/[path]"*
5. Enforce `AGENTS.md` < 300 lines

### Phase 4: Knowledge Heat & SKILL Lifecycle (Professional)

#### Phase 4.1: Knowledge Heat Tracking
- **Action**: Update `heat_score` in `registry.json` for all reference documents.
- **Mechanism**:
    1. Scan `progress.md` session history for document access patterns.
    2. For each reference document accessed in current session: `heat_score += 1`.
    3. Update `registry.json` referenceDocuments section with current heat scores.
- **Purpose**: Identify high-value knowledge for SKILL extraction.

#### Phase 4.2: SKILL Extraction Recommendations
- **Trigger**: `heat_score > 5` AND meets SKILL-UPDATE-PROTOCOL.md extraction criteria.
- **Extraction Criteria** (from SKILL-UPDATE-PROTOCOL.md):
    1. Document accessed > 3 times in recent sessions
    2. Solution pattern is executable (has clear steps)
    3. Solution validated in production
    4. Knowledge applicable across multiple features
- **Action**: Add to `[ENTROPY_REPORT]` with recommendation:
    ```markdown
    ### SKILL Extraction Candidates
    - **Document**: [path]
    - **Heat Score**: [current_score]
    - **Recommendation**: Extract to SKILL - meets all extraction criteria
    - **Proposed Command**: /<topic>
    ```

#### Phase 4.3: Dormant SKILL Identification
- **Action**: Identify SKILLs with no usage in last 60 days.
- **Logic**: Calculate days since `last_used` in `registry.json`.
- **Output**: Flag SKILLs > 60 days for "Pruning Proposal" in report.

#### Phase 4.4: Content Linkage Integrity
- **Action**: Validate that migrated content preserves mandatory descriptions.
- **Requirement**: When content moves from AGENTS.md to reference/, must retain:
    1. **Mandatory constraint language** (MUST, MUST NOT, CRITICAL)
    2. **Why this matters** explanation
    3. **Cross-reference** to original AGENTS.md section
- **Validation**: Check each reference document for:
    ```markdown
    ## Origin & Enforcement
    **Source**: AGENTS.md Section [X]
    **Enforcement**: [Prohibition #X / Decision D0XX]
    **Why Critical**: [Reason]
    ```
- **Fix**: If missing, add origin block to ensure governance continuity.

### Phase 5: System Logs Management

#### Phase 5.1: Generate Maintenance Log
- **Action**: Record current maintenance session for audit trail.
- **Output**: `.harness/memory/maintenance-logs/YYYY-MM-DD-maintenance-log.md`
- **Template**:
    ```markdown
    # Maintenance Log - YYYY-MM-DD

    **Trigger**: `/maintenance` (manual/auto)
    **Duration**: X minutes
    **Status**: ✅ Complete | ⚠️ Issues Found

    ---

    ## [SYSTEM_ENTROPY_REPORT]
    [Copy from Phase 1-4 output]

    ---

    ## [LEAN_UPDATE]
    [Summary of AGENTS.md changes]

    ---

    ## [PRUNING_PROPOSAL]
    [SKILLs identified for archival]

    ---

    ## [HEAT_MAP]
    [Top 10 high-value reference documents]

    ---

    ## Actions Taken
    - [List of specific fixes applied]
    - [Files updated]
    - [Archive operations performed]

    ---

    ## Next Maintenance
    - **Recommended**: YYYY-MM-DD (after 10 tasks or 7 days)
    - **Critical Issues**: [List any issues requiring immediate attention]
    ```

#### Phase 5.2: Clean and Archive Logs
- **Action**: Clean and archive system-generated logs based on retention policy.
- **Trigger**: Run automatically at the end of each `/maintenance` execution.

- **Retention Policy**:

| Directory | Keep Period | Action After | Archive Strategy |
|-----------|-------------|--------------|------------------|
| `auditor-reports/` | 90 days | Archive | Merge into quarterly archive |
| `maintenance-logs/` | 60 days | Delete | Low historical value, keep last 10 |

- **Process**:

**Step 1: Scan for Expired Files**
- List all files in `auditor-reports/` and `maintenance-logs/`
- Calculate age based on file creation date (from filename `YYYY-MM-DD-*`)
- Identify files exceeding retention period

**Step 2: Archive Auditor Reports** (90+ days old)
- Group by quarter: Q1 (Jan-Mar), Q2 (Apr-Jun), Q3 (Jul-Sep), Q4 (Oct-Dec)
- Merge into single quarterly archive: `memory/archives/auditor-reports-YYYY-QN.md`
- **Keep**: Executive summary, consensus reached, impact, decision links
- **Remove**: Verbose debate details, intermediate challenges
- **Format**:
    ```markdown
    # Auditor Reports Archive - YYYY QN

    **Period**: YYYY-MM-DD to YYYY-MM-DD
    **Reports Count**: X
    **Generated**: YYYY-MM-DD

    ---

    ## Report 1: [Topic]
    **Date**: YYYY-MM-DD
    **Status**: ✅ CONSENSUS
    **Summary**: [Executive summary]
    **Decision**: D0XX (if applicable)
    **Impact**: [One-line impact]

    ---

    ## Report 2: [Topic]
    ...
    ```
- Delete original files after successful merge

**Step 3: Delete Old Maintenance Logs** (60+ days old)
- Identify files older than 60 days
- Delete immediately (low historical value)
- Keep last 10 log files for recent reference

**Step 4: Update Directory Index**
- If `auditor-reports/README.md` exists, update with archive link
- If `maintenance-logs/README.md` exists, update file count

- **Output**: Add to `[ENTROPY_REPORT]`:
    ```markdown
    ### System Logs Cleanup
    - Auditor reports archived: X files → 1 quarterly archive
    - Maintenance logs deleted: Y files (> 60 days)
    - Disk space recovered: Z KB
    ```

### Phase 6: Archives Integrity Validation
- **Action**: Validate archives directory structure and enforce consistency.
- **Purpose**: Ensure archives follow standardized naming and structure.

#### Phase 6.1: Structure Validation
- **Expected Structure**:
    ```
    memory/archives/
    ├── progress-archive-2026-Q1.md      # Progress records (from /update-memory)
    ├── progress-archive-2026-Q2.md
    ├── auditor-reports-archive-2026-Q1.md  # Audit reports (from /maintenance)
    ├── session-summaries-archive-2026-Q1.md # Optional: Compressed sessions
    └── README.md                        # Index documentation
    ```

- **Validation Rules**:
    1. ✅ Archives should be **FILES**, not subdirectories
    2. ✅ Naming format: `<type>-archive-YYYY-QN.md`
    3. ✅ Each archive file < 1000 lines (compress if larger)
    4. ✅ README.md exists and lists all archives

#### Phase 6.2: Repair Inconsistent Structure
- **If subdirectory found** (e.g., `tasks-2026-Q1/`):
    1. **Scan subdirectory** for markdown files
    2. **Merge into single archive file**: `progress-archive-2026-Q1.md`
    3. **Delete subdirectory** after successful merge
    4. **Update README.md** with correct archive link

- **If oversized archive found** (> 1000 lines):
    1. **Extract critical content**: decision titles, key milestones
    2. **Compress verbose details**: remove full logs, keep summaries
    3. **Target**: < 800 lines per archive file

#### Phase 6.3: Archive Index Update
- **Action**: Update `archives/README.md` with current archive list.

- **Template**:
    ```markdown
    # Progress Archives

    This directory stores archived project records.

    ## Progress Archives
    - [2026 Q1](./progress-archive-2026-Q1.md) - [X tasks]
    - [2026 Q2](./progress-archive-2026-Q2.md) - [Y tasks]

    ## Auditor Reports Archives
    - [2026 Q1](./auditor-reports-archive-2026-Q1.md) - [Z disputes]

    ## Session Summaries Archives
    - [2026 Q1](./session-summaries-archive-2026-Q1.md) - [N sessions]

    ## Purpose
    - Keep active memory files manageable
    - Preserve complete project history
    - Enable historical analysis
    ```

- **Output**: Add to `[ENTROPY_REPORT]`:
    ```markdown
    ### Archives Validation
    - Structure: ✅ Consistent (all files) | ⚠️ Fixed (X subdirectories merged)
    - Total archives: X files
    - Largest archive: [filename] (Y lines)
    - README index: ✅ Updated
    ```

## Output Requirements
1. **[INTEGRITY_STATUS]**: Results from the Python audit script.
2. **[ENTROPY_REPORT]**: Identify 3 specific areas of bloat or misalignment.
    - **Include**: SKILL Extraction Candidates (documents with heat_score > 5)
    - **Include**: High-value knowledge patterns detected
    - **Include**: System Logs Cleanup summary
    - **Include**: Archives Validation summary
3. **[PRUNING_PROPOSAL]**: List of dormant or redundant SKILLs to archive.
    - **Include**: SKILLs with no usage in > 60 days
4. **[LEAN_UPDATE]**: Updated Markdown blocks for `AGENTS.md`.
5. **[HEAT_MAP]**: Top 10 reference documents by heat_score (data-driven prioritization).
6. **[ARCHIVES_STATUS]**: Archives directory structure and consistency report.