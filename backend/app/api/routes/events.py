from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from app.orchestration.event_bus import get_event_bus

router = APIRouter(prefix="/runs/{run_id}/events", tags=["Live Streaming Events"])


@router.get("", summary="Stream live agent execution events via SSE")
async def stream_run_events(run_id: str) -> EventSourceResponse:
    """Stream real-time multi-agent execution events to UI over Server-Sent Events."""
    bus = get_event_bus()

    async def event_generator():
        async for event in bus.subscribe(run_id):
            yield event.to_sse()

    return EventSourceResponse(event_generator())
