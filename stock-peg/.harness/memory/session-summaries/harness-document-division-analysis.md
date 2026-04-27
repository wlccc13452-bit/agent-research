# Harness Engineering Document Division Analysis

## Current Problems

### 1. **Redundant Content**

| Content | AGENTS.md | core-facts.md | FRONTEND.md | BACKEND.md | ARCHITECTURE.md |
|---------|-----------|---------------|-------------|------------|-----------------|
| **Tech Stack** | ✅ Brief | ✅ Brief | ✅ Detailed | ✅ Detailed | ❌ |
| **Code Style** | ✅ Brief | ⚠️ **Detailed + Examples** | ✅ Detailed | ✅ Detailed | ❌ |
| **Naming** | ✅ Brief | ⚠️ **Table** | ✅ Frontend | ✅ Backend | ❌ |
| **Prohibitions** | ✅ Detailed | ⚠️ **Brief (duplicate)** | ✅ Frontend | ✅ Backend | ❌ |
| **API Paths** | ✅ Critical Rules | ⚠️ **Immutable Paths** | ❌ | ❌ | ✅ API Design |
| **Language Rules** | ✅ **Detailed + Examples** | ❌ | ❌ | ❌ | ❌ |
| **Data Sources** | ❌ | ✅ | ❌ | ❌ | ✅ |

### 2. **Problem Domain Confusion**

**core-facts.md** currently mixes:
- ❌ Code style rules (should be in FRONTEND.md / BACKEND.md)
- ❌ Development standards (should be in AGENTS.md)
- ❌ API endpoints (should be in AGENTS.md or separate doc)
- ✅ Data sources (correct domain)
- ✅ Environment constraints (correct domain)

---

## Proposed Document Division

### **AGENTS.md** - Global Rules & Coordination
**Purpose**: Define system-wide rules, workflows, and document navigation

**Content**:
1. ✅ Mandatory Read Order
2. ✅ Project Overview & Tech Stack (brief)
3. ✅ Language Rules (keep detailed examples)
4. ✅ Core Principles (boundaries, data flow, non-blocking)
5. ✅ Code Style (brief, link to FRONTEND.md / BACKEND.md)
6. ✅ Naming Conventions (consolidated table from core-facts.md)
7. ✅ Workflows (feature dev, bug fix, dependency changes)
8. ✅ Multi-Environment Consistency
9. ✅ **API Path Rules** (immutable endpoints)
10. ✅ Prohibitions (comprehensive list)
11. ✅ Document Division Map (NEW)

**Remove**:
- ❌ Python environment details → move to SKILL
- ❌ Duplicate tech stack details

---

### **core-facts.md** - Immutable Facts & Constraints
**Purpose**: Record eternal facts that NEVER change during project lifetime

**Content**:
1. ✅ **Eternal Facts**
   - Project Positioning (name, core, goal)
   - Tech Stack (immutable choices)
   - Runtime Environment (ports, proxy)

2. ✅ **Data Sources** (Single Source of Truth)
   - Holdings Data: `自持股票.md`
   - Market Data: Akshare, yfinance
   - Financial Data: Akshare, yfinance
   - Stock Name Mapping: `stock_name_mapping.json`

3. ✅ **Environment Constraints**
   - Ports (Frontend 5173, Backend 8001, API Base 8000)
   - Database (SQLite, WAL mode)
   - Dependencies (UV, npm)

4. ✅ **Quick Reference**
   - Common Issues & Solutions
   - Check Before Starting
   - API Path Verification

**Remove**:
- ❌ Code Style (detailed examples) → FRONTEND.md / BACKEND.md
- ❌ Development Standards → AGENTS.md
- ❌ Prohibitions → AGENTS.md
- ❌ Naming Conventions Table → AGENTS.md

---

### **FRONTEND.md** - Frontend Development Standards
**Purpose**: Define frontend-specific standards with examples

**Content**:
1. ✅ Tech Stack (detailed table)
2. ✅ Directory Structure
3. ✅ State Management Strategy (Zustand + TanStack Query)
4. ✅ API Call Standards
5. ✅ Styling Standards (Tailwind, shadcn)
6. ✅ Component Standards (with code examples)
7. ✅ Chart Standards (ECharts)
8. ✅ Path Aliases
9. ✅ Performance Optimization
10. ✅ WebSocket Integration
11. ✅ Frontend Prohibitions

**Keep**: All current content is correct

---

### **BACKEND.md** - Backend Development Standards
**Purpose**: Define backend-specific standards with examples

**Content**:
1. ✅ Tech Stack (detailed table)
2. ✅ Directory Structure
3. ✅ Layered Architecture
4. ✅ Non-Blocking Principle (with examples)
5. ✅ Database Standards (ORM, async session)
6. ✅ Pydantic Models
7. ✅ Configuration Management
8. ✅ Error Handling
9. ✅ Logging Standards
10. ✅ WebSocket Push
11. ✅ Dependency Management (UV)
12. ✅ Backend Prohibitions

**Keep**: All current content is correct

---

### **ARCHITECTURE.md** - System Architecture
**Purpose**: Define overall system architecture and data flow

**Content**:
1. ✅ Overall Architecture Diagram
2. ✅ Core Boundaries
3. ✅ Data Flow (Startup, K-Line, Holdings)
4. ✅ API Design (RESTful endpoints)
5. ✅ WebSocket Message Types
6. ✅ Background Tasks
7. ✅ AI Integration
8. ✅ Security Considerations
9. ✅ Performance Optimization

**Keep**: All current content is correct

---

## Content Migration Plan

### AGENTS.md Changes
**Add**:
- Naming Conventions Table (from core-facts.md)
- Document Division Map (new section)

**Remove**:
- Python environment details (keep only link to SKILL)

### core-facts.md Changes
**Keep**:
- Eternal Facts
- Data Sources
- Environment Constraints
- Quick Reference

**Remove**:
- Code Style (lines 31-94) → already in FRONTEND.md / BACKEND.md
- Naming Conventions Table (lines 70-79) → move to AGENTS.md
- Prohibitions (lines 151-158) → already in AGENTS.md
- Development Standards → already in FRONTEND.md / BACKEND.md

**Add**:
- Focus on immutable constraints
- Quick reference tables

---

## Document Division Map (Add to AGENTS.md)

```markdown
## Document Division Map

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **AGENTS.md** | Global rules, workflows, prohibitions | Start of every task |
| **core-facts.md** | Immutable facts, environment constraints | When need facts about project |
| **FRONTEND.md** | Frontend development standards | Before frontend work |
| **BACKEND.md** | Backend development standards | Before backend work |
| **ARCHITECTURE.md** | System architecture, data flow | Before architecture decisions |
| **decisions.md** | Technical decision records | Before making new decisions |
| **progress.md** | Project completion status | Start of every session |

### Quick Reference Guide

**Q: Where do I find [topic]?**

| Topic | Document | Section |
|-------|----------|---------|
| API endpoints | AGENTS.md | API Path Rules |
| Code style | FRONTEND.md / BACKEND.md | Code Standards |
| Naming conventions | AGENTS.md | Naming Conventions |
| Data sources | core-facts.md | Data Sources |
| Environment ports | core-facts.md | Environment Constraints |
| System architecture | ARCHITECTURE.md | Overall Architecture |
| Prohibitions | AGENTS.md | Prohibitions |
| Tech stack details | FRONTEND.md / BACKEND.md | Tech Stack |
| Workflows | AGENTS.md | Workflows |
```

---

## Summary

**Core Principle**: Each document has a SINGLE RESPONSIBILITY

- **AGENTS.md**: Global coordination (rules, workflows, prohibitions)
- **core-facts.md**: Immutable facts (data sources, environment)
- **FRONTEND.md**: Frontend implementation details
- **BACKEND.md**: Backend implementation details
- **ARCHITECTURE.md**: System design & data flow

**Eliminate Redundancy**: Remove duplicate content, keep single source of truth for each topic.
