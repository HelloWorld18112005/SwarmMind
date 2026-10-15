from typing import Any
from app.memory.service import MemoryService


class MemorySearchTool:
    """Tool enabling agents to search project graph memories and find existing claims."""

    def __init__(self, memory_service: MemoryService) -> None:
        self.service = memory_service

    async def search(self, project_id: str, query: str = "", limit: int = 20) -> list[dict[str, Any]]:
        memories = await self.service.list_memories(project_id, query=query, limit=limit)
        return [
            {
                "id": m.id,
                "content": m.content,
                "type": m.memory_type,
                "confidence": m.confidence,
                "tags": m.tags,
            }
            for m in memories
        ]
