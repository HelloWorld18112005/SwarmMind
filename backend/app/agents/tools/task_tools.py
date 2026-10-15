from typing import Any
from app.graph.base import GraphRepository


class TaskTool:
    """Tool enabling agents to fetch prerequisite task results and report output summaries."""

    def __init__(self, repo: GraphRepository) -> None:
        self.repo = repo

    async def get_prerequisite_results(self, task_id: str) -> dict[str, Any]:
        task = await self.repo.get_task(task_id)
        if not task:
            return {}
        results = {}
        for dep_id in task.dependencies:
            dep_task = await self.repo.get_task(dep_id)
            if dep_task and dep_task.result:
                results[dep_id] = {
                    "title": dep_task.title,
                    "role": dep_task.assigned_role,
                    "result": dep_task.result,
                }
        return results
