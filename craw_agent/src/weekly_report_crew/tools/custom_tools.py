from __future__ import annotations

import json
from pathlib import Path
from typing import List

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class WeeklyDataLoaderInput(BaseModel):
    week_period: str = Field(..., description="Week label or date range")
    focus: str = Field(default="", description="Optional reporting focus")
    max_files: int = Field(default=20, ge=1, le=200, description="Maximum number of files to read")


class WeeklyDataLoaderTool(BaseTool):
    name: str = "weekly_data_loader"
    description: str = "Load weekly internal notes and artifacts from local folders by period and focus."
    args_schema: type[BaseModel] = WeeklyDataLoaderInput
    base_path: str = "src/weekly_report_crew/data/weekly_notes"

    def _run(self, week_period: str, focus: str = "", max_files: int = 20) -> str:
        folder = Path(self.base_path)
        if not folder.exists():
            return json.dumps(
                {
                    "internal_sources": [],
                    "raw_text": "",
                    "warning": "weekly notes directory not found",
                },
                ensure_ascii=False,
            )

        terms: List[str] = [week_period.lower().strip()]
        if focus.strip():
            terms.extend(token for token in focus.lower().split() if token.strip())

        candidates = sorted(
            [path for path in folder.rglob("*") if path.is_file()],
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        selected: List[Path] = []
        for path in candidates:
            filename = path.name.lower()
            if any(term in filename for term in terms):
                selected.append(path)
            if len(selected) >= max_files:
                break

        if not selected:
            selected = candidates[: min(max_files, len(candidates))]

        sources: List[str] = []
        chunks: List[str] = []
        for path in selected:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                content = ""
            sources.append(str(path))
            chunks.append(f"FILE: {path}\n{content[:8000]}")

        payload = {
            "internal_sources": sources,
            "raw_text": "\n\n".join(chunks),
            "warning": "" if sources else "no files found",
        }
        return json.dumps(payload, ensure_ascii=False)
