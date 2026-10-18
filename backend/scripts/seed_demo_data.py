"""
seed_demo_data.py
-----------------
Seeds the SwarmMind Signature Demo project into the configured graph repository.

Scenario: AI Tutoring Startup Feasibility Evaluation.
Contains: Project, Run, 6 Agents, 6 Tasks (with dependencies), 5 Sources,
          4 Claims, 1 explicit CONTRADICTS edge, and 3 shared Memories.

Usage:
    python backend/scripts/seed_demo_data.py

Reads credentials from backend/.env (via pydantic-settings).
To seed local Docker:
    GRAPH_BACKEND=falkordb FALKORDB_HOST=localhost FALKORDB_SSL=false python backend/scripts/seed_demo_data.py
"""

import asyncio
import sys
from pathlib import Path

# Allow running from the repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.graph.factory import create_graph_repository
from app.demo.seed_data import seed_demo_project


async def main() -> None:
    settings = get_settings()
    print("=" * 60)
    print("  SwarmMind — Demo Seed Script")
    print("=" * 60)
    print(f"  Backend:   {settings.graph_backend}")
    print(f"  Host:      {settings.falkordb_host or 'in-memory (local)'}")
    print(f"  Port:      {settings.falkordb_port}")
    print(f"  Graph:     {settings.falkordb_graph}")
    print("-" * 60)

    repo = create_graph_repository(settings)

    print("🔌  Connecting to graph repository …")
    try:
        await repo.initialize()
    except Exception as e:
        print(f"❌  Failed to connect: {e}")
        if settings.graph_backend == "falkordb":
            print()
            print("  For local Docker, ensure FalkorDB is running:")
            print("    docker run --rm -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest")
            print()
            print("  Then set in backend/.env:")
            print("    GRAPH_BACKEND=falkordb")
            print("    FALKORDB_HOST=localhost")
            print("    FALKORDB_SSL=false")
        sys.exit(1)

    health = await repo.check_health()
    print(f"✅  Connected: {health.get('status', 'ok')} (backend={health.get('backend')})")
    print()

    # Check if demo project already exists
    existing = await repo.get_project("proj-apexai-audit")
    if existing:
        print("⚠️   Demo project 'proj-apexai-audit' already exists in the graph.")
        answer = input("   Overwrite / re-seed? [y/N]: ").strip().lower()
        if answer != "y":
            print("   Aborted. No changes made.")
            await repo.close()
            return
        # Clean up existing project before re-seeding
        await repo.delete_project("proj-apexai-audit")
        print("   Deleted existing project. Re-seeding …")
    else:
        print("📦  Seeding demo data …")

    result = await seed_demo_project(repo)

    print()
    print("=" * 60)
    print("  SEED COMPLETE 🎉")
    print("=" * 60)
    print(f"  Project ID:      {result['project_id']}")
    print(f"  Run ID:          {result['run_id']}")
    print(f"  Tasks:           {result['tasks_count']}")
    print(f"  Claims:          {result['claims_count']}")
    print(f"  Contradictions:  {result['contradictions_count']}")
    print(f"  Memories:        {result['memories_count']}")
    print("=" * 60)
    print()
    print("  Next steps:")
    if settings.graph_backend == "falkordb":
        print("  • Open FalkorDB Browser at http://localhost:3000")
        print("    to explore the graph visually.")
    print("  • Start the backend:  uvicorn app.main:app --reload")
    print("  • Start the frontend: cd frontend && npm run dev")
    print("  • Visit http://localhost:5173 → the demo project will be pre-loaded.")

    await repo.close()


if __name__ == "__main__":
    asyncio.run(main())
