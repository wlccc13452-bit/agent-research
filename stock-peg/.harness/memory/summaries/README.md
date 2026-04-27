# Session Summaries Archive

This directory stores compressed weekly and monthly session summaries.

## Summary Files
- `weekly-summary-2026-W01.md` - Week 1 summary (compressed from daily summaries)
- `monthly-summary-2026-01.md` - January 2026 summary (milestones only)

## Retention Policy

| Time Range | Detail Level | Location |
|------------|--------------|----------|
| **0-7 days** | Full detail | `session-summaries/YYYY-MM-DD-*.md` |
| **8-30 days** | Weekly compressed | `summaries/weekly-summary-YYYY-WNN.md` |
| **> 30 days** | Monthly compressed | `summaries/monthly-summary-YYYY-MM.md` |

## Purpose
- Reduce file count in session-summaries/
- Preserve essential information
- Enable quick retrospective reviews

## Compression Process
1. Daily summaries > 7 days → compressed into weekly summary
2. Weekly summaries > 4 weeks → compressed into monthly summary
3. Original files removed after successful compression

## Access
Weekly/monthly summaries provide quick overview of:
- Key decisions made
- Major milestones achieved
- Critical issues resolved
- Files modified during period
