# Harness System Architecture

**Priority**: Standard
**Project**: Stock PEG
**Last Updated**: 2026-03-18
**Purpose**: Detailed harness architecture, directory structure, and document organization

---

## Directory Structure

```
.harness/
├── AGENTS.md                       # Global rules (this file)
├── progress.md                     # Project completion status
├── decisions.md                    # Technical decision records
├── FRONTEND.md                     # Frontend development standards
├── BACKEND.md                      # Backend development standards
├── ARCHITECTURE.md                 # System architecture
├── memory/
│   ├── core-facts.md               # Immutable facts & constraints
│   ├── session-summaries/          # Daily session records
│   └── archives/                   # Completed task archives
├── reference/
│   ├── general/                    # Universal patterns (reusable)
│   ├── project-specific/           # Domain knowledge
│   ├── skills/                     # Executable workflows
│   └── architecture/               # Decision details
└── skills/                         # AI Agent capabilities
    ├── utils/                      # Utility skills
    ├── cross-layer/                # Full-stack skills
    └── indicators/                 # Technical indicator skills
```

---

## Layered Architecture

**Three-Layer Knowledge System**:

1. **Core Files (Summary Layer)** - Concise, quick reference
   - AGENTS.md - Global rules, workflows, prohibitions (< 400 lines)
   - decisions.md - Decision summaries only (< 200 lines)
   - progress.md - Recent 3 days progress only (< 300 lines)
   - memory/core-facts.md - Immutable facts, constraints (< 150 lines)

2. **Reference Files (Detail Layer)** - Detailed knowledge
   - general/ - Universal patterns (reusable in other projects)
   - project-specific/ - Domain knowledge (this project only)
   - skills/ - Executable workflows (automated)
   - architecture/ - Decision details (long-term)

3. **Session Summaries (Log Layer)** - Historical records
   - memory/session-summaries/ - Daily session logs
   - memory/archives/ - Completed task archives

**Data Flow**: Core Files (Summary) → Reference (Details) → Session Summaries (Logs)

---

## Quality Standards

**Reference**: `reference/QUALITY-STANDARDS.md`

### Admission Criteria

- ✅ Debugging time > 30 minutes
- ✅ Root cause analysis complete
- ✅ Document < 300 lines (general) / < 400 lines (project-specific)
- ✅ English only (no Chinese in documentation)
- ✅ Reusable (general) or project-specific (domain)
- ✅ Code examples < 50 lines (core snippets)

### Document Lifecycle

1. **Creation**: Debugging time > 30min + root cause identified
2. **Review**: Check quality standards compliance
3. **Registration**: Add to reference/index.md
4. **Maintenance**: Update when patterns change
5. **Archive**: Move to archives when obsolete

---

## Quick Navigation Guide

### Where to Find What?

**Core Files (Summary Layer)**:
- API endpoints & paths → AGENTS.md (API Path Rules)
- Code style → FRONTEND.md / BACKEND.md
- Tech stack details → FRONTEND.md / BACKEND.md (Tech Stack tables)
- Workflows → AGENTS.md (Workflows section)
- Prohibitions → AGENTS.md (Prohibitions section)
- Recent progress → progress.md (Recent Completions section)

**Reference Files (Detail Layer)**:

| Category | Purpose | Location | Example |
|----------|---------|----------|---------|
| **General** | Universal patterns (reusable) | `reference/general/<category>/` | async-patterns/ |
| **Project-Specific** | Domain knowledge | `reference/project-specific/<domain>/` | feishu/ |
| **Skills** | Executable knowledge | `reference/skills/<topic>/` | force-index/ |
| **Architecture** | Decision details | `reference/architecture/` | D022-D027-*.md |

**Memory Files (Immutable Facts)**:
| Topic | Location |
|-------|----------|
| Data sources | memory/core-facts.md (Data Sources) |
| Environment ports | memory/core-facts.md (Environment Constraints) |
| System architecture | ARCHITECTURE.md |
| Recent completions | progress.md (Recent Completions section) |
| Session details | memory/session-summaries/ (Daily files) |

**Master Index**: `reference/index.md` - Comprehensive index for all detailed knowledge

---

## Reference Directory Organization

### General (Universal Patterns)

**Purpose**: Reusable patterns across projects  
**Language**: English only  
**Size Target**: < 300 lines per file

**Categories**:
- `async-patterns/` - Async/await patterns, event loops, threading
- `database-patterns/` - Database session management, connection pooling
- `api-patterns/` - RESTful API design, error handling
- `testing-patterns/` - Test organization, mocking strategies

### Project-Specific (Domain Knowledge)

**Purpose**: Domain knowledge for this project  
**Language**: English only (Chinese allowed in code comments, UI text)  
**Size Target**: < 400 lines per file

**Categories**:
- `feishu/` - Feishu integration patterns
- `stock-data/` - Stock data management
- `environment/` - Development environment setup, troubleshooting
- `standards/` - Project-specific coding standards
- `workflows/` - Development workflows

### Skills (Executable Workflows)

**Purpose**: Automated, executable knowledge  
**Language**: English only  
**Size Target**: < 200 lines per SKILL.md

**Categories**:
- Indicators (technical analysis)
- Utils (utility skills)
- Cross-layer (full-stack skills)

### Architecture (Decision Details)

**Purpose**: Detailed architectural decisions  
**Language**: English only  
**Size Target**: No limit (comprehensive documentation)

**Naming Convention**: `D###-title.md` (e.g., `D022-D027-feishu-integration.md`)

---

## SKILL Extraction Process

**Trigger**: Document accessed > 3 times OR pattern is executable OR user requests

**Process**:
1. Extract core knowledge from reference document
2. Create SKILL in `reference/skills/<topic>/SKILL.md`
3. Copy to `.harness/skills/` directory
4. Register in `.harness/skills/registry.json`
5. Update AGENTS.md Skills Directory
6. Add SKILL link to source reference document

**Example**: `async-sdk-integration` SKILL extracted from `general/async-patterns/thread-isolation-pattern.md`

**Requirements**:
- Keep SKILL < 200 lines (精华版 - essence version)
- Include executable steps
- Provide clear validation criteria
- Link back to detailed reference

---

## Document Maintenance Schedule

### Daily
- Update progress.md (add to Recent Completions)
- Create session summary in memory/session-summaries/

### Weekly
- Archive old progress entries (if > 200 lines)
- Compress session summaries (if > 7 files)
- Review progress and plan next steps

### Monthly
- Deduplicate decisions.md (if > 50 entries)
- Review and clean memory/archives/
- Review and update core-facts.md if needed

### Quarterly
- Comprehensive harness audit
- Archive old sessions to quarterly archives
- Review document structure and eliminate overlaps

---

## Related Documents

- `.harness/AGENTS.md` - Global rules and workflows
- `.harness/reference/QUALITY-STANDARDS.md` - Content quality criteria
- `.harness/reference/index.md` - Master index
- `.harness/memory/core-facts.md` - Immutable facts
