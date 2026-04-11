# CrewAI Classic Python Project Plan

## Summary
- Create a new Python CrewAI project in English that uses two agents, **Researcher** and **Analyst**, to collaboratively produce a final report.
- Scaffold a runnable CLI workflow with clear configuration, modular source files, and reproducible output generation.
- Include baseline quality checks and usage guidance so the project can be executed immediately after dependency installation.

## Current State Analysis
- Repository root currently appears empty (no existing source files or configuration detected at `d:\play-ground\openclaw-works\agent-research\crewai-test`).
- No pre-existing Python package structure, virtual environment metadata, or CrewAI-specific scaffolding is present.
- Therefore, the implementation should initialize a full minimal project structure from scratch.

## Proposed Changes

### 1) Project scaffolding and dependency management
**Files to create**
- `pyproject.toml`
- `README.md`
- `.gitignore`
- `requirements.txt` (optional compatibility list mirroring pyproject dependencies)

**What / Why / How**
- Define Python project metadata and dependencies for CrewAI execution.
- Pin practical minimum versions for deterministic setup.
- Add README with English-only setup and run instructions.
- Add `.gitignore` for Python cache, virtual environment folders, and generated outputs.

### 2) Application package and entrypoints
**Files to create**
- `src/crewai_reporter/__init__.py`
- `src/crewai_reporter/main.py`
- `src/crewai_reporter/config.py`

**What / Why / How**
- Use a package-based layout for maintainability.
- `main.py` provides the executable entrypoint (e.g., `python -m crewai_reporter.main`).
- `config.py` centralizes constants (default topic, output path, model placeholders, and role goals).

### 3) Agent, task, and crew orchestration modules
**Files to create**
- `src/crewai_reporter/agents.py`
- `src/crewai_reporter/tasks.py`
- `src/crewai_reporter/crew.py`

**What / Why / How**
- `agents.py`: define two CrewAI agents:
  - **Researcher**: gathers and structures source insights.
  - **Analyst**: synthesizes findings into a coherent report.
- `tasks.py`: define task contracts, expected outputs, and handoff ordering.
- `crew.py`: compose agents + tasks into a crew process, run it, and return final output.

### 4) Report output pipeline
**Files to create**
- `outputs/.gitkeep`

**Files to update/create**
- `src/crewai_reporter/main.py` (save final report to `outputs/final_report.md`)

**What / Why / How**
- Ensure deterministic artifact location for generated reports.
- Persist final markdown report and print terminal summary.
- Keep all generated content in an explicit output directory.

### 5) Environment and secrets handling
**Files to create**
- `.env.example`

**What / Why / How**
- Provide required environment variable template (e.g., LLM provider API key).
- Keep secrets out of source code while making setup straightforward.

### 6) Baseline tests
**Files to create**
- `tests/test_structure.py`

**What / Why / How**
- Add light structural tests to verify:
  - Agent factory returns exactly two roles (Researcher, Analyst).
  - Task builder creates research-then-analysis flow.
  - Crew assembly object can be instantiated without runtime side effects.
- Keep tests fast and dependency-light.

## Assumptions & Decisions
- All source code, prompts, role descriptions, and README content will be written in English.
- The project targets a modern Python 3.x runtime with package-based execution.
- The first iteration will implement a classic two-agent sequential flow (research → analysis), without extra tools or vector database integration.
- LLM credentials are provided through environment variables by the user at runtime.
- The implementation favors clarity and extendability over advanced optimization in v1.

## Verification Steps
1. Confirm project structure and required files exist.
2. Install dependencies in a clean virtual environment.
3. Run tests to validate module structure and orchestration wiring.
4. Execute the main entrypoint with a sample topic.
5. Verify `outputs/final_report.md` is generated and contains synthesized report sections.
6. Confirm README instructions reproduce the same workflow end-to-end.
