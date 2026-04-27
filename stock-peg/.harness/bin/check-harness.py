#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Harness Integrity Checker - Enhanced with Anti-Forgery Verification

Exit codes: 0 = PASS, 1 = FAIL
"""

import sys
import json
import re
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass


def parse_progress_entries(content: str):
    entries = []
    current_date = None
    current_lines = []
    for line in content.splitlines():
        date_match = re.match(r"^###\s+(\d{4}-\d{2}-\d{2})", line.strip())
        if date_match:
            if current_lines:
                entries.append({"date": current_date, "text": "\n".join(current_lines)})
                current_lines = []
            current_date = date_match.group(1)
            continue
        if line.startswith("- [x] "):
            if current_lines:
                entries.append({"date": current_date, "text": "\n".join(current_lines)})
            current_lines = [line]
            continue
        if current_lines:
            if line.startswith("### "):
                entries.append({"date": current_date, "text": "\n".join(current_lines)})
                current_lines = []
            else:
                current_lines.append(line)
    if current_lines:
        entries.append({"date": current_date, "text": "\n".join(current_lines)})
    return entries


def extract_agent_name(entry_text: str) -> str:
    agent_match = re.search(r"\*\*Agent\*\*:\s*([^\n]+)", entry_text)
    if not agent_match:
        return ""
    return agent_match.group(1).strip().strip("`")


def extract_test_temp_paths(entry_text: str):
    paths = re.findall(r"test/temp/[A-Za-z0-9._\-/]+", entry_text)
    cleaned = []
    for path in paths:
        normalized = path.rstrip(".,)]`\"'")
        if "<task>" in normalized:
            continue
        cleaned.append(normalized)
    return list(dict.fromkeys(cleaned))


def extract_contract_hash(entry_text: str) -> str:
    match = re.search(r"api-contract\.md#md5=([a-fA-F0-9]{32}|PENDING_GENERATION)", entry_text)
    if not match:
        return ""
    return match.group(1).lower()


def extract_contract_md5_from_contract(contract_path: Path) -> str:
    if not contract_path.exists():
        return ""
    content = contract_path.read_text(encoding='utf-8', errors='ignore')
    match = re.search(r"\|\s*Contract MD5\s*\|\s*`?([a-fA-F0-9]{32}|PENDING_GENERATION)`?\s*\|", content)
    if not match:
        return ""
    return match.group(1).lower()


def main():
    """Main integrity checker."""
    root = Path.cwd()
    harness_dir = root / ".harness"
    test_dir = root / "test" / "temp"
    
    print("[CHECK] Harness Integrity Checker")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # ========================================
    # Phase 1: Core Files Check
    # ========================================
    print("\n[CORE_FILES]")
    core_files = [
        "AGENTS.md",
        "progress.md",
        "decisions.md",
        "memory/core-facts.md",
    ]
    
    for file_path in core_files:
        full_path = harness_dir / file_path
        if full_path.exists():
            print(f"  [PASS] {file_path}")
        else:
            print(f"  [FAIL] {file_path} - MISSING")
            errors.append(f"Missing core file: {file_path}")
    
    # ========================================
    # Phase 2: Skills Registry Check
    # ========================================
    print("\n[SKILLS_REGISTRY]")
    skills_registry = harness_dir / "skills" / "registry.json"
    
    if skills_registry.exists():
        try:
            with open(skills_registry, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print("  [PASS] registry.json parse")
            
            # Check command paths
            commands = data.get("commands", {})
            for cmd_name, cmd_info in commands.items():
                skill_path = cmd_info.get("path", "")
                if skill_path:
                    full_path = root / skill_path
                    if full_path.exists():
                        print(f"  [PASS] {cmd_name} path")
                    else:
                        print(f"  [FAIL] {cmd_name} path - BROKEN: {skill_path}")
                        errors.append(f"Broken skill path: {cmd_name}")
        except Exception as e:
            print(f"  [FAIL] registry.json parse - ERROR: {str(e)}")
            errors.append(f"Registry parse error: {str(e)}")
    else:
        print("  [FAIL] registry.json - MISSING")
        errors.append("Missing skills registry.json")
    
    # ========================================
    # Phase 3: Reference Registry Check (NEW)
    # ========================================
    print("\n[REFERENCE_REGISTRY]")
    ref_registry = harness_dir / "reference" / "registry.json"
    
    if ref_registry.exists():
        try:
            with open(ref_registry, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print("  [PASS] registry.json parse")
            
            # Check document paths
            documents = data.get("documents", {})
            missing_files = []
            
            for doc_path, doc_info in documents.items():
                full_path = harness_dir / "reference" / doc_path
                if not full_path.exists():
                    missing_files.append(doc_path)
            
            if missing_files:
                print(f"  [FAIL] Document paths - MISSING {len(missing_files)} files")
                errors.append(f"Missing reference files: {', '.join(missing_files[:3])}")
            else:
                print(f"  [PASS] Document paths - All {len(documents)} exist")
            
            # Check for unregistered files
            reference_dir = harness_dir / "reference"
            unregistered = []
            
            ignored_unregistered_prefixes = (
                "project-specific/data-sources/tushare-api/references/",
                "project-specific/data-sources/tushare-api/example/",
            )
            ignored_unregistered_files = {
                "index.md",
                "QUALITY-STANDARDS.md",
                "SKILL-UPDATE-PROTOCOL.md",
            }

            for md_file in reference_dir.rglob("*.md"):
                if md_file.name == "README.md":
                    continue
                
                rel_path = str(md_file.relative_to(reference_dir)).replace("\\", "/")
                if rel_path in ignored_unregistered_files:
                    continue
                if any(rel_path.startswith(prefix) for prefix in ignored_unregistered_prefixes):
                    continue
                
                if rel_path not in documents:
                    unregistered.append(rel_path)
            
            if unregistered:
                print(f"  [WARN] Unregistered files - FOUND {len(unregistered)}")
                warnings.append(f"Unregistered reference files: {len(unregistered)}")
            else:
                print("  [PASS] Unregistered files - None found")
        
        except Exception as e:
            print(f"  [FAIL] registry.json parse - ERROR: {str(e)}")
            errors.append(f"Reference registry error: {str(e)}")
    else:
        print("  [FAIL] registry.json - MISSING")
        errors.append("Missing reference registry.json")
    
    # ========================================
    # Phase 4: AGENTS.md Size Check
    # ========================================
    print("\n[AGENTS_CONSTRAINT]")
    agents_path = harness_dir / "AGENTS.md"
    
    if agents_path.exists():
        lines = agents_path.read_text(encoding='utf-8').splitlines()
        line_count = len(lines)
        
        if line_count <= 300:
            print(f"  [PASS] AGENTS.md size - {line_count}/300 lines")
        else:
            print(f"  [FAIL] AGENTS.md size - EXCEEDS LIMIT: {line_count}/300 lines")
            errors.append(f"AGENTS.md exceeds limit: {line_count} lines")
    
    # ========================================
    # Phase 5: Verification Evidence Check (NEW)
    # ========================================
    print("\n[VERIFICATION_EVIDENCE]")
    progress_path = harness_dir / "progress.md"
    contract_path = harness_dir / "reference" / "project-specific" / "api-contract.md"
    
    # Initialize variables for later phases
    test_refs = []
    unique_tasks = set()
    
    if progress_path.exists():
        content = progress_path.read_text(encoding='utf-8')
        
        # Find test/temp references
        test_refs = [
            task for task in re.findall(r'test/temp/([^/\s]+)/', content)
            if task and task != "<task>"
        ]
        
        if test_refs:
            unique_tasks = set(test_refs[:5])  # Check first 5 tasks
            
            for task_id in unique_tasks:
                task_dir = test_dir / task_id
                
                if task_dir.exists():
                    log_files = list(task_dir.glob("*.log")) + list(task_dir.glob("*.json"))
                    
                    if log_files:
                        print(f"  [PASS] Task {task_id} - Physical evidence exists")
                    else:
                        print(f"  [FAIL] Task {task_id} - NO LOG FILES")
                        errors.append(f"Missing test logs: {task_id}")
                else:
                    print(f"  [FAIL] Task {task_id} - Directory MISSING")
                    errors.append(f"Missing test directory: {task_id}")
        else:
            print("  [PASS] No test references to verify")

    print("\n[MUNGER_INVERSION_GUARDS]")
    if progress_path.exists():
        progress_content = progress_path.read_text(encoding='utf-8')
        entries = parse_progress_entries(progress_content)
        identity_cutoff = "2026-03-21"
        expected_contract_md5 = extract_contract_md5_from_contract(contract_path)

        if not expected_contract_md5:
            errors.append("api-contract.md missing Contract MD5 metadata")
            print("  [FAIL] api-contract.md - Missing Contract MD5 metadata")
        elif expected_contract_md5 == "pending_generation":
            errors.append("api-contract.md Contract MD5 is still pending")
            print("  [FAIL] api-contract.md - Contract MD5 still pending")
        else:
            print("  [PASS] api-contract.md - Contract MD5 metadata valid")

        for idx, entry in enumerate(entries, start=1):
            entry_date = entry.get("date") or ""
            entry_text = entry.get("text", "")
            lower_text = entry_text.lower()

            if entry_date >= identity_cutoff and not re.search(r"Executed By", entry_text):
                errors.append(f"Missing Executed By tag in progress entry #{idx} ({entry_date})")
                print(f"  [FAIL] Entry #{idx} ({entry_date}) - Missing Executed By tag")

            if entry_date >= identity_cutoff:
                contract_md5 = extract_contract_hash(entry_text)
                if not contract_md5:
                    errors.append(f"Missing Contract hash in progress entry #{idx} ({entry_date})")
                    print(f"  [FAIL] Entry #{idx} ({entry_date}) - Missing Contract hash")
                elif contract_md5 == "pending_generation":
                    errors.append(f"Pending Contract hash in progress entry #{idx} ({entry_date})")
                    print(f"  [FAIL] Entry #{idx} ({entry_date}) - Contract hash still pending")
                elif expected_contract_md5 and expected_contract_md5 != "pending_generation" and contract_md5 != expected_contract_md5:
                    errors.append(f"Contract hash mismatch in progress entry #{idx} ({entry_date})")
                    print(f"  [FAIL] Entry #{idx} ({entry_date}) - Contract hash mismatch")

            agent_name = extract_agent_name(entry_text).lower()
            if "backend-node" in agent_name and re.search(r"(^|[\s`])frontend/", lower_text):
                errors.append(f"Boundary violation in entry #{idx}: Backend-Node modified frontend path")
                print(f"  [FAIL] Entry #{idx} - Backend-Node touched frontend path")
            if "frontend-node" in agent_name and re.search(r"(^|[\s`])backend/", lower_text):
                errors.append(f"Boundary violation in entry #{idx}: Frontend-Node modified backend path")
                print(f"  [FAIL] Entry #{idx} - Frontend-Node touched backend path")

            peg_sensitive = entry_date >= identity_cutoff and (
                "peg" in lower_text
                or "force_index" in lower_text
                or "pmr_calculator" in lower_text
            )
            if peg_sensitive:
                evidence_paths = extract_test_temp_paths(entry_text)
                if not evidence_paths:
                    errors.append(f"PEG evidence missing in entry #{idx}: no test/temp path")
                    print(f"  [FAIL] Entry #{idx} - PEG change without physical evidence path")
                    continue
                existing = any((root / rel_path).exists() for rel_path in evidence_paths)
                if not existing:
                    errors.append(f"PEG evidence missing in entry #{idx}: referenced path not found")
                    print(f"  [FAIL] Entry #{idx} - PEG evidence path not found on disk")
                else:
                    print(f"  [PASS] Entry #{idx} - PEG evidence path verified")
    
    # ========================================
    # Phase 6: Anti-Forgery & Sanitization (D038 Enhanced)
    # ========================================
    print("\n[ANTI_FORGERY_&_SANITIZATION]")
    import time
    
    # Check session summaries for absolute path leaks
    summaries_dir = harness_dir / "memory" / "session-summaries"
    if summaries_dir.exists():
        for summary in summaries_dir.glob("*.md"):
            content = summary.read_text(encoding='utf-8', errors='ignore')
            
            # Remove code blocks to avoid false positives
            content_no_code = re.sub(r'```[\s\S]*?```', '', content)
            
            # Enhanced absolute path patterns (Windows + Unix + year-based paths)
            path_patterns = [
                r'[A-Z]:[\\/](?:[^:\s\)`\\/\n]+[\\/])+',  # Windows: C:\Users\..., E:\2025Projects\...
                r'/(?:Users|home|mnt|var|opt)/[^\s\)`]+',  # Unix: /Users/..., /home/..., /mnt/...
                r'\\\\[^\\]+\\[^\s\)`]+',  # UNC paths: \\server\share\...
            ]
            
            all_leaks = []
            for pattern in path_patterns:
                leaks = re.findall(pattern, content_no_code)
                all_leaks.extend(leaks)
            
            # Filter out allowed paths (project-relative, temp, etc.)
            allowed_patterns = [
                r'[A-Z]:[\\/][^\\/]+[\\/]\.harness',  # Project .harness paths
                r'[A-Z]:[\\/][^\\/]+[\\/]test[\\/]temp',  # Project test paths
                r'/\.\.harness',  # Relative harness paths
            ]
            
            filtered_leaks = []
            for leak in all_leaks:
                is_allowed = any(re.match(allowed, leak) for allowed in allowed_patterns)
                if not is_allowed and len(leak) > 10:  # Ignore short matches
                    filtered_leaks.append(leak)
            
            if filtered_leaks:
                errors.append(f"Absolute paths leaked in {summary.name}: {filtered_leaks[:3]}")
                print(f"  [FAIL] {summary.name} - Local environment paths detected:")
                for leak in filtered_leaks[:3]:
                    print(f"         → {leak}")
    
    # Deep verify task logs for environment fingerprints
    if test_refs:
        for task_id in unique_tasks:
            task_dir = test_dir / task_id
            if task_dir.exists():
                logs = list(task_dir.glob("*.log")) + list(task_dir.glob("*.json"))
                if logs:
                    # Check for environment fingerprints (hard to fake)
                    valid_log = False
                    forgery_indicators = []
                    
                    for log_file in logs:
                        file_size = log_file.stat().st_size
                        content = log_file.read_text(encoding='utf-8', errors='ignore')
                        
                        # Check 1: File size (empty files are suspicious)
                        if file_size < 100:
                            forgery_indicators.append(f"File too small ({file_size} bytes)")
                            continue
                        
                        # Check 2: Comprehensive pytest fingerprints
                        pytest_fingerprints = [
                            "test session starts",
                            "collected",
                            "passed",
                            "platform win32",
                            "rootdir:",
                            "plugins:",
                            "cachedir:",
                            "Python 3.13",
                        ]
                        
                        # Check 3: Time-based fingerprints (real logs have timestamps)
                        timestamp_patterns = [
                            r'\d{4}-\d{2}-\d{2}',  # Date: 2026-03-19
                            r'\d{2}:\d{2}:\d{2}',  # Time: 14:30:45
                        ]
                        
                        # Count matched fingerprints
                        matched_fingerprints = sum(1 for f in pytest_fingerprints if f in content)
                        has_timestamps = any(re.search(p, content) for p in timestamp_patterns)
                        
                        # Validation criteria: at least 3 pytest fingerprints OR 2 fingerprints + timestamp
                        if matched_fingerprints >= 3 or (matched_fingerprints >= 2 and has_timestamps):
                            valid_log = True
                            break
                        else:
                            if matched_fingerprints < 2:
                                forgery_indicators.append(f"Insufficient pytest fingerprints ({matched_fingerprints}/3 required)")
                            if not has_timestamps:
                                forgery_indicators.append("No timestamp metadata")
                    
                    if not valid_log:
                        error_msg = f"Task {task_id} logs failed integrity check (Possible Forgery)"
                        if forgery_indicators:
                            error_msg += f": {', '.join(forgery_indicators[:2])}"
                        errors.append(error_msg)
                        print(f"  [FAIL] {task_id} - Integrity check failed:")
                        for indicator in forgery_indicators[:2]:
                            print(f"         → {indicator}")
    
    # ========================================
    # Phase 7: Memory Lifecycle Validation (D038)
    # ========================================
    print("\n[MEMORY_LIFECYCLE]")
    
    # Check auditor reports retention with detailed expiry info
    auditor_dir = harness_dir / "memory" / "auditor-reports"
    if auditor_dir.exists():
        now = time.time()
        expired_reports = []  # List of (filename, days_old) tuples
        
        for report in auditor_dir.glob("*.md"):
            file_age_seconds = now - report.stat().st_mtime
            file_age_days = int(file_age_seconds / 86400)
            
            # Flag files older than 90 days
            if file_age_days > 90:
                expired_reports.append((report.name, file_age_days))
        
        if expired_reports:
            # Sort by age (oldest first)
            expired_reports.sort(key=lambda x: x[1], reverse=True)
            
            print(f"  [WARN] ⚠️  {len(expired_reports)} auditor report(s) EXCEEDED 90-day retention:")
            for filename, days in expired_reports[:3]:
                print(f"         → {filename} ({days} days old)")
            
            if len(expired_reports) > 3:
                print(f"         ... and {len(expired_reports) - 3} more")
            
            warnings.append(
                f"⚠️  {len(expired_reports)} expired auditor reports (oldest: {expired_reports[0][1]} days). "
                f"Run /maintenance to archive."
            )
        else:
            print("  [PASS] All auditor reports within 90-day retention period")
    
    # Check maintenance logs retention with detailed expiry info
    logs_dir = harness_dir / "memory" / "maintenance-logs"
    if logs_dir.exists():
        now = time.time()
        expired_logs = []  # List of (filename, days_old) tuples
        
        for log in logs_dir.glob("*.md"):
            file_age_seconds = now - log.stat().st_mtime
            file_age_days = int(file_age_seconds / 86400)
            
            # Flag files older than 60 days
            if file_age_days > 60:
                expired_logs.append((log.name, file_age_days))
        
        if expired_logs:
            # Sort by age (oldest first)
            expired_logs.sort(key=lambda x: x[1], reverse=True)
            
            print(f"  [WARN] ⚠️  {len(expired_logs)} maintenance log(s) EXCEEDED 60-day retention:")
            for filename, days in expired_logs[:3]:
                print(f"         → {filename} ({days} days old)")
            
            if len(expired_logs) > 3:
                print(f"         ... and {len(expired_logs) - 3} more")
            
            warnings.append(
                f"⚠️  {len(expired_logs)} expired maintenance logs. Run /maintenance to cleanup."
            )
        else:
            print("  [PASS] All maintenance logs within 60-day retention period")
    
    # Check archives directory structure
    archives_dir = harness_dir / "memory" / "archives"
    if archives_dir.exists():
        # Check for subdirectories (should be files only)
        subdirs = [d for d in archives_dir.iterdir() if d.is_dir() and d.name != "tasks"]
        
        if subdirs:
            print(f"  [FAIL] Archives contains {len(subdirs)} subdirectories (should be files only)")
            errors.append(f"Inconsistent archives structure: {', '.join([d.name for d in subdirs[:3]])}")
        else:
            print("  [PASS] Archives structure consistent (files only)")
        
        # Check README.md exists
        archives_readme = archives_dir / "README.md"
        if not archives_readme.exists():
            print("  [WARN] Archives missing README.md index")
            warnings.append("Archives missing README.md - run /maintenance to create")
    
    # ========================================
    # Summary
    # ========================================
    print("\n" + "=" * 60)
    
    if warnings:
        print(f"\n[WARNINGS] {len(warnings)} warnings:")
        for warning in warnings[:3]:
            print(f"  - {warning}")
    
    if errors:
        print(f"\n[ERRORS] {len(errors)} errors detected:")
        for error in errors:
            print(f"  - {error}")
        print("\n[FAIL] HARNESS_INTEGRITY_FAILURE")
        return 1
    else:
        print("\n[PASS] HARNESS_INTEGRITY_PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
