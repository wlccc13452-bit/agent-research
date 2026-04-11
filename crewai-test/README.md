# CrewAI Reporter

A classic CrewAI Python project where two agents collaborate to produce a report:

- **Researcher** gathers and structures key findings.
- **Analyst** synthesizes those findings into a final report.

## Requirements

- Python 3.10+
- An API key for your LLM provider

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment template and set values:

```bash
copy .env.example .env
```

You can run this project with only `DEEPSEEK_API_KEY` in `.env`.  
The runtime automatically maps it to CrewAI-compatible OpenAI environment variables.

## Run

Use the default topic:

```bash
python -m crewai_reporter.main
```

Use a custom topic:

```bash
python -m crewai_reporter.main "Future of autonomous AI agents in healthcare"
```

After execution, the generated report is saved to:

- `outputs/final_report.md`

## Test

```bash
pytest
```
