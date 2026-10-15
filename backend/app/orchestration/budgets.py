import time
from typing import Any
from app.config import Settings, get_settings


class BudgetEnforcer:
    """Enforces agent step limits, token usage, cost accounting, and execution duration."""

    # Pricing per 1M tokens ($0.50 input / $1.50 output standard baseline)
    PROMPT_COST_PER_MILLION = 0.50
    COMPLETION_COST_PER_MILLION = 1.50

    def __init__(self, settings: Settings | None = None, run_id: str = "default-run") -> None:
        cfg = settings or get_settings()
        self.run_id = run_id
        self.max_concurrent_agents = cfg.max_concurrent_agents
        self.max_agent_steps = cfg.max_agent_steps
        self.max_run_duration_seconds = cfg.max_run_duration_seconds
        self.max_budget_usd: float = 5.0  # $5.00 default run limit

        self.start_time: float = time.time()
        self.step_counts: dict[str, int] = {}
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0

    @property
    def total_steps(self) -> int:
        return sum(self.step_counts.values())

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def elapsed_seconds(self) -> float:
        return round(time.time() - self.start_time, 2)

    @property
    def estimated_cost_usd(self) -> float:
        input_cost = (self.prompt_tokens / 1_000_000.0) * self.PROMPT_COST_PER_MILLION
        output_cost = (self.completion_tokens / 1_000_000.0) * self.COMPLETION_COST_PER_MILLION
        return round(input_cost + output_cost, 6)

    def record_agent_step(self, agent_role: str) -> None:
        count = self.step_counts.get(agent_role, 0) + 1
        if count > self.max_agent_steps:
            raise RuntimeError(
                f"Agent budget exceeded for '{agent_role}': {count} steps > limit {self.max_agent_steps}"
            )
        self.step_counts[agent_role] = count

    def record_tokens(self, prompt: int, completion: int) -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        if self.estimated_cost_usd > self.max_budget_usd:
            raise RuntimeError(
                f"Cost budget exceeded for run '{self.run_id}': ${self.estimated_cost_usd:.4f} > limit ${self.max_budget_usd:.2f}"
            )

    def check_duration(self) -> None:
        elapsed = time.time() - self.start_time
        if elapsed > self.max_run_duration_seconds:
            raise TimeoutError(
                f"Investigation run timed out: {elapsed:.1f}s exceeded limit of {self.max_run_duration_seconds}s"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": "within_budget" if self.estimated_cost_usd <= self.max_budget_usd else "exceeded",
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "max_budget_usd": self.max_budget_usd,
            "step_count": self.total_steps,
            "max_steps": self.max_agent_steps * 6,
            "elapsed_seconds": self.elapsed_seconds,
            "max_duration_seconds": self.max_run_duration_seconds,
            "agent_step_breakdown": self.step_counts,
        }


# Global run budget registry for API queries
RUN_BUDGET_REGISTRY: dict[str, BudgetEnforcer] = {}


def get_or_create_run_budget(run_id: str, settings: Settings | None = None) -> BudgetEnforcer:
    if run_id not in RUN_BUDGET_REGISTRY:
        RUN_BUDGET_REGISTRY[run_id] = BudgetEnforcer(settings, run_id=run_id)
    return RUN_BUDGET_REGISTRY[run_id]
