import asyncio
from datetime import datetime
from typing import Any, AsyncGenerator
from pydantic import BaseModel, Field


class ExecutionEvent(BaseModel):
    event_type: str = Field(..., description="task_started, task_completed, claim_extracted, contradiction_detected, run_completed, error")
    run_id: str
    task_id: str | None = None
    agent_role: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def to_sse(self) -> dict[str, Any]:
        return {
            "event": self.event_type,
            "data": self.model_dump_json(),
        }


class EventBus:
    """Asynchronous publish-subscribe event bus for real-time investigation streaming."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[ExecutionEvent]]] = {}
        self._history: dict[str, list[ExecutionEvent]] = {}
        self._lock = asyncio.Lock()

    async def publish(self, event: ExecutionEvent) -> None:
        async with self._lock:
            if event.run_id not in self._history:
                self._history[event.run_id] = []
            self._history[event.run_id].append(event)

            queues = self._subscribers.get(event.run_id, [])
            for q in queues:
                await q.put(event)

    async def subscribe(self, run_id: str) -> AsyncGenerator[ExecutionEvent, None]:
        q: asyncio.Queue[ExecutionEvent] = asyncio.Queue()

        async with self._lock:
            # Replay historical events first
            if run_id in self._history:
                for past_event in self._history[run_id]:
                    await q.put(past_event)

            if run_id not in self._subscribers:
                self._subscribers[run_id] = []
            self._subscribers[run_id].append(q)

        try:
            while True:
                event = await q.get()
                yield event
                q.task_done()
                if event.event_type in ("run_completed", "run_failed", "run_cancelled"):
                    break
        finally:
            async with self._lock:
                if run_id in self._subscribers and q in self._subscribers[run_id]:
                    self._subscribers[run_id].remove(q)


_event_bus_instance: EventBus | None = None


def get_event_bus() -> EventBus:
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance
