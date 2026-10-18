# SwarmMind REST & FastMCP API Reference

SwarmMind provides a REST API, Server-Sent Events (SSE) streaming, and a FastMCP tool server.

---

## 🔌 Core Endpoints

### 1. System Health & Telemetry
- **`GET /api/health`**
  - Returns backend status, active graph engine (`local` or `falkordb`), and live node/edge counts via FalkorDB `GRAPH.INFO`.
  - Returns `503 Service Unavailable` if the configured FalkorDB instance cannot be reached.

### 2. Projects & Tenants
- **`GET /api/projects`** — List all projects/tenants.
- **`POST /api/projects`** — Create a new project (allocating isolated tenant graph `swarmmind_{clean_id}`).
- **`GET /api/projects/{id}`** — Retrieve project metadata and run summaries.
- **`POST /api/projects/seed?scenario={all|venture_audit|incident}`** — Seed full hackathon demo datasets.

### 3. Execution Runs & Task DAG
- **`POST /api/projects/{id}/runs`** — Trigger an autonomous multi-agent run.
- **`GET /api/runs/{id}`** — Retrieve run status, task counts, and conflict counters.
- **`GET /api/runs/{id}/tasks`** — Retrieve DAG tasks and dependency state.
- **`GET /api/runs/{id}/events`** — SSE stream emitting real-time agent execution events and log updates.

### 4. Graph Explorer & Explainability
- **`GET /api/projects/{id}/graph`** — Retrieve the full project graph for React Flow visualization.
- **`GET /api/projects/{id}/graph/disputes`** — Retrieve all conflicting claims with opposing sources.
- **`GET /api/projects/{id}/graph/authority`** — Native FalkorDB PageRank ranking of claims.
- **`GET /api/runs/{run_id}/explain`** — Calculate multi-hop shortest-path provenance from a decision/claim back to primary sources (`algo.SPpaths`).

### 5. Cognitive Memory Subsystem
- **`GET /api/projects/{id}/memories`** — List active memories (filtering out superseded/invalid facts).
- **`POST /api/projects/{id}/memories`** — Ingest new semantic or procedural memory.
- **`POST /api/projects/{id}/memories/{old_id}/supersede`** — Invalidate old memory and establish `[:SUPERSEDES]` link.

### 6. Conversational Turns
- **`GET /api/runs/{run_id}/turns`** — Traverse graph-native conversation chain: `(Run)-[:HAS_TURN]->(Turn)-[:NEXT_TURN*]->(Turn)` with mentioned graph entity IDs.
- **`POST /api/runs/{run_id}/turns`** — Append user or assistant turn linked to specific claims.

---

## 🛠️ FastMCP Tool Server

Mounted at `/mcp` (or standalone in `app.mcp_server`), exposing tools for external LLM orchestrators (Claude Desktop, Cursor, etc.):
- `search_graph_memories(project_id, query, limit)`
- `rank_evidence_authority(project_id, limit)`
- `trace_shortest_path(project_id, claim_a_id, claim_b_id)`
- `get_disputes_with_evidence(project_id)`
- `record_claim_evidence(project_id, text, confidence, agent_role)`
