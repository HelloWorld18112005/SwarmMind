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
async def test_seed_demo_endpoint():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Trigger seed
        seed_res = await client.post("/api/demo/seed")
        assert seed_res.status_code == 200
        data = seed_res.json()
        assert data["status"] == "seeded"
        proj_id = data["project_id"]
        assert proj_id == "proj-apexai-audit"

        # Verify project exists
        p_res = await client.get(f"/api/projects/{proj_id}")
        assert p_res.status_code == 200
        assert "ApexAI" in p_res.json()["name"]

        # Verify contradictions endpoint reports the founder IP/infrastructure contradictions
        conflicts_res = await client.get(f"/api/projects/{proj_id}/graph/conflicts")
        assert conflicts_res.status_code == 200
        conflicts = conflicts_res.json()
        assert len(conflicts) >= 1
        assert any("claim-founder-prop" in c["claim_a_id"] or "claim-founder-prop" in c["claim_b_id"] for c in conflicts)
