from crewai import Agent

from . import config


def build_researcher() -> Agent:
    return Agent(
        role=config.RESEARCHER_ROLE,
        goal=config.RESEARCHER_GOAL,
        backstory=config.RESEARCHER_BACKSTORY,
        verbose=True,
        allow_delegation=False,
    )


def build_analyst() -> Agent:
    return Agent(
        role=config.ANALYST_ROLE,
        goal=config.ANALYST_GOAL,
        backstory=config.ANALYST_BACKSTORY,
        verbose=True,
        allow_delegation=False,
    )


def build_agents() -> list[Agent]:
    return [build_researcher(), build_analyst()]
