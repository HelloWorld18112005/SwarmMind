# SwarmMind Architecture

## System Overview

SwarmMind is a graph-grounded multi-agent collaboration platform designed for complex research, strategy, and analytical evaluations. Agents communicate through a shared persistent knowledge graph (FalkorDB), rather than ephemeral chat streams.

```
+-------------------------------------------------------------+
|                Frontend (React + Vite + TS)                 |
|  Workspace | Agent Dashboard | Graph Explorer | Reports UI  |
+------------------------------+------------------------------+
                               | HTTP API & SSE Events
+------------------------------v------------------------------+
|                FastAPI Backend Service                      |
|                                                             |
|  +--------------------+     +----------------------------+  |
|  | Multi-Agent Swarm  |     |   Orchestration Engine     |  |
|  | - Coordinator      |     |   - Task State Machine     |  |
|  | - Researcher       |     |   - Dependency Scheduler   |  |
|  | - Analyst          |     |   - Event Bus (SSE)        |  |
|  | - Critic           |     |   - Budget Enforcement     |  |
|  | - Planner          |     +--------------+-------------+  |
|  | - Synthesizer      |                    |                |
|  +---------+----------+                    |                |
|            |                               |                |
|  +---------v-------------------------------v-------------+  |
|  |             Graph Repository Interface                |  |
|  |             (Protocol Abstraction)                    |  |
|  +---------------------------+---------------------------+  |
+------------------------------|------------------------------+
                               |
            +------------------+------------------+
            |                                     |
+-----------v------------+            +-----------v------------+
|   LocalGraphAdapter    |            |    FalkorDBAdapter     |
| (In-memory, dev/tests) |            | (FalkorDB Cloud Graph) |
+------------------------+            +------------------------+
```

## Key Architectural Rules

1. **Decoupled Persistence**: The application interacts with graph storage strictly via the `GraphRepository` protocol.
2. **Cloud Switchability**: Switching from local development mode to FalkorDB Cloud is controlled via `GRAPH_BACKEND=falkordb` and environment credentials.
3. **Frontend Isolation**: The frontend never connects directly to the database; all queries pass through validated backend API endpoints.
4. **Agent Integrity**: Agents never manage database connections directly. They interact via domain tools (`memory_search`, `record_finding`, etc.).
