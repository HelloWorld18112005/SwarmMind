from pathlib import Path
from typing import Any, Type

from app.agents.base import BaseAgent
from app.agents.coordinator import CoordinatorAgent
from app.agents.researcher import ResearcherAgent
from app.agents.analyst import AnalystAgent
from app.agents.critic import CriticAgent
from app.agents.planner import PlannerAgent
from app.agents.synthesizer import SynthesizerAgent
from app.llm.base import LLMProvider
from app.memory.service import MemoryService

PROMPTS_DIR = Path(__file__).parent / "prompts"

ROLE_MAP: dict[str, Type[BaseAgent[Any]]] = {
    "coordinator": CoordinatorAgent,
    "researcher": ResearcherAgent,
    "analyst": AnalystAgent,
    "critic": CriticAgent,
    "planner": PlannerAgent,
    "synthesizer": SynthesizerAgent,
}


def load_prompt(role: str) -> str:
    prompt_file = PROMPTS_DIR / f"{role}.md"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    return f"You are the {role} agent in SwarmMind."


def create_agent(
    role: str,
    agent_id: str,
    llm: LLMProvider,
    memory_service: MemoryService,
) -> BaseAgent[Any]:
    """Factory to instantiate an agent by role string."""
    agent_cls = ROLE_MAP.get(role.lower())
    if not agent_cls:
        raise ValueError(f"Unknown agent role: '{role}'. Available: {list(ROLE_MAP.keys())}")
    prompt = load_prompt(role.lower())
    return agent_cls(
        agent_id=agent_id,
        llm=llm,
        memory_service=memory_service,
        prompt=prompt,
    )
