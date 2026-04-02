from crewai import Crew, Process

from .agents import build_analyst, build_researcher
from .tasks import build_tasks


def build_crew(topic: str) -> Crew:
    researcher = build_researcher()
    analyst = build_analyst()
    tasks = build_tasks(topic=topic, researcher=researcher, analyst=analyst)

    return Crew(
        agents=[researcher, analyst],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
