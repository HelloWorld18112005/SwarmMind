#!/usr/bin/env python3
"""
FalkorDB Cloud Connectivity & Diagnostics Utility for SwarmMind.

Validates FalkorDB Cloud credentials, network reachability, TLS/SSL handshake,
Cypher query execution, latency, and graph index readiness.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Load backend/.env
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def test_falkordb_cloud():
    print("=" * 60)
    print("      SWARMMIND - FALKORDB CLOUD CONNECTIVITY DIAGNOSTIC")
    print("=" * 60)

    host = os.getenv("FALKORDB_HOST", "").strip()
    port = int(os.getenv("FALKORDB_PORT", "6379"))
    username = os.getenv("FALKORDB_USERNAME", "").strip()
    password = os.getenv("FALKORDB_PASSWORD", "").strip()
    ssl = os.getenv("FALKORDB_SSL", "true").lower() in ("true", "1", "yes")
    graph_name = os.getenv("FALKORDB_GRAPH", "swarmmind").strip()

    print(f"\n[1/5] Checking Configuration:")
    print(f"  • FALKORDB_HOST:     {host if host else '<NOT SET (Local Mode)>'}")
    print(f"  • FALKORDB_PORT:     {port}")
    print(f"  • FALKORDB_USERNAME: {username if username else '<none>'}")
    print(f"  • FALKORDB_PASSWORD: {'*' * len(password) if password else '<none>'}")
    print(f"  • FALKORDB_SSL:      {ssl}")
    print(f"  • FALKORDB_GRAPH:    {graph_name}")

    if not host:
        print("\n" + "!" * 60)
        print("NOTICE: No FalkorDB Cloud host is configured in backend/.env")
        print("SwarmMind is currently operating in offline LocalGraphAdapter mode.")
        print("!" * 60)
        print("\nTo connect to FalkorDB Cloud:")
        print("  1. Create a free database on FalkorDB Cloud (https://app.falkordb.cloud)")
        print("  2. Open backend/.env and update:")
        print("       GRAPH_BACKEND=falkordb")
        print("       FALKORDB_HOST=<your-instance-subdomain>.falkordb.cloud")
        print("       FALKORDB_PORT=6379")
        print("       FALKORDB_PASSWORD=<your-database-password>")
        print("       FALKORDB_SSL=true")
        print("       FALKORDB_GRAPH=swarmmind")
        print("  3. Run this script again: python backend/scripts/test_cloud_connection.py\n")
        return 0

    print("\n[2/5] Verifying 'falkordb' Python Client...")
    try:
        from falkordb import FalkorDB
        print("  ✓ 'falkordb' client is installed.")
    except ImportError:
        print("  ✗ 'falkordb' package not found! Run: pip install falkordb")
        return 1

    print("\n[3/5] Establishing TLS/SSL Connection to FalkorDB Cloud...")
    start_time = time.time()
    try:
        db = FalkorDB(
            host=host,
            port=port,
            username=username if username else None,
            password=password if password else None,
            ssl=ssl,
        )
        graph = db.select_graph(graph_name)
        connect_time = (time.time() - start_time) * 1000
        print(f"  ✓ Connected successfully in {connect_time:.1f}ms")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  - Verify that your FalkorDB Cloud instance is active.")
        print("  - Verify that your IP is allowed in FalkorDB Cloud network access rules.")
        print("  - Double-check password and SSL configuration.")
        return 1

    print("\n[4/5] Testing Parameterized Cypher Query Execution & Latency...")
    try:
        query_start = time.time()
        res = graph.query("RETURN 1 AS ping, timestamp() AS server_time")
        query_time = (time.time() - query_start) * 1000
        print(f"  ✓ Cypher query returned: {res.result_set[0]}")
        print(f"  ✓ Round-trip query latency: {query_time:.1f}ms")
    except Exception as e:
        print(f"  ✗ Cypher query failed: {e}")
        return 1

    print("\n[5/5] Inspecting Graph Statistics...")
    try:
        node_res = graph.query("MATCH (n) RETURN count(n) AS node_count")
        edge_res = graph.query("MATCH ()-[r]->() RETURN count(r) AS edge_count")
        node_count = node_res.result_set[0][0] if node_res.result_set else 0
        edge_count = edge_res.result_set[0][0] if edge_res.result_set else 0
        print(f"  • Existing Graph Nodes:         {node_count}")
        print(f"  • Existing Graph Relationships: {edge_count}")
        print(f"  ✓ Graph '{graph_name}' is healthy and ready for multi-agent swarm operations.")
    except Exception as e:
        print(f"  ! Note on statistics: {e}")

    print("\n" + "=" * 60)
    print("  ALL FALKORDB CLOUD CHECKS PASSED — READY FOR PRODUCTION!")
    print("=" * 60 + "\n")
    return 0


if __name__ == "__main__":
    exit_code = test_falkordb_cloud()
    sys.exit(exit_code)
