import asyncio
from functools import wraps
from httpx import AsyncClient, ASGITransport
from app.main import create_app


def async_test(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


@async_test
async def test_incident_demo_seed_and_chat_flow():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Seed incident scenario
        seed_res = await client.post("/api/demo/seed?scenario=incident")
        assert seed_res.status_code == 200
        data = seed_res.json()
        assert data["status"] == "seeded"
        assert data["project_id"] == "proj-incident-investigation"

        # 2. Verify project & runs
        p_res = await client.get("/api/projects/proj-incident-investigation")
        assert p_res.status_code == 200
        assert "Production Incident" in p_res.json()["name"]

        runs_res = await client.get("/api/projects/proj-incident-investigation/runs")
        assert runs_res.status_code == 200
        runs = runs_res.json()
        assert len(runs) >= 2

        # 3. Verify chat turns
        chat_res = await client.get("/api/runs/run-incident-root-cause/chat")
        assert chat_res.status_code == 200
        turns = chat_res.json()
        assert len(turns) >= 4
        # Verify turns are chronologically ordered
        assert turns[0]["role"] == "user"
        assert "Why did our graph queries spike" in turns[0]["content"]
        assert turns[1]["role"] == "assistant"
        assert len(turns[1]["mentioned_claim_ids"]) >= 1

        # 4. Post follow-up chat turn
        post_turn_res = await client.post(
            "/api/runs/run-incident-root-cause/chat",
            json={"message": "Can we increase max_connections to 64 immediately?", "role": "user"},
        )
        assert post_turn_res.status_code == 201
        chat_resp = post_turn_res.json()
        assert chat_resp["user_turn"]["content"] == "Can we increase max_connections to 64 immediately?"
        assert chat_resp["assistant_turn"] is not None
        assert chat_resp["assistant_turn"]["role"] == "assistant"
        assert chat_resp["user_turn"]["id"] != chat_resp["assistant_turn"]["id"]

        # Verify turns count increased
        chat_res2 = await client.get("/api/runs/run-incident-root-cause/chat")
        assert len(chat_res2.json()) == len(turns) + 2

        # 5. Test Human Feedback on Procedural Rules
        rules_res = await client.get("/api/projects/proj-incident-investigation/memories?memory_type=procedural")
        assert rules_res.status_code == 200
        initial_rules = rules_res.json()
        assert len(initial_rules) >= 2

        # Send 'approve' feedback
        fb_approve = await client.post(
            "/api/runs/run-incident-root-cause/feedback",
            json={"action": "approve", "notes": "Approved root cause findings"},
        )
        assert fb_approve.status_code == 200
        fb_data = fb_approve.json()
        assert fb_data["status"] == "success"
        assert fb_data["updated_rules_count"] >= 1
