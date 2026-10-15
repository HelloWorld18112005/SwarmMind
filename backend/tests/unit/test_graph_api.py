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
async def test_graph_endpoints_and_runs():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create Project
        p_res = await client.post("/api/projects", json={"name": "Graph API Test"})
        assert p_res.status_code == 201
        proj_id = p_res.json()["id"]

        # 1. Test Runs API
        run_res = await client.post(
            f"/api/projects/{proj_id}/runs",
            json={"goal": "Evaluate graph multi-agent integration"},
        )
        assert run_res.status_code == 201
        run_id = run_res.json()["id"]

        # 2. Test Memories API
        mem_res = await client.post(
            f"/api/projects/{proj_id}/memories",
            json={"content": "Graph traversal operates in O(V+E) time", "memory_type": "fact"},
        )
        assert mem_res.status_code == 201
        mem_id = mem_res.json()["id"]

        # List memories
        list_mem = await client.get(f"/api/projects/{proj_id}/memories")
        assert list_mem.status_code == 200
        assert len(list_mem.json()) >= 1

        # 3. Test Graph retrieval
        graph_res = await client.get(f"/api/projects/{proj_id}/graph")
        assert graph_res.status_code == 200
        graph_data = graph_res.json()
        assert "nodes" in graph_data
        assert "edges" in graph_data
