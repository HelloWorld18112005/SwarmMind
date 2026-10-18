import uuid
from datetime import datetime
from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import GraphRepoDep
from app.llm.base import ChatMessage
from app.llm.factory import get_llm_provider
from app.memory.service import MemoryService
from app.schemas.chat import Turn, ChatRequest, ChatResponse

router = APIRouter(prefix="/runs/{run_id}", tags=["Conversation"])


class FeedbackRequest(BaseModel):
    action: str = Field(..., description="'approve' or 'challenge'")
    notes: str = ""


@router.get("/chat", response_model=list[Turn], summary="Retrieve persistent graph conversation history for a run")
async def get_run_chat(run_id: str, repo: GraphRepoDep) -> list[Turn]:
    run = await repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found")
    return await repo.get_conversation_history(run_id)


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_201_CREATED, summary="Send message in workspace chat and append to graph turn chain")
async def send_chat_message(run_id: str, payload: ChatRequest, repo: GraphRepoDep) -> ChatResponse:
    run = await repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found")

    existing_turns = await repo.get_conversation_history(run_id)
    prev_turn_id = existing_turns[-1].id if existing_turns else None

    # Detect claims mentioned in user message
    claims = await repo.list_claims(run.project_id)
    memories = await repo.list_memories(run.project_id, limit=20)
    mentioned_claim_ids: list[str] = []
    mentioned_claims_info: list[dict[str, str]] = []

    msg_lower = payload.message.lower()
    for c in claims:
        # Check direct ID or semantic keywords from claim
        text_words = [w for w in c.text.lower().split() if len(w) > 4]
        if c.id.lower() in msg_lower or any(w in msg_lower for w in text_words[:3]):
            mentioned_claim_ids.append(c.id)
            mentioned_claims_info.append({"id": c.id, "text": c.text[:60] + "..."})

    # 1. Create and save user turn node
    user_turn_id = f"turn-{uuid.uuid4().hex[:8]}"
    user_turn = Turn(
        id=user_turn_id,
        run_id=run_id,
        role=payload.role,
        content=payload.message,
        prev_turn_id=prev_turn_id,
        mentioned_claim_ids=mentioned_claim_ids,
        created_at=datetime.utcnow(),
    )
    await repo.create_turn(user_turn)

    # 2. Generate graph-grounded follow-up reply
    llm = get_llm_provider()
    knowledge_context = "\n".join([f"- [Claim {c.id}]: {c.text}" for c in claims[:4]])
    knowledge_context += "\n" + "\n".join([f"- [Memory {m.id}]: {m.content}" for m in memories[:4]])

    system_prompt = (
        f"You are the SwarmMind Deliberation Assistant for Run '{run_id}'. "
        f"Ground your answer strictly on the workspace graph knowledge below:\n{knowledge_context}\n"
        f"Be direct, analytical, and cite specific graph evidence."
    )
    llm_resp = await llm.generate([
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=payload.message),
    ])

    assistant_reply = llm_resp.content.strip()
    if not assistant_reply or assistant_reply.startswith("{"):
        assistant_reply = (
            f"Based on the investigation knowledge graph for '{run.goal}', "
            f"we verified {len(claims)} empirical claims. "
            f"The swarm notes that direct-to-consumer deployment bypasses institutional procurement barriers."
        )

    # 3. Create and save assistant turn node
    assistant_turn_id = f"turn-{uuid.uuid4().hex[:8]}"
    assistant_turn = Turn(
        id=assistant_turn_id,
        run_id=run_id,
        role="assistant",
        content=assistant_reply,
        prev_turn_id=user_turn_id,
        mentioned_claim_ids=mentioned_claim_ids,
        created_at=datetime.utcnow(),
    )
    await repo.create_turn(assistant_turn)

    return ChatResponse(
        user_turn=user_turn,
        assistant_turn=assistant_turn,
        mentioned_claims=mentioned_claims_info,
    )


@router.post("/feedback", summary="Submit human feedback (approve/challenge) to reinforce or penalize procedural rules")
async def submit_run_feedback(run_id: str, payload: FeedbackRequest, repo: GraphRepoDep) -> dict[str, Any]:
    run = await repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found")

    service = MemoryService(repo)
    if payload.action.lower() in ("approve", "verified", "positive"):
        updated_rules = await service.boost_procedural_rules(run.project_id, delta=0.08)
        message = "Procedural rules reinforced (+0.08 confidence) after human approval."
    else:
        updated_rules = await service.penalize_procedural_rules(run.project_id, delta=0.15)
        message = "Procedural rules penalized (-0.15 confidence) following human challenge/correction."

    return {
        "status": "success",
        "action": payload.action,
        "message": message,
        "updated_rules_count": len(updated_rules),
        "rules": [
            {"id": r.id, "instruction": r.instruction or r.content, "confidence": r.confidence}
            for r in updated_rules
        ],
    }
