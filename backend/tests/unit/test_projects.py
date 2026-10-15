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
async def test_projects_crud_api():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"name": "Test Hackathon Project", "description": "Testing SwarmMind"}
        create_res = await client.post("/api/projects", json=payload)
        assert create_res.status_code == 201
        created = create_res.json()
        assert created["name"] == "Test Hackathon Project"
        proj_id = created["id"]

        list_res = await client.get("/api/projects")
        assert list_res.status_code == 200
        projects = list_res.json()
        assert any(p["id"] == proj_id for p in projects)

        get_res = await client.get(f"/api/projects/{proj_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == proj_id

        update_res = await client.patch(
            f"/api/projects/{proj_id}",
            json={"name": "Updated Hackathon Project"},
        )
        assert update_res.status_code == 200
        assert update_res.json()["name"] == "Updated Hackathon Project"

        del_res = await client.delete(f"/api/projects/{proj_id}")
        assert del_res.status_code == 204

        not_found = await client.get(f"/api/projects/{proj_id}")
        assert not_found.status_code == 404
