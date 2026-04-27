# Session: 2026-03-11 - Force Index Analysis & Windows Environment Issue

## Completed Tasks
- Loaded harness engineering system context (progress.md, decisions.md, core-facts.md, AGENTS.md)
- Analyzed Force Index indicator for 中煤能源 (601898) using force-index-indicator-analysis skill
- Identified Windows execute_command tool limitation with quoted Chinese URLs
- Updated CodeBuddy system memory with Windows URL handling issue
- Created session summary documentation

## Technical Issues Discovered

### Windows execute_command URL Handling Limitation
**Problem**: execute_command tool fails with exit code 3 when using quoted URLs containing Chinese characters.

**Root Cause**: Tool-level quote processing issue in Windows environment.

**Solutions**:
1. ✅ Use unquoted URLs: `curl -s http://localhost:8000/api/indicators/force-index/中煤能源`
2. ✅ Use stock codes (most stable): `curl -s http://localhost:8000/api/indicators/force-index/601898`
3. ✅ Use Python requests library as fallback
4. ❌ Avoid: `curl -s "http://localhost:8000/api/indicators/force-index/中煤能源"` (fails)

**Impact**: This affects all future API calls with Chinese characters in URLs on Windows systems.

## Key Decisions
- Use stock codes instead of Chinese names for API calls (more stable across platforms)
- Record Windows-specific technical limitations in system memory for future reference
- Follow standard SKILL template structure for all skill files

## Issues Encountered
- update-memory/SKILL.md does not follow standard template structure
- SKILL file lacks detailed execution steps, causing incomplete workflow execution
- core-facts.md contains too many redundant code examples, lacks problem domain organization

### core-facts.md Restructure

**Problem Identified**:
- Too many code examples (TypeScript, Python, Tailwind, API responses)
- No clear problem domain classification (server/client interfaces, data sources)
- Difficult to quickly reference key constraints

**Solution Implemented**:
1. **Removed code examples**: Only keep principles and rules
2. **Added problem domain sections**:
   - API Endpoints (Server vs Client)
   - Data Sources (Holdings, Market, Financial)
   - Environment Constraints
3. **Added Quick Reference section**: Common issues and solutions table
4. **Enhanced API Path verification**: Clear correct/incorrect examples

**New Structure**:
```
core-facts.md
├── Eternal Facts (immutable tech stack)
├── API Endpoints (Server vs Client)
├── Data Sources (by type)
├── Development Standards (concise)
├── Environment Constraints
├── Development Workflow
├── Prohibitions
└── Quick Reference (tables)
```

**Benefits**:
- Faster reference for AI agents
- Clearer problem domain separation
- Easier to maintain and update
- Reduced cognitive load

---

## Harness Engineering Document Division Refactor

### Problem Identified
Documents have **overlapping responsibilities** and **redundant content**:
- **core-facts.md**: Contains code style, naming, prohibitions (duplicate with AGENTS.md, FRONTEND.md, BACKEND.md)
- **AGENTS.md**: Missing consolidated naming table and document navigation
- **No clear document map**: AI doesn't know where to find specific information

### Solution Implemented

#### 1. **core-facts.md Refactored** (242 lines → 144 lines)
**Removed**:
- ❌ Code style rules (TypeScript/Python examples)
- ❌ Naming conventions table → moved to AGENTS.md
- ❌ Prohibitions list → already in AGENTS.md
- ❌ Development standards → already in FRONTEND.md/BACKEND.md

**Kept** (Immutable Facts):
- ✅ Eternal Facts (project positioning, tech stack)
- ✅ Data Sources (holdings, market, financial, mapping)
- ✅ Environment Constraints (ports, database, dependencies)
- ✅ Quick Reference (common issues, API path verification)

#### 2. **AGENTS.md Enhanced**
**Added**:
- ✅ Naming Conventions table (consolidated from core-facts.md)
- ✅ Document Division Map (new section)
- ✅ Quick Reference Guide (where to find topics)

**Removed**:
- ❌ Python environment details (keep only link to SKILL)

### Document Responsibilities (Clear Division)

| Document | Single Responsibility |
|----------|----------------------|
| **AGENTS.md** | Global coordination (rules, workflows, prohibitions, naming, document map) |
| **core-facts.md** | Immutable facts (data sources, environment constraints) |
| **FRONTEND.md** | Frontend implementation details + code examples |
| **BACKEND.md** | Backend implementation details + code examples |
| **ARCHITECTURE.md** | System design & data flow |

### Benefits
1. **Single Source of Truth**: Each topic in ONE document
2. **Clear Navigation**: Document Division Map tells AI where to find info
3. **No Redundancy**: Eliminated duplicate content
4. **Faster Loading**: Smaller files, focused content
5. **Easier Maintenance**: Update in one place, not multiple files

## SKILL System Improvements

### Problem Identified
Original update-memory/SKILL.md was too simplistic (only 2 lines), missing:
- Mandatory Read Order (forced context loading)
- Detailed Step-by-Step Execution (clear workflow)
- Prohibitions (quality gates)
- Output Format (standard structure)
- **Intelligent compression capabilities**

### Solution Implemented
1. **Rewrote update-memory/SKILL.md**: Full 8-step workflow with automatic memory updates
2. **Simplified SKILL-TEMPLATE.md**: Focused on core principles, removed redundancy
3. **Added intelligent compression**: Auto-archive and compress old records

### Key Design Principles
1. **Mandatory Context Reading**: Force reading core-facts.md, decisions.md, progress.md, AGENTS.md before ANY action
2. **Test-First Discipline**: Always write failing test before implementation
3. **Automatic Memory Updates**: decisions.md, progress.md, session summaries auto-updated
4. **Language Enforcement**: English for all technical docs, Chinese only for UI
5. **Logging Standards**: trace_id required, truncate large data, proper log levels
6. **Intelligent Compression**: Auto-triggered compression based on file size/count

### Intelligent Compression Features

#### Auto-Trigger Conditions
| File | Trigger | Action |
|------|---------|--------|
| progress.md | > 200 lines | Archive entries > 30 days |
| session-summaries/ | > 7 files | Compress to weekly/monthly |
| decisions.md | > 50 entries | Group similar decisions |

#### Compression Hierarchy
```
memory/
├── session-summaries/ (last 7 days, detailed)
├── summaries/ (weekly/monthly compressed)
└── archives/ (progress archives)
```

#### Retention Policy
- **0-7 days**: Full detail in session-summaries/
- **8-30 days**: Weekly compressed summaries/
- **> 30 days**: Monthly summaries (milestones only)

### Why This Works
- **Predictable AI behavior**: Clear triggers and steps
- **Consistent quality**: Built-in quality gates
- **Memory continuity**: Automatic project knowledge updates
- **Best practices enforcement**: No manual oversight needed
- **Scalability**: Auto-compression prevents file bloat

## Continue Next Time
- Test updated update-memory SKILL with real scenarios
- Validate Force Index API accuracy with more stocks
- Consider batch Force Index analysis for all holdings
- Monitor if SKILL system improves AI task execution consistency
