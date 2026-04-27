# D028: Harness Engineering Knowledge Management Restructuring

**Date**: 2026-03-16
**Status**: Active

---

## Decision

Restructure harness engineering knowledge management to establish clear layered architecture and prevent core files from becoming too large.

---

## Reason

### Problems Identified

1. **Core Files Too Large**:
   - `decisions.md`: 438 lines (27 decisions with full details)
   - `progress.md`: 469 lines (complete project history)
   - AI Agent context waste: reading same detailed content repeatedly

2. **Knowledge Overlap**:
   - Domain-specific knowledge mixed with core records
   - Technical details duplicated across multiple files
   - Unclear where to find specific information

3. **No Clear Hierarchy**:
   - All knowledge at same level
   - No separation between summary and details
   - Difficult to maintain and update

### Solution Benefits

1. **Faster AI Context Loading**:
   - Core files < 300 lines each
   - Only load details when needed
   - Estimated 50% context reduction

2. **Clear Knowledge Hierarchy**:
   - 摘要层 (Core): Quick reference
   - 详情层 (Reference): Deep knowledge
   - 日志层 (Session): Historical records

3. **Better Maintainability**:
   - Single responsibility per file
   - Clear update rules
   - Easier to find and update knowledge

---

## Architecture

### Layered Knowledge Management

```
核心文件 (摘要层 - Summary Layer)
├── AGENTS.md (< 600 lines)
├── decisions.md (< 200 lines, summaries only)
├── progress.md (< 300 lines, last 3 days only)
└── memory/core-facts.md (< 150 lines)
    ↓
Reference Files (详情层 - Detail Layer)
├── reference/architecture/ (architecture decisions)
├── reference/technical/ (technical solutions)
├── reference/debugging/ (debugging records)
└── reference/index.md (master index)
    ↓
Session Summaries (日志层 - Log Layer)
└── memory/session-summaries/YYYY-MM-DD-*.md
```

### Directory Structure

```
.harness/
├── reference/
│   ├── architecture/
│   │   ├── README.md
│   │   ├── D001-D010-tech-stack.md
│   │   ├── D011-D015-harness-optimization.md (to be created)
│   │   ├── D020-mcp-server.md (to be created)
│   │   ├── D021-harness-upgrade-v5.md (to be created)
│   │   └── D022-D027-feishu-integration.md
│   ├── technical/
│   │   ├── README.md
│   │   ├── indicators/ (to be created)
│   │   ├── feishu/ (to be created)
│   │   └── data-management/ (to be created)
│   ├── debugging/
│   │   ├── README.md
│   │   └── feishu-event-loop-conflict.md (to be created)
│   ├── configuration/ (existing)
│   └── index.md
```

---

## Implementation

### Phase 1: Establish Structure ✅

1. Created `reference/` directory structure
2. Created `reference/index.md` (master index)
3. Created README.md for each subdirectory

### Phase 2: Migrate Content ✅

1. Created `reference/architecture/D001-D010-tech-stack.md`
2. Created `reference/architecture/D022-D027-feishu-integration.md`
3. Refactored `decisions.md` to summaries only
4. Refactored `progress.md` to last 3 days only

### Phase 3: Update Rules ✅

1. Updated `AGENTS.md` with new document division
2. Established size targets for core files
3. Created update rules in each file

### Phase 4: Create Remaining Docs (Pending)

- D011-D015, D016-D019, D020, D021 detailed documents
- Technical solution documents
- Debugging record documents

---

## Update Rules

### For Core Files

1. **decisions.md**:
   - Add decision summary (number, title, date, one-liner, reference link)
   - Create detailed doc in `reference/architecture/`
   - Keep file < 200 lines

2. **progress.md**:
   - Add completion to "Recent Completions" (last 3 days only)
   - Move older records to `memory/session-summaries/`
   - Link to detailed docs in `reference/`
   - Keep file < 300 lines

3. **AGENTS.md**:
   - Update document division section
   - Update quick reference table
   - Keep file < 600 lines

### For Reference Files

1. **Architecture Decisions**:
   - Create in `reference/architecture/`
   - Group related decisions (e.g., D022-D027)
   - Use template from `reference/architecture/README.md`

2. **Technical Solutions**:
   - Create in `reference/technical/<category>/`
   - Link to related decisions
   - Include code examples and implementation details

3. **Debugging Records**:
   - Create in `reference/debugging/`
   - Document root cause analysis
   - Extract lessons learned

---

## Impact

### Positive

1. **Context Efficiency**:
   - 50% reduction in core file sizes
   - AI loads only needed details
   - Faster task understanding

2. **Knowledge Organization**:
   - Clear hierarchy: summary → details → logs
   - Single responsibility per file
   - Easier to find information

3. **Maintainability**:
   - Clear update rules
   - Prevents knowledge accumulation in core files
   - Better long-term scalability

### Potential Issues

1. **More Files**: Increased number of files to maintain
   - Mitigation: Clear naming and indexing

2. **Navigation Overhead**: Need to follow links to get details
   - Mitigation: Index file and README guides

3. **Migration Effort**: Existing knowledge needs to be reorganized
   - Mitigation: Incremental migration, prioritize recent decisions

---

## Files Modified

- `reference/index.md` - Created master index
- `reference/architecture/README.md` - Created architecture guide
- `reference/architecture/D001-D010-tech-stack.md` - Migrated tech stack decisions
- `reference/architecture/D022-D027-feishu-integration.md` - Migrated Feishu decisions
- `reference/technical/README.md` - Created technical guide
- `reference/debugging/README.md` - Created debugging guide
- `decisions.md` - Refactored to summaries only
- `progress.md` - Refactored to last 3 days only
- `AGENTS.md` - Updated document division and quick reference

---

## Lessons Learned

1. **Knowledge Layering**: Summary-details-logs hierarchy is effective for AI context management
2. **Size Targets**: Explicit size constraints prevent unbounded growth
3. **Clear Indexing**: Master index essential for navigation across many files
4. **Incremental Migration**: Prioritize recent/important content first

---

## Related Decisions

- D015: Eliminate Document Redundancy (similar goal)
- D017: Harness Robustness Protocol (robustness consideration)

---

## Version

- **Created**: 2026-03-16
- **Version**: 1.0
