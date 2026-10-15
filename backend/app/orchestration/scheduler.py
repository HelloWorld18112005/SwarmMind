from typing import Sequence
from app.schemas.task import Task


class DependencyScheduler:
    """Evaluates task prerequisites and determines ready-to-execute tasks in DAG order."""

    def __init__(self, max_concurrent: int = 3) -> None:
        self.max_concurrent = max_concurrent

    def get_ready_tasks(
        self,
        all_tasks: Sequence[Task],
        currently_running_count: int = 0,
    ) -> list[Task]:
        """Return tasks whose dependencies are all completed and are ready to execute."""
        completed_task_ids = {t.id for t in all_tasks if t.status == "completed"}
        available_slots = max(0, self.max_concurrent - currently_running_count)
        if available_slots == 0:
            return []

        ready_tasks: list[Task] = []
        for task in all_tasks:
            if task.status in ("pending", "ready"):
                # Check if all prerequisite tasks are completed
                deps_met = all(dep in completed_task_ids for dep in task.dependencies)
                if deps_met:
                    ready_tasks.append(task)
                    if len(ready_tasks) >= available_slots:
                        break

        return ready_tasks

    def is_run_finished(self, all_tasks: Sequence[Task]) -> tuple[bool, str]:
        """Check if all tasks are in terminal states. Returns (is_done, final_status)."""
        if not all_tasks:
            return False, "pending"

        terminal_states = {"completed", "failed", "cancelled"}
        all_terminal = all(t.status in terminal_states for t in all_tasks)

        if not all_terminal:
            return False, "running"

        if any(t.status == "failed" for t in all_tasks):
            return True, "failed"
        if any(t.status == "cancelled" for t in all_tasks):
            return True, "cancelled"

        return True, "completed"
