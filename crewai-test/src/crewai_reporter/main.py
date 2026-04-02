import sys
import os

from dotenv import load_dotenv

from .config import DEFAULT_TOPIC, OUTPUT_FILE
from .crew import build_crew


def run(topic: str) -> str:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY") and os.getenv("DEEPSEEK_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.environ["DEEPSEEK_API_KEY"]
    if not os.getenv("OPENAI_BASE_URL") and os.getenv("DEEPSEEK_API_KEY"):
        os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com"
    if not os.getenv("OPENAI_MODEL_NAME") and os.getenv("DEEPSEEK_API_KEY"):
        os.environ["OPENAI_MODEL_NAME"] = "deepseek-chat"
    crew = build_crew(topic=topic)
    result = crew.kickoff()
    report_text = str(result)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(report_text, encoding="utf-8")
    return report_text


def main() -> None:
    topic = " ".join(sys.argv[1:]).strip() or DEFAULT_TOPIC
    report_text = run(topic)
    print(f"Topic: {topic}")
    print(f"Report saved to: {OUTPUT_FILE}")
    print()
    print(report_text)


if __name__ == "__main__":
    main()
