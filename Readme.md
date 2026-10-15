Great choice. Let's turn SwarmMind into a complete hackathon project specification that you can give directly to Antigravity.

The key is that we're not building a basic multi-agent chatbot. We're building a collaborative AI system with shared graph memory, where agents contribute evidence, challenge one another, coordinate tasks, and update a common understanding of a problem.

We'll build the full application in phases, but the final goal is a complete product — frontend, backend, agent orchestration, shared memory, graph visualization, evaluation, and deployment preparation. We'll design it so FalkorDB Cloud can be connected after Antigravity finishes the initial implementation, without Docker.

# SwarmMind — complete project blueprint

ImpireX | AI Agents

Hackathon projectAgent Memory & CoordinationCloud database ready

Product vision: an AI team whose members collaborate through a shared, inspectable knowledge graph.

## 1. The idea

Today, many multi-agent applications work by passing text between agents. Each agent may have its own conversation history, and important findings can get lost, duplicated, or contradicted.

SwarmMind gives every agent access to a shared, persistent knowledge graph.

Imagine giving it this task:

> Research whether our fictional startup should launch an AI tutoring product. Assess the market, technical feasibility, risks, and launch plan. Cite evidence, identify disagreements, and produce a final recommendation.

SwarmMind creates a team of specialized agents:

- Coordinator: breaks the task into subtasks, assigns work, and manages dependencies.
- Researcher: gathers evidence from permitted sources or a controlled demo dataset.
- Analyst: connects findings, identifies patterns, and checks assumptions.
- Critic: challenges unsupported claims, contradictions, and missing evidence.
- Planner: turns verified findings into a prioritized action plan.
- Synthesizer: combines the work into a final report with evidence and citations.

All agents write to and read from the same graph. They can discover one another's findings, build on prior work, and update shared decisions.

The result is not just a chat transcript. It's an auditable record of what the system knows, where that knowledge came from, which agents contributed, what is disputed, and why the final recommendation was made.

## 2. Product requirements

The application must eventually support the following features. We should distinguish between a feature that merely appears in the UI and one that actually works end to end.

## Core product features

### 01

Multi-agent orchestration

Agents receive distinct roles, execute tasks, share findings, and coordinate through explicit task states.

### 02

Shared graph memory

Facts, evidence, tasks, decisions, agents, and dependencies are connected in one graph.

### 03

Persistent project workspaces

A user can return to an existing project and resume work without losing its knowledge.

### 04

Evidence and provenance

Important claims link to their sources, originating agent, timestamp, and verification status.

### 05

Conflict detection

Agents can flag contradictory claims, request verification, and record how conflicts were resolved.

### 06

Interactive graph explorer

Users can filter nodes, inspect relationships, follow evidence paths, and see which agent contributed a fact.

### 07

Live execution dashboard

Users can inspect agent status, task dependencies, findings, errors, and execution history.

### 08

Final reports and action plans

The system synthesizes findings into a structured answer with evidence, uncertainty, risks, and next steps.

### 09

Human oversight

Users can pause or cancel runs, retry failed tasks, correct memories, and approve consequential actions.

### 10

Evaluation and reliability

Tests verify graph persistence, agent coordination, evidence grounding, and behavior when tools or agents fail.

## 3. Architecture

## Frontend — React + TypeScript

Workspace · Agent dashboard · Chat · Graph explorer · Reports

HTTP API + Server-Sent Events (SSE)

## Backend — Python + FastAPI

Authentication · Projects · Runs · Memory API · Reports

Orchestration engine

Coordinator · agents · task queue · retries · limits

Agent runtime

LLM adapter · tools · prompts · structured outputs

## Graph repository layer

One interface for memory, relationships, traversal, and persistence

FalkorDB Cloud

Final persistent graph database

Local development adapter

Temporary graph implementation for early development

Target architecture. The local adapter is for development only; FalkorDB is the required production graph database.

### Architecture rules Antigravity must follow

1. The frontend must never connect directly to FalkorDB. All database access happens through the backend.
2. All graph operations must go through a repository interface, not be scattered throughout the application.
3. Agent code must not directly manipulate database connections. Agents call memory and task tools exposed by the backend.
4. LLM providers must be configurable through an adapter. Do not hardcode a particular provider into orchestration logic.
5. The application must have a clear local-development mode and a FalkorDB mode. Switching to FalkorDB must not require rewriting agents or the frontend.
6. Long-running agent tasks must not depend on a single browser request staying open. Store run state, emit events, and support status polling or reconnection.
7. External sources and LLM responses are untrusted data. They cannot override system instructions or execute arbitrary tools.
8. Store API keys and database credentials only in environment variables or an appropriate secret manager.

## 4. Technology stack

Use this stack unless there is a strong technical reason to change it.

| Layer | Technology | Purpose |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite | Main web application |
| Styling | Tailwind CSS and a consistent component library | Responsive, polished UI |
| Graph visualization | React Flow or Cytoscape.js | Interactive graph exploration |
| Backend | Python, FastAPI, Pydantic | REST API and validation |
| Agent orchestration | Custom Python orchestration service | Predictable task and agent lifecycle |
| Graph database | FalkorDB Cloud | Shared memory and relationship traversal |
| Graph client | Official `falkordb` Python package | Database connection and Cypher queries |
| LLM integration | Provider adapter | Model calls, structured output, retries |
| Streaming | Server-Sent Events (SSE) | Live updates to the UI |
| Testing | Pytest, HTTPX, Vitest | Backend and frontend verification |
| Packaging | Docker optional; not required for development | Deployment flexibility |

Important: Build the first version without Docker. Use a local adapter and synthetic data, then connect FalkorDB Cloud by setting environment variables and testing the real adapter.

The local adapter is a temporary convenience, not a substitute for FalkorDB in the final hackathon submission.

## 5. Graph data model

This is the most important technical part of the project. Antigravity must implement a real graph model, not just create a visualization.

### Node types

| Node | Important properties | Purpose |
| --- | --- | --- |
| `User` | `id`, `name` | Project owner |
| `Project` | `id`, `name`, `description`, `created_at` | Persistent workspace |
| `Run` | `id`, `status`, `goal`, `started_at`, `completed_at` | One multi-agent execution |
| `Agent` | `id`, `role`, `name` | Specialized team member |
| `Task` | `id`, `title`, `status`, `priority` | Work assigned to an agent |
| `Memory` | `id`, `content`, `memory_type`, `created_at` | Persistent shared knowledge |
| `Claim` | `id`, `text`, `confidence`, `status` | A statement that can be evaluated |
| `Source` | `id`, `title`, `uri`, `source_type` | Evidence source |
| `Decision` | `id`, `summary`, `status`, `created_at` | Team conclusion or choice |
| `Artifact` | `id`, `title`, `artifact_type` | Reports and generated deliverables |

### Relationship types

- `OWNS`: User → Project
- `HAS_RUN`: Project → Run
- `INCLUDES_AGENT`: Run → Agent
- `HAS_TASK`: Run → Task
- `ASSIGNED_TO`: Task → Agent
- `DEPENDS_ON`: Task → Task
- `PRODUCED`: Agent → Memory or Artifact
- `SUPPORTS`: Source or Memory → Claim
- `CONTRADICTS`: Claim → Claim
- `DERIVED_FROM`: Memory or Claim → Memory or Source
- `ABOUT`: Memory or Claim → Project, Task, or Decision
- `SHARES_WITH`: Agent → Memory
- `INFORMED_BY`: Decision → Claim or Memory
- `CREATED`: Run → Artifact

All nodes need stable IDs. The database must enforce uniqueness where appropriate, and every graph query must be scoped to the current user and project.

### Example graph

Researcher Agent

PRODUCED

Market finding

SUPPORTED BY

Source A

CHALLENGED BY

Critic finding

INFORMED BY

Final decision

Includes evidence and unresolved uncertainty

Illustrative relationships. The implementation should preserve provenance and unresolved disagreements instead of silently deleting conflicting information.

### Graph memory rules

Antigravity must implement the following behavior:

- Save new findings with their project, run, agent, timestamp, and provenance.
- Link repeated or related findings to existing entities rather than duplicating everything.
- Keep original evidence when a claim is corrected or challenged.
- Represent disagreements explicitly; don't overwrite one claim with another simply because it was generated later.
- Separate raw observations from interpretations and final decisions.
- Store confidence and verification status as metadata, not as proof of correctness.
- Use Cypher queries to retrieve related knowledge and multi-hop paths.
- Provide tests demonstrating that deleting or disconnecting graph relationships changes the results of graph-dependent features.

That final requirement is crucial: it helps demonstrate that FalkorDB genuinely drives the product.

## 6. How the multi-agent workflow works

The coordinator should manage a state machine rather than simply ask several agents to chat with each other.

mermaid
```

flowchart TD
    A[User submits goal] --> B[Create run and task graph]
    B --> C[Coordinator schedules tasks]
    C --> D[Research agent]
    C --> E[Analysis agent]
    D --> F[Save findings to shared graph]
    E --> F
    F --> G[Critic checks evidence and conflicts]
    G --> H{Enough reliable evidence?}
    H -- No --> I[Create follow-up tasks]
    I --> C
    H -- Yes --> J[Planner creates recommendations]
    J --> K[Synthesizer builds final report]
    K --> L[Save artifact and provenance]
    L --> M[Display report and graph to user]
```

### Agent responsibilities and boundaries

Coordinator

- Converts the user's goal into a structured task plan.
- Assigns tasks based on agent roles and task dependencies.
- Tracks pending, running, completed, failed, and cancelled tasks.
- Applies maximum agent-call, time, and retry budgets.
- Avoids scheduling a task whose prerequisites are incomplete.

Researcher

- Searches only configured, permitted data sources.
- Produces findings with source metadata.
- Distinguishes retrieved facts from assumptions.
- Cannot mark its own claims as independently verified.

Analyst

- Queries shared graph memory for related facts.
- Connects evidence across different sources or tasks.
- Identifies patterns and missing information.
- Records the path and facts supporting each inference.

Critic

- Checks claims against their sources.
- Identifies unsupported conclusions and contradictions.
- Requests additional evidence when necessary.
- Cannot silently delete findings or fabricate verification.

Planner

- Creates a prioritized plan with dependencies, risks, and expected outcomes.
- Explains which findings justify each recommendation.
- Marks assumptions and uncertain estimates explicitly.

Synthesizer

- Produces the final report.
- Uses verified or appropriately qualified evidence.
- Includes source references, unresolved conflicts, limitations, and recommended next steps.
- Must not invent citations or claim a task succeeded when it failed.

For the initial MVP, these can be separate role configurations using one model provider. We don't need six different AI models or six continuously running services.

## 7. Complete project directory structure

Give Antigravity this target structure. It may adjust small implementation details, but it must preserve the separation between agents, graph storage, orchestration, API routes, and UI.

text
```

swarmmind/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml             # Optional; never required locally
├── docs/
│   ├── ARCHITECTURE.md
│   ├── GRAPH_SCHEMA.md
│   ├── API.md
│   ├── AGENTS.md
│   ├── SECURITY.md
│   ├── TESTING.md
│   └── HACKATHON_SUBMISSION.md
│
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   │
│   │   ├── api/
│   │   │   ├── router.py
│   │   │   └── routes/
│   │   │       ├── health.py
│   │   │       ├── projects.py
│   │   │       ├── runs.py
│   │   │       ├── agents.py
│   │   │       ├── memories.py
│   │   │       ├── graph.py
│   │   │       ├── reports.py
│   │   │       └── events.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── project.py
│   │   │   ├── run.py
│   │   │   ├── task.py
│   │   │   ├── agent.py
│   │   │   ├── memory.py
│   │   │   ├── claim.py
│   │   │   └── report.py
│   │   │
│   │   ├── agents/
│   │   │   ├── base.py
│   │   │   ├── registry.py
│   │   │   ├── coordinator.py
│   │   │   ├── researcher.py
│   │   │   ├── analyst.py
│   │   │   ├── critic.py
│   │   │   ├── planner.py
│   │   │   ├── synthesizer.py
│   │   │   ├── prompts/
│   │   │   │   ├── coordinator.md
│   │   │   │   ├── researcher.md
│   │   │   │   ├── analyst.md
│   │   │   │   ├── critic.md
│   │   │   │   ├── planner.md
│   │   │   │   └── synthesizer.md
│   │   │   └── tools/
│   │   │       ├── memory_search.py
│   │   │       ├── evidence.py
│   │   │       └── task_tools.py
│   │   │
│   │   ├── orchestration/
│   │   │   ├── engine.py
│   │   │   ├── scheduler.py
│   │   │   ├── state_machine.py
│   │   │   ├── task_planner.py
│   │   │   ├── event_bus.py
│   │   │   ├── retry_policy.py
│   │   │   └── budgets.py
│   │   │
│   │   ├── graph/
│   │   │   ├── base.py
│   │   │   ├── factory.py
│   │   │   ├── schema.py
│   │   │   ├── queries.py
│   │   │   ├── mapper.py
│   │   │   ├── falkordb_adapter.py
│   │   │   ├── local_adapter.py
│   │   │   └── migrations/
│   │   │       └── 001_initial_schema.py
│   │   │
│   │   ├── memory/
│   │   │   ├── service.py
│   │   │   ├── extraction.py
│   │   │   ├── deduplication.py
│   │   │   ├── retrieval.py
│   │   │   ├── provenance.py
│   │   │   └── conflicts.py
│   │   │
│   │   ├── llm/
│   │   │   ├── base.py
│   │   │   ├── factory.py
│   │   │   └── providers/
│   │   │       └── configured_provider.py
│   │   │
│   │   ├── services/
│   │   │   ├── project_service.py
│   │   │   ├── run_service.py
│   │   │   ├── report_service.py
│   │   │   └── export_service.py
│   │   │
│   │   ├── security/
│   │   │   ├── auth.py
│   │   │   ├── permissions.py
│   │   │   └── redaction.py
│   │   │
│   │   └── demo/
│   │       ├── seed_data.py
│   │       ├── sample_tasks.py
│   │       └── sample_sources.json
│   │
│   └── tests/
│       ├── unit/
│       ├── integration/
│       ├── contract/
│       ├── e2e/
│       └── fixtures/
│
└── frontend/
    ├── package.json
    ├── index.html
    ├── vite.config.ts
    ├── tsconfig.json
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── routes/
        │   ├── Dashboard.tsx
        │   ├── Workspace.tsx
        │   ├── RunDetails.tsx
        │   ├── GraphExplorer.tsx
        │   ├── MemoryLibrary.tsx
        │   ├── ReportView.tsx
        │   └── Settings.tsx
        │
        ├── components/
        │   ├── layout/
        │   ├── workspace/
        │   ├── agents/
        │   ├── graph/
        │   ├── memory/
        │   ├── reports/
        │   └── ui/
        │
        ├── features/
        │   ├── projects/
        │   ├── runs/
        │   ├── agents/
        │   ├── memories/
        │   ├── graph/
        │   └── reports/
        │
        ├── hooks/
        ├── lib/
        │   ├── api.ts
        │   ├── events.ts
        │   └── formatters.ts
        ├── types/
        └── styles/
            └── globals.css
```

This is a target structure, not a requirement to create every empty file immediately. Antigravity should implement modules as they become necessary and keep the repository runnable after every phase.

## 8. Frontend design specification

The app should feel like a polished AI operations workspace, not a generic chat interface.

Pulse - AI Agent Management Dashboard Concept by Alex Rivera on Dribbble

A. Dashboard

Show active projects, recent runs, completed reports, failed tasks, and a prominent New investigation action.

My personal multi agent dashboard - mrum\_ - Friends of the Crustacean 🦞🤝

B. Investigation workspace

Display the goal, agent roster, task progress, live event feed, findings, and a conversational interface for follow-up questions.

GitHub - KnowledgeCanvas/knowledge: Knowledge is a tool for saving, searching, accessing, exploring and chatting with all of your favorite websites, documents and files.

C. Graph explorer

Display typed nodes and relationships, filters, search, selected-node details, provenance, and a path-inspection panel. Support loading, empty, and error states.

VibeMesh Labs - Agentic systems, trained in the real world

D. Final report

Include executive summary, findings, source citations, contradictions, confidence explanations, recommendations, risks, and next steps.

### UI behavior requirements

- Use a consistent design system with clear typography, spacing, responsive layouts, and accessible contrast.
- Use distinct, consistent colors for agents, memories, claims, tasks, and sources.
- Every graph node and relationship shown must correspond to actual backend data.
- Clicking an agent opens its current task and recent contributions.
- Clicking a claim opens its supporting and contradicting evidence.
- Live updates should show progress without requiring page refreshes.
- Include retry, cancel, and empty/error states where appropriate.
- Use a realistic seeded demo so the first launch is not an empty dashboard.
- Do not hardcode fake run progress, agent messages, graph nodes, or success indicators into the production interface.

## 9. Implementation phases

Build the project in the following order. Each phase has its own acceptance criteria, so Antigravity can verify the result before moving forward. The full feature set remains the end goal; the early phases are not the final product.

# P0

Foundation

## Project setup and contracts

Deliverable: runnable application skeleton

- Create the frontend and backend, environment configuration, linting, and test commands.
- Define API schemas, graph repository interfaces, error formats, and typed frontend API clients.
- Add a health endpoint and a visible backend connection status.
- Provide clear setup instructions.
  Acceptance: frontend and backend start using documented commands, and automated smoke tests pass.

# P1

Graph

## Graph storage and memory

Deliverable: real graph-backed persistence

- Implement the graph schema, repository interface, local adapter, and FalkorDB adapter.
- Add project creation, node and relationship operations, graph traversal, and provenance.
- Implement memory creation, retrieval, correction, deletion, and deduplication.
- Create synthetic seed data and migration/bootstrap scripts.
  Acceptance: memories persist in the selected backend and graph queries return real relationships.

# P2

Agents

## LLM adapter and agent tools

Deliverable: specialized agents with structured outputs

- Implement the configurable LLM adapter.
- Build agent base classes, prompt templates, typed outputs, and tool permissions.
- Give agents tools for memory search, evidence creation, task updates, and graph traversal.
- Validate all model-generated outputs before using them.
  Acceptance: each agent performs its assigned role and saves structured, attributable findings.

# P3

Swarm

## Orchestration and coordination

Deliverable: complete multi-agent execution

- Build the coordinator, dependency-aware scheduler, task state machine, retries, cancellation, and budgets.
- Implement research, analysis, critique, planning, and synthesis workflows.
- Let agents share and retrieve findings through the graph.
- Persist run status and emit execution events.
  Acceptance: a complete investigation can run, recover from a simulated agent failure, and produce a final artifact.

# P4

Interface

## Full frontend experience

Deliverable: working workspace and graph explorer

- Implement dashboard, projects, investigation workspace, agent activity, graph visualization, memory library, and report viewer.
- Connect all screens to real backend endpoints.
- Add streaming events, filtering, selection, loading states, and error recovery.
  Acceptance: users can create a project, launch a run, inspect live execution, and view actual graph data.

# P5

Intelligence

## Evidence, conflicts, and explainability

Deliverable: reliable graph-grounded answers

- Implement multi-hop retrieval, claim provenance, contradiction detection, evidence verification, and source-aware synthesis.
- Expose the paths supporting key recommendations.
- Include uncertainty, unsupported claims, and unresolved disputes in reports.
  Acceptance: a test scenario demonstrates that an agent finds a relationship another agent stored and uses it correctly in a subsequent decision.

# P6

Quality

## Security, evaluation, and persistence

Deliverable: trustworthy application

- Test cross-project isolation, invalid inputs, duplicate memories, contradictory evidence, and interrupted runs.
- Add request limits, timeouts, retries, safe logging, and secret redaction.
- Measure task completion, evidence coverage, unsupported claims, and execution cost.
  Acceptance: automated tests pass, no credentials are committed, and failure states are visible and recoverable.

# P7

Release

## Deployment and hackathon submission

Deliverable: complete demo-ready product

- Verify the FalkorDB Cloud connection, configure the production LLM, and run all migrations.
- Deploy the frontend and backend, or provide reproducible local setup instructions.
- Finalize README, graph model, Cypher examples, architecture notes, and AI-assistant disclosure.
- Record a complete demo video.
  Acceptance: a new user can follow the instructions, launch an investigation, inspect the graph, and retrieve the final report.

### What the final feature set must include

Do not consider SwarmMind finished until the following end-to-end flows work:

1. Create, rename, and delete projects.
2. Start, monitor, cancel, and retry investigations.
3. Assign tasks to agents and track dependencies.
4. Store shared knowledge in FalkorDB with provenance.
5. Search and traverse related memories across tasks and agents.
6. Detect, display, and resolve or preserve contradictory claims.
7. Inspect the graph and navigate between evidence, agents, tasks, and decisions.
8. Generate source-grounded reports with downloadable/exportable output.
9. Resume a workspace after refreshing or reopening the app.
10. Handle errors, timeouts, model failures, and empty results gracefully.
11. Switch from the local adapter to FalkorDB Cloud through configuration.
12. Run automated tests and provide documented installation and deployment instructions.

Do not replace a missing feature with a static mockup and call it complete.

## 10. FalkorDB Cloud integration — design it now, connect it later

You said you want Antigravity to build the application first and connect your cloud database afterward. That is a good workflow, provided we define the integration contract from the beginning.

### Environment configuration

Create `backend/.env.example` with these placeholders:

dotenv
```
APP_ENV=development
APP_SECRET_KEY=replace-with-a-random-secret
FRONTEND_ORIGIN=http://localhost:5173

GRAPH_BACKEND=local

FALKORDB_HOST=
FALKORDB_PORT=6379
FALKORDB_USERNAME=
FALKORDB_PASSWORD=
FALKORDB_SSL=true
FALKORDB_GRAPH=swarmmind

LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=

MAX_CONCURRENT_AGENTS=3
MAX_AGENT_STEPS=20
MAX_RUN_DURATION_SECONDS=600
```

The `.env.example` file is safe to commit because it contains no real credentials. Create your actual `backend/.env` separately and add it to `.gitignore`.

The values shown are configuration examples, not a claim that your particular cloud instance uses those settings.

### Graph backend interface

`backend/app/graph/base.py` should define the common operations the rest of the application needs. For example:

python
```
from typing import Any, Protocol

class GraphRepository(Protocol):
    async def initialize(self) -> None: ...

    async def close(self) -> None: ...

    async def create_project(
        self, project: dict[str, Any]
    ) -> dict[str, Any]: ...

    async def save_memory(
        self, memory: dict[str, Any]
    ) -> dict[str, Any]: ...

    async def search_memories(
        self,
        project_id: str,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]: ...

    async def traverse_graph(
        self,
        project_id: str,
        node_id: str,
        depth: int = 2,
    ) -> dict[str, Any]: ...

    async def save_claim(
        self, claim: dict[str, Any]
    ) -> dict[str, Any]: ...

    async def record_relationship(
        self, relationship: dict[str, Any]
    ) -> None: ...
```

This is an illustrative interface. Antigravity must implement the methods fully, including validation, access scoping, persistence, error handling, and tests. It should also define the remaining operations needed by projects, runs, tasks, sources, decisions, and artifacts.

The application should instantiate the correct repository through `graph/factory.py`:

- `GRAPH_BACKEND=local`: use the local development implementation.
- `GRAPH_BACKEND=falkordb`: use the official FalkorDB client and the configured cloud connection.

Critical: The local adapter must not silently become the production database. When the application is configured for FalkorDB and the connection fails, show a clear error instead of silently switching to local storage.

### What must be implemented in the FalkorDB adapter

- Create or verify required indexes and uniqueness constraints where supported.
- Implement graph schema initialization and migrations.
- Use parameterized Cypher queries instead of interpolating user input into query strings.
- Implement every repository method used by the application.
- Add connection health checks and graceful shutdown.
- Support TLS and credentials from environment variables.
- Handle connection failures and database timeouts.
- Scope every read and write to the authorized project.
- Include integration tests that can run against an explicitly configured test graph.
- Document which Cypher queries power memory retrieval, multi-hop traversal, task dependencies, and contradiction detection.

The cloud adapter must be written against the installed FalkorDB Python client version and tested against a real instance before claiming integration is complete. The local adapter is not evidence that the cloud integration works.

### How you will connect it later

1. Open your FalkorDB Cloud dashboard and create or select an instance.
2. Copy the actual host, port, username, password, and TLS requirements from its connection details.
3. Put those values in `backend/.env`.
4. Change `GRAPH_BACKEND=local` to `GRAPH_BACKEND=falkordb`.
5. Install the backend dependencies and run the graph migration/bootstrap command.
6. Start the backend and verify the health endpoint reports a successful FalkorDB connection.
7. Create a demo project and save a test memory. Restart the backend and verify that the memory still exists.
8. Run an integration test that retrieves a memory through a graph relationship and inspect the result in the graph explorer.

Do not paste your real password into Antigravity prompts, source files, GitHub issues, or this chat. Add secrets through your local environment configuration.

## 11. API specification

Antigravity should implement these endpoints with typed request and response models. The names can be refined, but the functionality must be preserved.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | API and database health |
| POST | `/api/projects` | Create a project |
| GET | `/api/projects` | List accessible projects |
| GET | `/api/projects/{id}` | Retrieve a project |
| PATCH | `/api/projects/{id}` | Update project details |
| DELETE | `/api/projects/{id}` | Delete a project and its associated data according to retention rules |
| POST | `/api/projects/{id}/runs` | Start an investigation |
| GET | `/api/runs/{id}` | Retrieve run state and summary |
| POST | `/api/runs/{id}/cancel` | Cancel an active run |
| POST | `/api/runs/{id}/retry` | Retry eligible failed work |
| GET | `/api/runs/{id}/events` | Stream execution events using SSE |
| GET | `/api/runs/{id}/tasks` | List tasks and dependencies |
| GET | `/api/runs/{id}/agents` | Inspect agent status and contributions |
| GET | `/api/projects/{id}/memories` | Search and list graph memories |
| PATCH | `/api/memories/{id}` | Correct a memory |
| DELETE | `/api/memories/{id}` | Delete a memory |
| GET | `/api/projects/{id}/graph` | Retrieve a filtered graph |
| GET | `/api/projects/{id}/graph/paths` | Retrieve relevant graph paths |
| GET | `/api/runs/{id}/claims` | Inspect claims, evidence, and disputes |
| GET | `/api/runs/{id}/report` | Retrieve the final report |
| GET | `/api/runs/{id}/export` | Export the report and evidence |

Every endpoint must validate inputs, handle errors consistently, and enforce access control. Do not expose passwords, provider API keys, or raw internal exception traces.

For a four-day hackathon, implement the essential endpoints first, then complete the remaining routes in the relevant phases. Do not build frontend screens that depend on nonexistent endpoints.

## 12. The signature demo

The product needs one scenario that makes the value of shared memory immediately obvious.

Use a fictional startup evaluating an AI tutoring product.

1. Start an investigation. The user asks SwarmMind to evaluate the product's market, technical feasibility, launch risks, and go-to-market strategy.
2. Watch agents collaborate. The Researcher records market evidence, the Analyst links technical requirements to costs, and the Critic challenges a claim with insufficient evidence.
3. Show the shared memory. A finding created by one agent appears in the graph and becomes available to another agent through a graph query.
4. Introduce a conflict. Two findings disagree about a launch assumption. SwarmMind preserves both, identifies their sources, and requests verification instead of hiding the conflict.
5. Generate the final recommendation. The Planner uses the connected evidence to prioritize actions. The Synthesizer creates a report with citations, uncertainty, and a visible explanation of the decision.
6. Prove persistence. Refresh the browser or restart the backend and show that the project, findings, and report can be retrieved from FalkorDB Cloud.

Use public or synthetic data, clearly label simulated findings, and never fabricate real-world research citations. If external research is unavailable, the demo should still work using a curated synthetic dataset.

## 13. Testing requirements

Antigravity must write and run tests, not simply generate code and report success.

- Unit tests: task state transitions, memory extraction, deduplication, contradiction handling, budget enforcement.
- Repository tests: create, read, update, delete, graph traversal, relationship creation, and project scoping.
- Integration tests: FalkorDB connection, graph initialization, query execution, persistence across restart.
- Agent tests: correct role assignment, structured output validation, evidence attribution, retry behavior.
- Orchestration tests: dependency ordering, parallel tasks, cancellation, partial failures, and completion.
- API tests: invalid inputs, authorization, missing resources, and consistent error responses.
- Frontend tests: workspace creation, run monitoring, graph selection, filtering, report rendering, and failed-request handling.
- End-to-end test: launch an investigation, persist findings, retrieve connected evidence, and display a final report.

Include at least one test that demonstrates a meaningful multi-hop relationship. For example, a claim connects to a memory, which connects to a source, and the report can retrieve that source through the graph.

## 14. How to use Antigravity

Don't give Antigravity a huge vague request such as "build the whole app perfectly." Give it a durable specification, ask it to create a task checklist, and have it implement the phases in order.

The master prompt below tells it what the complete product must become, including the directory structure, database integration, and acceptance criteria.

Writing

# MASTER BUILD SPECIFICATION — SWARMMIND

You are the lead full-stack engineer responsible for building SwarmMind, a complete, polished, graph-powered multi-agent AI collaboration platform for the FalkorDB Graph Hacks hackathon.

## Mission

Build a functioning application where specialized AI agents collaborate on complex tasks through shared, persistent graph memory. Agents must create and retrieve knowledge, discover relationships, share evidence, detect contradictions, coordinate dependent tasks, and produce source-grounded reports.

This is not a generic chatbot, a static dashboard, or a graph visualization demo. The graph database must be essential to the application's core functionality.

## Mandatory technology

- Frontend: React, TypeScript, Vite.
- Styling: Tailwind CSS and reusable accessible components.
- Backend: Python, FastAPI, Pydantic.
- Graph database: FalkorDB, with FalkorDB Cloud as the final target.
- Graph client: Official FalkorDB Python client.
- Graph visualization: React Flow or Cytoscape.js.
- Streaming: Server-Sent Events.
- Testing: Pytest, HTTPX, Vitest.
- LLM: Configurable provider adapter; do not hardcode provider credentials.
- Local development: Must work without Docker.

## Development strategy

I will connect my FalkorDB Cloud account after the initial implementation. Therefore:

1. Build a local development graph adapter first.
2. Define a complete graph repository interface from the beginning.
3. Implement the FalkorDB adapter and configuration path in the initial architecture, even if live credentials are not yet available.
4. Use synthetic seed data for local development.
5. Make it possible to switch to FalkorDB Cloud using environment variables without rewriting business logic.
6. Never silently fall back to local storage when FalkorDB is configured but unavailable.
7. Clearly distinguish implemented, tested, simulated, and unconfigured functionality.
8. Do not claim a cloud integration is verified until it has been tested against a real FalkorDB instance.

## Product features

Implement the complete feature set:

- Project creation, listing, editing, deletion, and persistent workspaces.
- Investigation creation, execution, progress monitoring, cancellation, retry, and execution history.
- Specialized Coordinator, Researcher, Analyst, Critic, Planner, and Synthesizer agents.
- Dependency-aware task scheduling and bounded parallel execution.
- Shared graph memory with provenance, timestamps, deduplication, and correction.
- Claims, sources, evidence, decisions, artifacts, and agent contribution tracking.
- Explicit contradiction detection and preservation of unresolved disputes.
- Graph traversal and multi-hop evidence retrieval.
- Interactive graph explorer with filters, node selection, relationship inspection, and path explanations.
- Live agent activity and task status using SSE.
- Source-grounded reports with recommendations, uncertainty, citations, and unresolved questions.
- Exportable reports.
- Error handling, retry policies, execution limits, and user cancellation.
- Persistent storage, configuration validation, security controls, and automated tests.
- A complete README, architecture documentation, graph schema, Cypher query examples, setup instructions, and hackathon submission checklist.

## Required graph model

Use nodes including User, Project, Run, Agent, Task, Memory, Claim, Source, Decision, and Artifact.

Implement meaningful relationships including OWNS, HAS_RUN, INCLUDES_AGENT, HAS_TASK, ASSIGNED_TO, DEPENDS_ON, PRODUCED, SUPPORTS, CONTRADICTS, DERIVED_FROM, ABOUT, SHARES_WITH, INFORMED_BY, and CREATED.

Use stable IDs, project scoping, schema initialization, and appropriate uniqueness constraints or indexes supported by FalkorDB.

Implement graph queries that retrieve connected memories, trace evidence, traverse task dependencies, find relevant claims, and identify contradictions. Do not substitute ordinary text search for all graph operations.

## Architecture requirements

Separate the code into:

- API routes and schemas.
- Agent roles and tools.
- Orchestration engine, scheduler, task state machine, retry policies, and budgets.
- Graph repository interface, local adapter, FalkorDB adapter, migrations, and queries.
- Memory extraction, retrieval, provenance, deduplication, and conflict services.
- LLM provider abstraction.
- Project, run, and report services.
- Frontend pages, components, API client, event handling, and graph visualization.
- Automated tests and documentation.

The frontend must never connect directly to FalkorDB. Agents must use backend tools and services instead of directly manipulating database connections. Keep provider calls and database access out of UI components.

## Directory structure

Create the following structure, adding files when they are needed:

swarmmind/ README.md .env.example .gitignore docs/ ARCHITECTURE.md GRAPH_SCHEMA.md API.md AGENTS.md SECURITY.md TESTING.md HACKATHON_SUBMISSION.md backend/ pyproject.toml requirements.txt app/ main.py config.py dependencies.py api/ router.py routes/ schemas/ agents/ base.py registry.py coordinator.py researcher.py analyst.py critic.py planner.py synthesizer.py prompts/ tools/ orchestration/ engine.py scheduler.py state_machine.py task_planner.py event_bus.py retry_policy.py budgets.py graph/ base.py factory.py schema.py queries.py mapper.py falkordb_adapter.py local_adapter.py migrations/ memory/ service.py extraction.py deduplication.py retrieval.py provenance.py conflicts.py llm/ base.py factory