#!/usr/bin/env python
"""Remove emoji from Python files to fix Windows console encoding issues."""

import re
from pathlib import Path

# Emoji mappings to ASCII
EMOJI_MAP = {
    # Success
    "[OK]": "[OK]",
    "[OK]": "[OK]",
    "[OK]": "[OK]",
    # Errors
    "[ERROR]": "[ERROR]",
    "[ERROR]": "[ERROR]",
    "[ERROR]": "[ERROR]",
    # Warnings
    "[WARN]": "[WARN]",
    "[WARN]️": "[WARN]",
    "[WARN]": "[WARN]",
    # Status
    "[START]": "[START]",
    "[STOP]": "[STOP]",
    "[READY]": "[READY]",
    # Actions
    "[TARGET]": "[TARGET]",
    "[MSG]": "[MSG]",
    "[NOTE]": "[NOTE]",
    "[MENU]": "[MENU]",
    "[BOT]": "[BOT]",
    "[CHART]": "[DATA]",
    "[FIX]": "[FIX]",
    "[CHART]": "[CHART]",
    # Heartbeat
    "[HEART]": "[HEART]",
}

def replace_emoji(content: str) -> str:
    """Replace all emoji with ASCII equivalents."""
    for emoji, replacement in EMOJI_MAP.items():
        content = content.replace(emoji, replacement)
    return content

def process_file(file_path: Path) -> bool:
    """Process a single Python file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        new_content = replace_emoji(content)
        
        if content != new_content:
            file_path.write_text(new_content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Process all Python files in backend directory."""
    backend_dir = Path(__file__).parent.parent
    py_files = list(backend_dir.rglob("*.py"))
    
    # Exclude virtual environment and cache
    py_files = [f for f in py_files if '.venv' not in str(f) and '__pycache__' not in str(f)]
    
    changed = 0
    for file_path in py_files:
        if process_file(file_path):
            changed += 1
            print(f"Fixed: {file_path.relative_to(backend_dir)}")
    
    print(f"\nTotal files changed: {changed}")

if __name__ == "__main__":
    main()
