from types import SimpleNamespace

from crewai_reporter import agents as agents_module
from crewai_reporter import crew as crew_module
from crewai_reporter import tasks as tasks_module
from crewai_reporter.agents import build_agents
from crewai_reporter.crew import build_crew
from crewai_reporter.tasks import build_tasks


def test_build_agents_has_researcher_and_analyst(monkeypatch) -> None:
    def fake_agent(*, role, goal, backstory, verbose, allow_delegation):
        return SimpleNamespace(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=verbose,
            allow_delegation=allow_delegation,
        )

    monkeypatch.setattr(agents_module, "Agent", fake_agent)
    agents = build_agents()
    roles = [agent.role for agent in agents]
    assert len(agents) == 2
    assert roles == ["Researcher", "Analyst"]


def test_build_tasks_returns_research_then_analysis(monkeypatch) -> None:
    def fake_task(*, description, expected_output, agent):
        return SimpleNamespace(
            description=description, expected_output=expected_output, agent=agent
        )

    monkeypatch.setattr(tasks_module, "Task", fake_task)
    researcher = SimpleNamespace(role="Researcher")
    analyst = SimpleNamespace(role="Analyst")
    tasks = build_tasks("AI in education", researcher=researcher, analyst=analyst)
    assert len(tasks) == 2
    assert "Research the topic" in tasks[0].description
    assert "Using the research brief" in tasks[1].description


def test_build_crew_instantiates_sequential_flow(monkeypatch) -> None:
    researcher = SimpleNamespace(role="Researcher")
    analyst = SimpleNamespace(role="Analyst")
    fake_tasks = [SimpleNamespace(name="research"), SimpleNamespace(name="analysis")]

    monkeypatch.setattr(crew_module, "build_researcher", lambda: researcher)
    monkeypatch.setattr(crew_module, "build_analyst", lambda: analyst)
    monkeypatch.setattr(
        crew_module,
        "build_tasks",
        lambda topic, researcher, analyst: fake_tasks,
    )

    captured = {}

    def fake_crew(*, agents, tasks, process, verbose):
        captured["agents"] = agents
        captured["tasks"] = tasks
        captured["process"] = process
        captured["verbose"] = verbose
        return SimpleNamespace(agents=agents, tasks=tasks, process=process, verbose=verbose)

    monkeypatch.setattr(crew_module, "Crew", fake_crew)
    crew = build_crew("AI for climate risk modeling")
    assert len(crew.agents) == 2
    assert len(crew.tasks) == 2
    assert captured["process"] == crew_module.Process.sequential
