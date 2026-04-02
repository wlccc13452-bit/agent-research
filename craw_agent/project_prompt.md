You are a senior CrewAI architect in 2026, expert in v0.110+ best practices (YAML-first config, hierarchical or sequential process, memory=True, planning=True where useful, structured JSON/Markdown outputs, callbacks, guardrails).

Generate a complete, production-ready CrewAI project for a **Weekly Report Generation Crew** that automates creating a professional weekly report (e.g. team progress, project updates, metrics, learnings).

Core workflow (all in English):
- Input: week number or date range (e.g. "Week 12 2026" or "March 10-16, 2026"), optional topic/focus (e.g. "AI product development team")
- Agents:
  - Researcher: gathers raw data (from provided sources, web search, internal files, APIs, calendars, etc.)
  - Analyst: extracts key insights, trends, blockers, achievements from the raw data
  - Writer: composes a clear, professional narrative report in English
  - Formatter: converts the draft into clean, structured Markdown (with headings, bullets, tables) that is easy to paste into Notion or other tools
- Output: final Markdown report + optional JSON summary

Requirements — output strictly in this Markdown structure (nothing before or after):

# 1. Project Overview
- Project name (kebab-case English folder name)
- One-sentence goal
- Target users / use-case
- Expected complexity / token burn level (low / medium / high)
- Recommended LLM routing (strong model for manager/writer, cheaper for researcher/analyst)

# 2. Directory Structure
Clean tree view (like after `crewai create crew weekly-report-crew`)

# 3. Installation & Setup Commands
- pip / uv install commands (crewai, crewai-tools, pydantic, etc.)
- .env example (OPENAI_API_KEY, SERPER_API_KEY / TAVILY_API_KEY for search if used, optional others)
- How to run

# 4. agents.yaml (full content)
- 4–6 agents: e.g. Manager/Orchestrator (if hierarchical), Data Researcher, Insight Analyst, Report Writer, Markdown Formatter
- Each: role, goal, backstory (detailed, guides precise behavior in English), llm model name, verbose: true, allow_delegation: true/false, tools: [list – SerperDevTool / ScrapeWebsiteTool / FileReadTool / DirectoryReadTool if applicable], max_rpm if needed

# 5. tasks.yaml (full content)
- 5–8 tasks with clear dependencies (context: [previous_task_id])
- Each: description (detailed, use {week_period} {focus} placeholders), expected_output (strict format: JSON schema for intermediate, Markdown structure for final), agent: key, async_execution: false/true, tools if extra
- Last task produces clean Markdown ready for Notion

# 6. crew.py (full Python code)
- from crewai import Agent, Crew, Process, Task
- from crewai_tools import SerperDevTool, ScrapeWebsiteTool, FileReadTool, DirectoryReadTool (or others you choose)
- Optional: custom tools import
- Load YAML configs
- Create agents & tasks
- Crew with: agents, tasks, process=Process.sequential OR hierarchical (recommend hierarchical with manager_llm), manager_llm=strong model if hierarchical, memory=True, verbose=2
- Optional: embedder config, step_callback for logging

# 7. tools/custom_tools.py (1–2 examples if useful)
- At least one BaseTool subclass: e.g. WeeklyDataLoaderTool (reads from folder of notes/CSVs/JSONs), or SimpleWebSearchWrapper
- Include description, args_schema (Pydantic), _run method

# 8. main.py (entry point)
- Simple script: load crew, kickoff with sample inputs e.g. {"week_period": "March 10-16, 2026", "focus": "AI engineering team progress"}
- Print or save final Markdown result

# 9. Quick Start & Debugging Tips
- Commands to run
- How to add human_input=True on final formatter task
- Observability (verbose=2, optional Langfuse/Phonix stub)
- Common fixes: hallucinations, missing data, context overflow, Notion formatting issues

# 10. Next-Level Extensions
- Add long-term memory (vector store for past weeks)
- Integrate calendar/email APIs (Google Calendar, Gmail tools)
- Add reflection agent to critique & improve draft
- Convert to CrewAI Flow for conditional steps (e.g. if no data → alert human)
- Save reports to folder / Notion via API

Use 2026 best practices:
- YAML correct indentation & syntax
- Python PEP-8
- Tools: prefer SerperDevTool or similar for research; add file/directory tools for internal weekly notes
- Structured outputs (JSON for analysis, clean Markdown for final)
- Detailed backstories to keep everything in English and reduce drift
- Realistic division: data collection → insight extraction → narrative → polished formatting

Now generate the full project exactly for this Weekly Report Generation use case (all agents and content in English).