from pathlib import Path

DEFAULT_TOPIC = "The impact of AI agents on modern research workflows"
OUTPUT_DIR = Path("outputs")
OUTPUT_FILE = OUTPUT_DIR / "final_report.md"

RESEARCHER_ROLE = "Researcher"
RESEARCHER_GOAL = "Collect accurate, high-value findings about the topic."
RESEARCHER_BACKSTORY = (
    "You are a precise research specialist focused on identifying trustworthy "
    "information, themes, and evidence."
)

ANALYST_ROLE = "Analyst"
ANALYST_GOAL = "Synthesize findings into a clear, actionable report."
ANALYST_BACKSTORY = (
    "You are an analytical writer who turns raw findings into concise, "
    "well-structured insights for decision-makers."
)
