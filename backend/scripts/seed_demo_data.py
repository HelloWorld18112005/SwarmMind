#!/usr/bin/env python3
"""
Seed Demo Dataset Utility for SwarmMind.

Seeds the Signature Demo ("AI Tutoring Product Feasibility & Launch Strategy")
into the active graph repository (either local in-memory or FalkorDB Cloud).
"""

import asyncio
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.graph.factory import get_graph_repository
from app.demo.seed_data import seed_demo_project

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


async def main():
    print("=" * 60)
    print("       SWARMMIND - SEED SIGNATURE DEMO DATASET")
    print("=" * 60)
    print("Initializing active Graph Repository...")

    repo = await get_graph_repository()
    print(f"Active Adapter: {repo.__class__.__name__}")

    print("Seeding AI Tutoring Startup Evaluation dataset...")
    result = await seed_demo_project(repo)

    print("\n✓ Seed completed successfully!")
    print(f"  • Project ID: {result['project_id']}")
    print(f"  • Run ID:     {result['run_id']}")
    print(f"  • Nodes:      6 Agents, 6 Tasks, 5 Sources, 4 Claims, 5 Memories")
    print(f"  • Relations:  CONTRADICTS ($5.2B vs $800M TAM dispute preserved),")
    print(f"                SUPPORTS, ASSIGNED_TO, DEPENDS_ON, PRODUCED, ABOUT")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
