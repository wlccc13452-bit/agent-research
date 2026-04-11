from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml
from crewai import Agent, Crew, Process, Task
from crewai_tools import DirectoryReadTool, FileReadTool, ScrapeWebsiteTool, SerperDevTool
from dotenv import load_dotenv
from pydantic import BaseModel

from .tools.custom_tools import WeeklyDataLoaderTool


class RawWeeklyData(BaseModel):
    week_period: str
    focus: str
    internal_sources: List[Dict[str, Any]]
    raw_events: List[Dict[str, Any]]
    metrics: List[Dict[str, Any]]
    open_questions: List[str]


class InsightPackage(BaseModel):
    executive_highlights: List[str]
    achievements: List[Dict[str, Any]]
    blockers: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    metric_summary: List[Dict[str, Any]]
    trend_assessment: str
    confidence: Dict[str, Any]
    assumptions: List[str]


class JsonSummary(BaseModel):
    week_period: str
    focus: str
    overall_status: str
    top_3_wins: List[str]
    top_3_issues: List[str]
    next_week_priorities: List[str]
    needs_leadership_attention: List[str]


class WeeklyReportCrewBuilder:
    def __init__(self) -> None:
        load_dotenv()
        self.base_dir = Path(__file__).resolve().parent
        self.config_dir = self.base_dir / "config"
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.strong_model = self._resolve_strong_model()
        self.research_model = self._resolve_research_model()

        with (self.config_dir / "agents.yaml").open("r", encoding="utf-8") as handle:
            self.agents_config = yaml.safe_load(handle)
        with (self.config_dir / "tasks.yaml").open("r", encoding="utf-8") as handle:
            self.tasks_config = yaml.safe_load(handle)

        notes_dir = os.getenv("WEEKLY_NOTES_DIR", str(self.base_dir / "data" / "weekly_notes"))

        self.weekly_data_loader = WeeklyDataLoaderTool(base_path=notes_dir)
        self.directory_reader = DirectoryReadTool(directory=notes_dir)
        self.file_reader = FileReadTool()
        self.serper_search = self._build_serper_tool()
        self.website_scraper = ScrapeWebsiteTool()
        self._sync_provider_api_keys()

    @staticmethod
    def _provider_name() -> str:
        return os.getenv("AI_DEFAULT_PROVIDER", "").strip().lower()

    @classmethod
    def _normalize_model_name(cls, model_name: str) -> str:
        provider = cls._provider_name()
        model_name = model_name.strip()
        if provider in {"zhipu", "zhipuai"} and "/" not in model_name:
            return f"zhipuai/{model_name}"
        return model_name

    @classmethod
    def _resolve_strong_model(cls) -> str:
        provider = cls._provider_name()
        if provider in {"zhipu", "zhipuai"}:
            selected = (
                os.getenv("AI_DEFAULT_MODEL")
                or os.getenv("OPENAI_MODEL_NAME")
                or "glm-4.7"
            )
        else:
            selected = (
                os.getenv("OPENAI_MODEL_NAME")
                or os.getenv("AI_DEFAULT_MODEL")
                or "gpt-5"
            )
        return cls._normalize_model_name(selected)

    def _resolve_research_model(self) -> str:
        selected = os.getenv("OPENAI_RESEARCH_MODEL") or self.strong_model
        return self._normalize_model_name(selected)

    @staticmethod
    def _sync_provider_api_keys() -> None:
        zhipu_key = os.getenv("ZHIPU_API_KEY", "").strip()
        zhipuai_key = os.getenv("ZHIPUAI_API_KEY", "").strip()
        if zhipu_key and not zhipuai_key:
            os.environ["ZHIPUAI_API_KEY"] = zhipu_key

    @staticmethod
    def _build_serper_tool() -> SerperDevTool | None:
        if os.getenv("SERPER_API_KEY", "").strip():
            return SerperDevTool()
        return None

    @staticmethod
    def _resolve_embedder() -> Dict[str, Any] | None:
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        if openai_key:
            return {
                "provider": "openai",
                "config": {"model": "text-embedding-3-small"},
            }
        return None

    def _agent_config(self, key: str) -> Dict[str, Any]:
        config = dict(self.agents_config[key])
        config.pop("tools", None)
        if key in {"manager_orchestrator", "report_writer", "markdown_formatter"}:
            config["llm"] = self.strong_model
        if key in {"data_researcher", "insight_analyst"}:
            config["llm"] = self.research_model
        return config

    def _task_config(self, key: str) -> Dict[str, Any]:
        return dict(self.tasks_config[key])

    def _step_callback(self, step_output: Any) -> None:
        log_path = self.output_dir / "run_steps.log"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(str(step_output) + "\n")

    @staticmethod
    def _json_guardrail(output: Any) -> tuple[bool, str]:
        text = output if isinstance(output, str) else str(output)
        try:
            json.loads(text)
            return True, "valid_json"
        except Exception:
            return False, "invalid_json_output"

    @staticmethod
    def _markdown_guardrail(output: Any) -> tuple[bool, str]:
        text = output if isinstance(output, str) else str(output)
        headers = [
            "# Weekly Report:",
            "## Focus",
            "## Executive Summary",
            "## Achievements",
            "## Metrics",
            "## Blockers & Risks",
            "## Decisions & Learnings",
            "## Next Week Priorities",
            "## Leadership Support Needed",
            "## Action Checklist",
        ]
        valid = all(header in text for header in headers)
        return (True, "valid_markdown_structure") if valid else (False, "invalid_markdown_structure")

    def build(self) -> Crew:
        manager = Agent(config=self._agent_config("manager_orchestrator"))

        data_researcher = Agent(
            config=self._agent_config("data_researcher"),
            tools=[
                tool
                for tool in [
                    self.weekly_data_loader,
                    self.directory_reader,
                    self.file_reader,
                    self.serper_search,
                    self.website_scraper,
                ]
                if tool is not None
            ],
        )
        insight_analyst = Agent(
            config=self._agent_config("insight_analyst"),
            tools=[self.file_reader],
        )
        report_writer = Agent(config=self._agent_config("report_writer"))
        markdown_formatter = Agent(config=self._agent_config("markdown_formatter"))

        collect_raw_weekly_data = Task(
            config=self._task_config("collect_raw_weekly_data"),
            agent=data_researcher,
            output_pydantic=RawWeeklyData,
            guardrail=self._json_guardrail,
        )
        enrich_with_web_research = Task(
            config=self._task_config("enrich_with_web_research"),
            agent=data_researcher,
            context=[collect_raw_weekly_data],
            guardrail=self._json_guardrail,
        )
        analyze_weekly_insights = Task(
            config=self._task_config("analyze_weekly_insights"),
            agent=insight_analyst,
            context=[collect_raw_weekly_data, enrich_with_web_research],
            output_pydantic=InsightPackage,
            guardrail=self._json_guardrail,
        )
        produce_json_summary = Task(
            config=self._task_config("produce_json_summary"),
            agent=insight_analyst,
            context=[analyze_weekly_insights],
            output_pydantic=JsonSummary,
            guardrail=self._json_guardrail,
        )
        write_weekly_narrative = Task(
            config=self._task_config("write_weekly_narrative"),
            agent=report_writer,
            context=[analyze_weekly_insights, produce_json_summary],
        )
        format_notion_ready_markdown = Task(
            config=self._task_config("format_notion_ready_markdown"),
            agent=markdown_formatter,
            context=[write_weekly_narrative],
            guardrail=self._markdown_guardrail,
            output_file=str(self.output_dir / "weekly_report.md"),
        )

        crew_kwargs: Dict[str, Any] = {
            "agents": [
                data_researcher,
                insight_analyst,
                report_writer,
                markdown_formatter,
            ],
            "tasks": [
                collect_raw_weekly_data,
                enrich_with_web_research,
                analyze_weekly_insights,
                produce_json_summary,
                write_weekly_narrative,
                format_notion_ready_markdown,
            ],
            "process": Process.hierarchical,
            "manager_agent": manager,
            "manager_llm": self.strong_model,
            "memory": True,
            "planning": True,
            "verbose": 2,
            "step_callback": self._step_callback,
        }
        embedder = self._resolve_embedder()
        if embedder is not None:
            crew_kwargs["embedder"] = embedder
        return Crew(
            **crew_kwargs,
        )


def build_weekly_report_crew() -> Crew:
    return WeeklyReportCrewBuilder().build()
