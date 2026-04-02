from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from .crew import build_weekly_report_crew


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="weekly-report-crew")
    parser.add_argument(
        "--week-period",
        default="March 10-16, 2026",
    )
    parser.add_argument(
        "--focus",
        default="AI engineering team progress",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = _parse_args()
    crew = build_weekly_report_crew()
    inputs = {
        "week_period": args.week_period,
        "focus": args.focus,
    }
    crew_output = crew.kickoff(inputs=inputs)
    result_text = str(crew_output)

    output_path = Path(__file__).resolve().parent / "output" / "weekly_report_latest.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result_text, encoding="utf-8")
    summary_payload = {
        "week_period": inputs["week_period"],
        "focus": inputs["focus"],
        "result_markdown_file": str(output_path),
    }
    summary_path = output_path.with_suffix(".json")
    summary_path.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(result_text)
    print(f"\nSaved Markdown report to: {output_path}")
    print(f"Saved run summary to: {summary_path}")


if __name__ == "__main__":
    main()
