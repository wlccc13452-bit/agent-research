from crewai import Agent, Task


def build_tasks(topic: str, researcher: Agent, analyst: Agent) -> list[Task]:
    research_task = Task(
        description=(
            f"Research the topic: {topic}. Identify major themes, reliable facts, "
            "important trends, and supporting evidence."
        ),
        expected_output=(
            "A structured research brief with key findings, bullet points, and "
            "evidence-backed observations."
        ),
        agent=researcher,
    )

    analysis_task = Task(
        description=(
            "Using the research brief from the Researcher, write a final report "
            "with an executive summary, key insights, risks, opportunities, and "
            "a conclusion."
        ),
        expected_output=(
            "A polished markdown report suitable for stakeholders and decision-makers."
        ),
        agent=analyst,
    )

    return [research_task, analysis_task]
