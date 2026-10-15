import time
from app.config import Settings, get_settings


class BudgetEnforcer:
    """Enforces agent step limits, maximum execution duration, and concurrency."""

    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or get_settings()
        self.max_concurrent_agents = cfg.max_concurrent_agents
        self.max_agent_steps = cfg.max_agent_steps
        self.max_run_duration_seconds = cfg.max_run_duration_seconds
        self.start_time: float = time.time()
        self.step_counts: dict[str, int] = {}

    def record_agent_step(self, agent_role: str) -> None:
        count = self.step_counts.get(agent_role, 0) + 1
        if count > self.max_agent_steps:
            raise RuntimeError(
                f"Agent budget exceeded for '{agent_role}': {count} steps > limit {self.max_agent_steps}"
            )
        self.step_counts[agent_role] = count

    def check_duration(self) -> None:
        elapsed = time.time() - self.start_time
        if elapsed > self.max_run_duration_seconds:
            raise TimeoutError(
                f"Investigation run timed out: {elapsed:.1f}s exceeded limit of {self.max_run_duration_seconds}s"
            )
