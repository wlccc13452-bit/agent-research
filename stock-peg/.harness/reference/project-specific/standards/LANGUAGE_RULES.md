# Language Rules

**Priority**: Critical
**Applicable Prohibition**: AGENTS.md Prohibition #16
**Project**: Stock PEG
**Last Updated**: 2026-03-18
**Purpose**: Language usage standards for documentation, code, and UI

---

## Primary Language

**English** is the primary language for ALL harness engineering documentation.

---

## Chinese Allowed In

- Code comments (代码注释)
- User-facing UI text (用户界面文本)
- Report content (报告内容)
- Error messages shown to users (用户错误信息)
- Data field names in Chinese (中文字段名)

---

## English Required In

- All documentation files (所有文档)
- All SKILL.md files (所有技能文档)
- All reference/ directory files (reference目录所有文件)
- Code variable names and function names
- API endpoint names
- Database table/column names
- Log messages (日志消息)
- Git commit messages

---

## Examples

### ✅ Correct Usage

#### Skill File (English)

```markdown
## Description
Calculate Force Index for stock analysis
```

#### Code (English variable names, Chinese UI text)

```python
def calculate_force_index(stock_code: str) -> dict:
    """Calculate Force Index indicator"""
    result = {
        'stock_name': stock_name,  # English key
        'signal': '买入',  # Chinese value (user-facing)
        'trend': '上涨趋势'  # Chinese value (user-facing)
    }
    logger.info(f"Calculating Force Index for {stock_code}")  # English log
    return result
```

#### UI Component (Chinese text)

```tsx
<div>
  <h1>股票分析报告</h1>
  <p>当前信号: {signal}</p>
</div>
```

### ❌ Incorrect Usage

#### Variable Name in Chinese

```python
股票代码 = "000001"  # WRONG
```

**Correct**:
```python
stock_code = "000001"  # CORRECT
```

#### Log Message in Chinese

```python
logger.info("计算Force Index")  # WRONG
```

**Correct**:
```python
logger.info("Calculating Force Index")  # CORRECT
```

#### SKILL.md in Chinese

```markdown
## 描述
计算Force Index指标  # WRONG
```

**Correct**:
```markdown
## Description
Calculate Force Index indicator  # CORRECT
```

---

## Quick Reference

| Context | Language | Example |
|---------|----------|---------|
| Documentation | English | SKILL.md, reference files |
| Variable names | English | `stock_code`, `fetch_data` |
| Function names | English | `calculate_force_index()` |
| API endpoints | English | `/api/indicators/force-index` |
| Database tables | English | `stock_kline_data` |
| Log messages | English | `logger.info("Processing data")` |
| Code comments | Chinese allowed | `# 计算技术指标` |
| UI text | Chinese allowed | `<div>股票分析报告</div>` |
| Error messages | Chinese allowed | `"股票代码不存在"` |

---

## Rationale

### Why English for Documentation?

1. **Consistency**: All technical documentation follows same standard
2. **Reusability**: Reference documents can be reused across projects
3. **International**: Accessible to global development community
4. **Searchability**: Easier to search and index English content
5. **Maintainability**: Consistent naming conventions reduce cognitive load

### Why Chinese Allowed for UI/Comments?

1. **User Experience**: Chinese users understand Chinese UI text better
2. **Context Clarity**: Chinese comments can provide better context for complex business logic
3. **Team Efficiency**: Chinese team members can quickly understand code intent

---

## Validation Checklist

Before committing code or documentation, verify:

- [ ] All documentation files are in English
- [ ] All variable names are in English
- [ ] All function names are in English
- [ ] All API endpoints are in English
- [ ] All database tables/columns are in English
- [ ] All log messages are in English
- [ ] Git commit messages are in English
- [ ] Chinese text is only in: comments, UI text, user messages

---

## Related Documents

- `.harness/AGENTS.md` - Global rules and prohibitions
- `.harness/FRONTEND.md` - Frontend development standards
- `.harness/BACKEND.md` - Backend development standards
