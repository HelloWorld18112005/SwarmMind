# SwarmMind REST & Streaming API Documentation

SwarmMind provides an auditable, graph-grounded HTTP REST API paired with Server-Sent Events (SSE) for real-time agent telemetry.

Base URL: `http://127.0.0.1:8000`

---

## 1. System Health & Infrastructure

### `GET /api/health`
Inspects backend server status, active graph storage adapter, and database connectivity.

**Response `200 OK`:**
```json
{
  "status": "healthy",
  "backend": "local",
  "app_env": "development",
  "active_provider": "mock"
}
```
*(When connected to FalkorDB Cloud, `"backend": "falkordb"`, `"host": "...", "ping": 1`)*

---

## 2. Projects & Workspaces API

### `POST /api/projects`
Creates a persistent collaborative project workspace.

**Request Body:**
```json
{
  "name": "AI Tutoring Product Feasibility",
  "description": "Evaluation of market size, inference cost, and pedagogical risks."
}
```

**Response `200 OK`:**
```json
{
  "id": "proj-ai-tutoring",
  "name": "AI Tutoring Product Feasibility",
  "description": "Evaluation of market size, inference cost, and pedagogical risks.",
  "created_at": "2026-10-15T12:00:00Z",
  "updated_at": "2026-10-15T12:00:00Z"
}
```

### `GET /api/projects`
Lists all active projects scoped to the user workspace.

### `GET /api/projects/{id}`
Retrieves a project by ID.

### `DELETE /api/projects/{id}`
Deletes a project and its associated execution artifacts according to retention rules.

---

## 3. Swarm Orchestration & Runs API

### `POST /api/projects/{project_id}/runs`
Launches a multi-agent investigation under the specified project.

**Request Body:**
```json
{
  "goal": "Evaluate whether our startup should launch an AI tutoring product. Assess market TAM, inference costs, pedagogical efficacy, and identify disagreements."
}
```

**Response `200 OK`:**
```json
{
  "id": "run-4f81-a9c1",
  "project_id": "proj-ai-tutoring",
  "goal": "...",
  "status": "pending",
  "started_at": "2026-10-15T12:00:00Z",
  "task_count": 6,
  "completed_task_count": 0
}
```

### `GET /api/runs/{run_id}`
Returns the current run state, completion counts, and summary.

### `POST /api/runs/{run_id}/cancel`
Signals the orchestration engine to gracefully cancel running agent tasks.

### `POST /api/runs/{run_id}/retry`
Retries any failed tasks in the investigation DAG.

### `GET /api/runs/{run_id}/events` *(SSE Streaming)*
Streams live Server-Sent Events to connected clients without browser polling.
- Event types: `run_started`, `task_scheduled`, `task_started`, `task_completed`, `memory_saved`, `conflict_detected`, `run_completed`.

---

## 4. Shared Graph Memory & Claim API

### `GET /api/projects/{project_id}/memories`
Searches and filters shared graph memories across all agents.
- Query Parameters: `query` (optional string search), `limit` (default: 50).

### `POST /api/projects/{project_id}/memories`
Manually contributes a memory or observation to the graph. Secrets are automatically redacted before storage.

### `PATCH /api/memories/{memory_id}`
Updates or corrects an existing memory entry.

### `DELETE /api/memories/{memory_id}`
Removes a memory from the graph while maintaining relationship auditability.

### `GET /api/runs/{run_id}/claims`
Retrieves claims generated during the run, linked evidence sources, and contradiction statuses.

---

## 5. Graph Intelligence & Explainability API

### `GET /api/projects/{project_id}/graph`
Retrieves the complete or filtered knowledge graph (Nodes and Edges) for interactive visualization.
- Node types: `Project`, `Run`, `Agent`, `Task`, `Memory`, `Claim`, `Source`.
- Edge types: `OWNS`, `HAS_RUN`, `INCLUDES_AGENT`, `HAS_TASK`, `ASSIGNED_TO`, `DEPENDS_ON`, `PRODUCED`, `SUPPORTS`, `CONTRADICTS`, `ABOUT`.

### `GET /api/runs/{run_id}/explain`
Generates a multi-hop reasoning explanation for a given recommendation or finding.
- Query Parameter: `recommendation_title` (optional).
- Response includes:
  - Narrative justification.
  - Step-by-step reasoning pipeline (`Sources -> Researcher -> Analyst -> Critic -> Planner`).
  - Cited primary sources.
  - Preserved contradictions.
  - Multi-hop subgraph (`nodes`, `edges`).

### `GET /api/projects/{project_id}/graph/shortest-path`
Calculates the shortest graph traversal path between two nodes via Cypher / BFS.
- Query Parameters: `start_id`, `end_id`.

### `GET /api/projects/{project_id}/graph/conflicts`
Retrieves contradictory claim pairs with both sides' supporting sources and dispute notes.

---

## 6. Reports, Export & Governance API

### `GET /api/runs/{run_id}/report`
Retrieves the structured synthesized report:
- Executive Summary
- Key Findings
- Strategic Recommendations
- Preserved Contradictions & Disputes
- Limitations & Risks
- Evidence Sources

### `GET /api/runs/{run_id}/export`
Returns the full audit report as a downloadable GitHub-flavored Markdown document with citation tables and dispute logs.

### `GET /api/runs/{run_id}/budget`
Reports live execution financial accounting:
- `step_count` & `max_steps`
- `prompt_tokens` & `completion_tokens`
- `cost_usd` (computed at $0.50/M input, $1.50/M output)
- `remaining_budget_usd`
- `is_exceeded` flag
