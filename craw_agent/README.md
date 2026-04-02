# craw-agent

Weekly Report Generation Crew built with CrewAI, focused on turning weekly raw data into polished Markdown reports.

## Features

- Hierarchical multi-agent workflow (manager, researcher, analyst, writer, formatter)
- Structured JSON intermediate outputs with guardrails
- Notion-ready Markdown final report
- Local weekly notes loader via custom tool
- Zhipu-first model routing support (`AI_DEFAULT_PROVIDER=zhipu`)
- Optional web research and optional OpenAI embedder

## Project Structure

```text
craw_agent/
├── pyproject.toml
├── .env
└── src/
    └── weekly_report_crew/
        ├── __init__.py
        ├── crew.py
        ├── main.py
        ├── config/
        │   ├── agents.yaml
        │   └── tasks.yaml
        ├── tools/
        │   ├── __init__.py
        │   └── custom_tools.py
        ├── data/
        │   └── weekly_notes/
        └── output/
```

## Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate
pip install -e .
```

## Environment Variables

Create or update `.env`:

```env
AI_DEFAULT_PROVIDER=zhipu
AI_DEFAULT_MODEL=glm-4.7
ZHIPU_API_KEY=your_zhipu_key

OPENAI_API_KEY=
OPENAI_MODEL_NAME=
OPENAI_RESEARCH_MODEL=

SERPER_API_KEY=
TAVILY_API_KEY=
WEEKLY_NOTES_DIR=src/weekly_report_crew/data/weekly_notes
```

Notes:

- With `AI_DEFAULT_PROVIDER=zhipu`, model names are normalized to `zhipuai/<model>`.
- If `ZHIPU_API_KEY` is set and `ZHIPUAI_API_KEY` is empty, runtime auto-syncs it.
- `SERPER_API_KEY` is optional; web search tool is enabled only when this key exists.
- `OPENAI_API_KEY` is optional; embedder is enabled only when this key exists.

## Run

Option 1: console script

```bash
weekly-report-crew --week-period "Week 12 2026" --focus "AI engineering team progress"
```

Option 2: module

```bash
python -m src.weekly_report_crew.main --week-period "March 10-16, 2026" --focus "AI product development team"
```

## Outputs

- Markdown report: `src/weekly_report_crew/output/weekly_report_latest.md`
- Run summary JSON: `src/weekly_report_crew/output/weekly_report_latest.json`
- Crew step logs: `src/weekly_report_crew/output/run_steps.log`

## Core Flow

1. Researcher collects internal data and optional web evidence.
2. Analyst extracts insights, blockers, risks, and metric interpretation.
3. Writer drafts narrative.
4. Formatter produces clean final Markdown.

## Security

- Never commit real API keys into `.env`.
- Rotate any leaked key immediately.
