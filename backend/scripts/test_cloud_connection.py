"""
test_cloud_connection.py
------------------------
Verifies that the FalkorDB instance (local Docker or cloud) is reachable
and that the SwarmMind graph schema can be initialized.

Usage:
    python backend/scripts/test_cloud_connection.py

Reads credentials from backend/.env (via pydantic-settings).
"""

import asyncio
import sys
from pathlib import Path

# Allow running from the repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.graph.factory import create_graph_repository


async def main() -> None:
    settings = get_settings()
    print("=" * 60)
    print("  SwarmMind — FalkorDB Connection Diagnostic")
    print("=" * 60)
    print(f"  Backend:   {settings.graph_backend}")
    print(f"  Host:      {settings.falkordb_host or '(none)'}")
    print(f"  Port:      {settings.falkordb_port}")
    print(f"  SSL:       {settings.falkordb_ssl}")
    print(f"  Graph:     {settings.falkordb_graph}")
    print("-" * 60)

    if settings.graph_backend != "falkordb":
        print(
            "⚠  GRAPH_BACKEND is set to 'local'.\n"
            "   Set GRAPH_BACKEND=falkordb in backend/.env to test a real instance."
        )
        return

    repo = create_graph_repository(settings)

    print("🔌  Connecting …")
    try:
        await repo.initialize()
    except Exception as e:
        print(f"❌  Connection FAILED: {e}")
        print()
        print("  If using local Docker, ensure the container is running:")
        print("    docker run --rm -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest")
        sys.exit(1)

    health = await repo.check_health()
    print(f"✅  Connected!  Status: {health}")

    # Basic round-trip test
    print()
    print("🔁  Running basic CRUD round-trip …")

    from app.schemas.project import Project
    from datetime import datetime

    test_proj = Project(
        id="test-conn-probe",
        name="Connection Probe",
        description="Temporary project created by test_cloud_connection.py",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await repo.create_project(test_proj)
    fetched = await repo.get_project("test-conn-probe")
    assert fetched is not None, "Project not found after creation"
    assert fetched.name == "Connection Probe"
    await repo.delete_project("test-conn-probe")
    gone = await repo.get_project("test-conn-probe")
    assert gone is None, "Project still exists after deletion"

    print("✅  Create → Read → Delete round-trip: PASS")

    # Graph traversal test
    print("🕸️   Running basic Cypher traversal …")
    from app.schemas.claim import Claim, Source
    from app.schemas.project import Project as Proj

    ping_proj = Project(
        id="test-traversal-ping",
        name="Traversal Ping",
        description="Temporary traversal test project",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await repo.create_project(ping_proj)

    src = Source(id="test-src-ping", title="Test Source", uri="http://test.internal", source_type="test")
    await repo.save_source(src)

    claim = Claim(
        id="test-claim-ping",
        project_id="test-traversal-ping",
        text="This is a test claim for graph traversal.",
        confidence=0.99,
        status="proposed",
        created_at=datetime.utcnow(),
    )
    await repo.save_claim(claim)
    await repo.record_relationship("test-src-ping", "test-claim-ping", "SUPPORTS")

    graph_data = await repo.get_project_graph("test-traversal-ping", limit=20)
    assert len(graph_data.nodes) > 0, "No nodes returned from graph query"
    print(f"✅  Traversal returned {len(graph_data.nodes)} node(s) and {len(graph_data.edges)} edge(s): PASS")

    # Cleanup
    await repo.delete_project("test-traversal-ping")

    await repo.close()
    print()
    print("=" * 60)
    print("  ALL CHECKS PASSED — FalkorDB is ready for SwarmMind 🎉")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
