from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass
class CheckResult:
    name: str
    ok: bool
    details: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_repo_path(path_text: str) -> str:
    return path_text.strip().replace("\\", "/")


def validate_required_files(root: Path) -> list[CheckResult]:
    required = [
        ".harness/AGENTS.md",
        ".harness/progress.md",
        ".harness/decisions.md",
        ".harness/memory/core-facts.md",
    ]
    results: list[CheckResult] = []
    for item in required:
        target = root / item
        results.append(
            CheckResult(
                name=f"Required file: {item}",
                ok=target.exists(),
                details="exists" if target.exists() else "missing",
            )
        )
    return results


def validate_routing_files(root: Path) -> list[CheckResult]:
    required = [
        ".codebuddy/rules/harness-loader.mdc",
        ".codebuddy/rules/update-memory.mdc",
        ".harness/skills/registry.json",
    ]
    results: list[CheckResult] = []
    for item in required:
        target = root / item
        results.append(
            CheckResult(
                name=f"Routing file: {item}",
                ok=target.exists(),
                details="exists" if target.exists() else "missing",
            )
        )
    return results


def load_registry(root: Path) -> tuple[dict, list[CheckResult]]:
    path = root / ".harness/skills/registry.json"
    if not path.exists():
        return {}, [CheckResult(name="registry.json parse", ok=False, details="file missing")]
    try:
        data = json.loads(read_text(path))
        return data, [CheckResult(name="registry.json parse", ok=True, details="valid JSON")]
    except Exception as exc:
        return {}, [CheckResult(name="registry.json parse", ok=False, details=str(exc))]


def validate_registry_top_level(registry: dict) -> list[CheckResult]:
    results: list[CheckResult] = []
    version = registry.get("version")
    last_updated = registry.get("lastUpdated")
    results.append(
        CheckResult(
            name="Registry field: version",
            ok=isinstance(version, str) and bool(version.strip()),
            details=f"value={version!r}",
        )
    )
    results.append(
        CheckResult(
            name="Registry field: lastUpdated",
            ok=isinstance(last_updated, str) and bool(last_updated.strip()),
            details=f"value={last_updated!r}",
        )
    )
    commands = registry.get("commands")
    results.append(
        CheckResult(
            name="Registry field: commands",
            ok=isinstance(commands, dict),
            details=f"type={type(commands).__name__}",
        )
    )
    return results


def validate_command_coverage(registry: dict) -> list[CheckResult]:
    required_commands = ["/harness", "/update-memory", "/check-harness", "/daily-watchlist"]
    commands = registry.get("commands", {})
    results: list[CheckResult] = []
    for command in required_commands:
        exists = isinstance(commands, dict) and command in commands
        results.append(
            CheckResult(
                name=f"Registry command coverage: {command}",
                ok=exists,
                details="present" if exists else "missing",
            )
        )
    return results


def validate_command_entries(root: Path, registry: dict) -> list[CheckResult]:
    commands = registry.get("commands", {})
    if not isinstance(commands, dict):
        return [CheckResult(name="Registry command entries", ok=False, details="commands is not an object")]

    results: list[CheckResult] = []
    command_pattern = re.compile(r"^/[a-z0-9]+(?:-[a-z0-9]+)*$")
    for command, payload in commands.items():
        if not isinstance(payload, dict):
            results.append(
                CheckResult(
                    name=f"Command {command}: payload type",
                    ok=False,
                    details=f"expected object, got {type(payload).__name__}",
                )
            )
            continue

        has_valid_name = isinstance(command, str) and bool(command_pattern.fullmatch(command))
        results.append(
            CheckResult(
                name=f"Command {command}: name format",
                ok=has_valid_name,
                details="kebab-case with leading slash required",
            )
        )

        command_type = payload.get("type")
        has_type = isinstance(command_type, str) and bool(command_type.strip())
        results.append(
            CheckResult(
                name=f"Command {command}: type",
                ok=has_type,
                details=f"value={command_type!r}",
            )
        )

        primary_skill = payload.get("primarySkill")
        has_primary_skill = isinstance(primary_skill, str) and bool(primary_skill.strip())
        results.append(
            CheckResult(
                name=f"Command {command}: primarySkill",
                ok=has_primary_skill,
                details=f"value={primary_skill!r}",
            )
        )

        if has_primary_skill:
            skill_path = root / normalize_repo_path(primary_skill)
            results.append(
                CheckResult(
                    name=f"Command {command}: primarySkill path exists",
                    ok=skill_path.exists(),
                    details=normalize_repo_path(primary_skill),
                )
            )

    return results


def validate_agents_skill_paths(root: Path) -> list[CheckResult]:
    agents_path = root / ".harness/AGENTS.md"
    if not agents_path.exists():
        return [CheckResult(name="AGENTS skill path check", ok=False, details="AGENTS.md missing")]
    content = read_text(agents_path)
    paths = sorted(set(re.findall(r"\.harness/skills/[^\s`]+/SKILL\.md", content)))
    if not paths:
        return [CheckResult(name="AGENTS skill path check", ok=False, details="no skill paths found")]
    results: list[CheckResult] = []
    for path_text in paths:
        target = root / normalize_repo_path(path_text)
        results.append(
            CheckResult(
                name=f"AGENTS skill path: {path_text}",
                ok=target.exists(),
                details="exists" if target.exists() else "missing",
            )
        )
    return results


def validate_agents_doc_links(root: Path) -> list[CheckResult]:
    agents_path = root / ".harness/AGENTS.md"
    if not agents_path.exists():
        return [CheckResult(name="AGENTS doc link check", ok=False, details="AGENTS.md missing")]
    content = read_text(agents_path)
    raw_links = re.findall(r"(?<!`)`([^`\n]+)`(?!`)", content)
    candidates: set[str] = set()
    for link in raw_links:
        normalized = normalize_repo_path(link)
        if not (normalized.startswith(".harness/") or normalized.startswith(".codebuddy/")):
            continue
        if "*" in normalized or "<" in normalized or ">" in normalized:
            continue
        candidates.add(normalized)
    if not candidates:
        return [CheckResult(name="AGENTS doc link check", ok=False, details="no candidate links found")]
    results: list[CheckResult] = []
    for rel in sorted(candidates):
        target = root / rel
        results.append(
            CheckResult(
                name=f"AGENTS link: {rel}",
                ok=target.exists(),
                details="exists" if target.exists() else "missing",
            )
        )
    return results


def validate_core_facts_section(root: Path) -> list[CheckResult]:
    core_facts = root / ".harness/memory/core-facts.md"
    if not core_facts.exists():
        return [CheckResult(name="core-facts validation baseline", ok=False, details="core-facts.md missing")]
    content = read_text(core_facts)
    found = "Validation Commands Baseline" in content
    return [
        CheckResult(
            name="core-facts validation baseline",
            ok=found,
            details="section found" if found else "section missing",
        )
    ]


def validate_env_not_committed(root: Path) -> list[CheckResult]:
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            text=True,
            capture_output=True,
            check=True,
        )
    except Exception as exc:
        return [CheckResult(name="Tracked .env file check", ok=False, details=f"git ls-files failed: {exc}")]
    tracked = [line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]
    env_files = [p for p in tracked if Path(p).name == ".env"]
    return [
        CheckResult(
            name="Tracked .env file check",
            ok=len(env_files) == 0,
            details="none found" if not env_files else ", ".join(env_files),
        )
    ]


def print_report(results: Iterable[CheckResult]) -> int:
    result_list = list(results)
    passed = sum(1 for r in result_list if r.ok)
    failed = len(result_list) - passed
    print("HARNESS CHECK REPORT")
    print(f"Total: {len(result_list)} | Passed: {passed} | Failed: {failed}")
    for item in result_list:
        mark = "PASS" if item.ok else "FAIL"
        print(f"[{mark}] {item.name} -> {item.details}")
    return 0 if failed == 0 else 1


def to_json_payload(root: Path, results: list[CheckResult]) -> dict:
    passed = sum(1 for item in results if item.ok)
    failed = len(results) - passed
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "projectRoot": str(root),
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "status": "pass" if failed == 0 else "fail",
        },
        "checks": [
            {
                "name": item.name,
                "ok": item.ok,
                "details": item.details,
            }
            for item in results
        ],
    }


def write_json_report(root: Path, results: list[CheckResult], json_out: str) -> Path:
    output_path = Path(json_out)
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = to_json_payload(root, results)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def build_checks(root: Path) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.extend(validate_required_files(root))
    checks.extend(validate_routing_files(root))
    registry, registry_parse_results = load_registry(root)
    checks.extend(registry_parse_results)
    if registry:
        checks.extend(validate_registry_top_level(registry))
        checks.extend(validate_command_coverage(registry))
        checks.extend(validate_command_entries(root, registry))
    checks.extend(validate_agents_skill_paths(root))
    checks.extend(validate_agents_doc_links(root))
    checks.extend(validate_core_facts_section(root))
    checks.extend(validate_env_not_committed(root))
    return checks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run harness health checks.")
    parser.add_argument(
        "--json-out",
        default=".harness/reports/check-harness-latest.json",
        help="Path for JSON check artifact output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[4]
    checks = build_checks(root)
    json_path = write_json_report(root, checks, args.json_out)
    print(f"JSON report: {json_path}")
    return print_report(checks)


if __name__ == "__main__":
    raise SystemExit(main())
