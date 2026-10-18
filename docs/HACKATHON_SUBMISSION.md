# SwarmMind: Autonomous Multi-Agent Graph Intelligence Engine
> **Powered by FalkorDB** — Built for the WeMakeDevs & FalkorDB "Graph Hacks" Hackathon  
> **Tracks Targeted:**  
> 🏆 **Track 02: Agent Memory and Coordination** (Primary)  
> 🏆 **Track 01: Agents That Act on Connected Data** (Secondary)

---

## 1. Executive Summary

Autonomous AI agents typically operate in isolation: they suffer from amnesia between sessions, hallucinate when reasoning over fragmented documents, execute redundant tasks, and cannot explain why they reached critical conclusions.

**SwarmMind** transforms a swarm of autonomous agents into an elite, self-improving intelligence collective by placing **FalkorDB** at the center of agent cognition. Rather than treating the graph as an external passive store, SwarmMind uses FalkorDB as the **shared working memory, execution coordinator, and reasoning substrate**.

Our flagship demonstration — **VentureAudit** — executes an autonomous technical and intellectual property due diligence audit on **ApexAI** for a simulated **\$45M acquisition**. Five specialized agents (Coordinator, Researcher, Analyst, Critic, Synthesizer) scour Git BOMs, legal documents, infrastructure manifests, and founder claims to uncover hidden IP contamination and single-region outages, recommending escrow holds backed by rigorous Cypher graph traversals and native graph algorithms.

---

## 2. Track Alignment & Core Capabilities

SwarmMind directly addresses the key evaluation criteria of **Track 2** and **Track 1**:

### 🤖 Track 02: Agent Memory and Coordination
| Requirement | SwarmMind Implementation |
|---|---|
| **Episodic, Semantic & Procedural Memory** | **3-Tier Cognitive Memory**: Semantic facts with bi-temporal validity (`valid_at`, `invalid_at`) and `[:SUPERSEDES]`; Episodic run reflections linked via `[:RECORDED_EPISODE]`; Procedural operational heuristics with dynamic reinforcement ($+0.08$ on verification, $-0.15$ on contradiction) and automatic prompt injection. |
| **Persistent Conversation History** | Graph-native `Turn` linked-list: `(Run)-[:HAS_TURN]->(t1)-[:NEXT_TURN]->(t2)` with semantic citations via `(t)-[:MENTIONS]->(Claim\|Memory\|Source)`. |
| **Shared State & Handoffs** | Explicit Cypher handoffs: `(t1)-[:HANDED_OFF_TO {at: timestamp(), context: $context}]->(t2)` passing intermediate findings between agents. |
| **High-Concurrency Reads & Writes** | `BlockingConnectionPool(max_connections=32)` with strict read/write query separation: concurrent reads use `await g.ro_query()`, mutations use `await g.query()`. |
| **Separate Memory per User or Tenant** | **Physical multigraph isolation**: Each project/tenant is mapped to its own isolated FalkorDB graph (`swarmmind_{clean_id}`) preventing cross-tenant data leakage. |

### 🕵️ Track 01: Agents That Act on Connected Data
| Requirement | SwarmMind Implementation |
|---|---|
| **Multi-Hop Reasoning** | Dynamic Cypher multi-hop traversals connecting `Source` $\to$ `Claim` $\to$ `Contradiction` $\to$ `Decision`. |
| **Native Graph Algorithms** | **`algo.pageRank`**: Ranks claim authority in `SynthesizerAgent` based on incoming support citations.<br>**`algo.SPpaths`**: Computes shortest-path explainability sequences between disputed findings. |
| **Tool Selection via FastMCP** | High-performance FastMCP server (`backend/app/mcp_server.py`) exposing FalkorDB PageRank, shortest paths, dispute citations, and claim memory recording. |
| **Actions Driven by Graph State** | Critic detects graph contradictions and applies penalty to procedural rules; Synthesizer anchors final executive summaries in high-PageRank claims. |
| **Explainable Results** | End-to-end provenance tracing via `/api/projects/{id}/graph/paths` and interactive visual inspection modal in React Flow frontend. |

---

## 3. Architecture & Graph Schema

```mermaid
flowchart TD
    subgraph FalkorDB["FalkorDB Engine (Tenant Graph: swarmmind_proj_apexai_audit)"]
        direction TB
        Run["(r:Run)"] -->|HAS_TASK| T1["(t1:Task: Recon)"]
        Run -->|HAS_TASK| T2["(t2:Task: IP Audit)"]
        T1 -->|HANDED_OFF_TO| T2
        
        Run -->|HAS_TURN| Turn1["(turn1:Turn: User)"]
        Turn1 -->|NEXT_TURN| Turn2["(turn2:Turn: Agent)"]
        Turn2 -->|MENTIONS| C1["(c1:Claim: Proprietary Weights)"]
        
        S1["(s1:Source: Git BOM)"] -->|SUPPORTS| C2["(c2:Claim: GPL-3.0 NeoCLIP)"]
        C1 -.->|CONTRADICTS| C2
        
        Run -->|RECORDED_EPISODE| M1["(m1:Memory: Episodic)"]
        M2["(m2:Memory: Semantic)"] -->|SUPERSEDES| M3["(m3:Memory: Obsolete)"]
        M4["(m4:Memory: Procedural Rules)"]
    end

    subgraph Agents["Autonomous Agent Swarm"]
        Coord["Coordinator Agent"]
        Res["Researcher Agent"]
        Ana["Analyst Agent"]
        Crit["Critic Agent (Reinforcement Loop)"]
        Synth["Synthesizer Agent (PageRank Anchoring)"]
    end

    Agents <-->|Async Connection Pool (32 max)| FalkorDB
    Agents -->|Exposed via MCP| FastMCP["FastMCP Server"]
```

### Graph Entities
- **Nodes:** `Project`, `Run`, `Agent`, `Task`, `Turn`, `Claim`, `Source`, `Memory`, `Decision`, `Artifact`.
- **Relationships:** `OWNS`, `HAS_RUN`, `HAS_TASK`, `ASSIGNED_TO`, `DEPENDS_ON`, `HANDED_OFF_TO`, `HAS_TURN`, `NEXT_TURN`, `MENTIONS`, `SUPPORTS`, `CONTRADICTS`, `DERIVED_FROM`, `ABOUT`, `SHARES_WITH`, `INFORMED_BY`, `CREATED`, `RECORDED_EPISODE`, `SUPERSEDES`.

---

## 4. Key Upgrades & Technical Innovations

### 1. 3-Tier Cognitive Memory with Reinforcement Loop
- **Semantic Tier**: Captures domain facts with bi-temporal validation (`valid_at`, `invalid_at`). When a new finding contradicts an old assumption, SwarmMind issues `SUPERSEDES` and invalidates the previous node.
- **Episodic Tier**: Summarizes complete investigation runs into graph episodic nodes (`(Run)-[:RECORDED_EPISODE]->(Memory)`), allowing subsequent runs to retrieve lessons from previous audits.
- **Procedural Tier (Self-Improving)**: Heuristic rules (e.g., *"Flag GPL-3.0 in core inference engine"*, *"Check cross-region failover"*) maintain dynamic confidence scores.
  - When the **Critic** verifies a claim supported by a procedural rule, confidence increases by **$+0.08$** (bounded at 1.0).
  - When the **Critic** identifies a contradiction or invalid claim, confidence is penalized by **$-0.15$** (bounded at 0.0).
  - High-confidence rules ($\ge 0.50$) are automatically extracted from FalkorDB and injected into agent prompts under `### Active Operational Heuristics (Learned from prior runs)`.

### 2. Graph-Native Conversation History
Rather than storing conversation history in flat session cookies or JSON arrays, SwarmMind models chat as a graph-native sequential chain:
- Initial query: `(Run)-[:HAS_TURN]->(Turn)`
- Dialogue continuation: `(Turn)-[:NEXT_TURN]->(Turn)`
- Entity grounding: `(Turn)-[:MENTIONS]->(Claim | Memory | Source)`
- Fast traversal: Ordered Cypher query `MATCH (r:Run {id: $run_id})-[:HAS_TURN]->(first:Turn) ...` reconstructs dialogue history with zero relational joins.

### 3. FalkorDB-Native Algorithms
- **PageRank (`algo.pageRank`)**: The `SynthesizerAgent` executes `CALL algo.pageRank('Claim', 'SUPPORTS')` across the tenant graph. Claims with dense evidential backing are prioritized as primary anchoring facts in the M&A report.
- **Shortest Path (`algo.SPpaths`)**: When users inspect contradictory claims or disputed evidence in the UI, the API executes `CALL algo.SPpaths($start_id, $end_id, 'SUPPORTS|CONTRADICTS|DERIVED_FROM')`, returning the exact path of supporting and contradicting citations.

### 4. Tenant Physical Multigraph Isolation & Async Pool
- Every project operates in an isolated FalkorDB graph (`swarmmind_{project_clean_id}`).
- Database queries use `redis.asyncio.BlockingConnectionPool(max_connections=32)`.
- Query execution separates read operations (`await g.ro_query()`) from write operations (`await g.query()`), enabling high-concurrency multi-agent execution.

### 5. Production Health Checking
The `/api/health` endpoint queries live telemetry using native `GRAPH.INFO`:
```json
{
  "status": "healthy",
  "database": "connected",
  "backend": "falkordb",
  "nodes": 42,
  "edges": 58
}
```
If FalkorDB is unreachable in production mode, the API strictly returns **HTTP 503 Service Unavailable** — guaranteeing no silent in-memory fallbacks degrade evaluation.

---

## 5. FastMCP Tool Server

SwarmMind includes a standalone FastMCP tool server (`backend/app/mcp_server.py`) allowing external LLMs or IDE agents (such as Claude Desktop or Cursor) to directly query the FalkorDB graph:
- `rank_evidence_authority(project_id, limit)`: Centrality ranking via `algo.pageRank`.
- `trace_shortest_path(project_id, claim_a_id, claim_b_id)`: Multi-hop explainability via `algo.SPpaths`.
- `get_disputes_with_evidence(project_id)`: Uncovers conflicting claims and citations.
- `search_graph_memories(project_id, query)`: Traverses semantic and procedural memories.
- `record_claim_evidence(project_id, text, confidence, agent_role)`: Ingests new empirical findings directly into the graph.

---

## 6. Verification & Test Suite

The entire backend and frontend have been rigorously tested and validated:
- **Pytest Suite**: 34 unit tests passing (100% pass rate).
  - Multi-agent orchestration and budget controls (`test_orchestration.py`, `test_budgets.py`)
  - Cognitive memory and procedural reinforcement (`test_memory_service.py`, `test_conflicts.py`)
  - Graph API, shortest path traversal, and PageRank (`test_graph_api.py`, `test_explainability.py`)
  - FalkorDB health checking and strict 503 error handling (`test_health.py`)
  - M&A Due Diligence seed data and multi-turn chat (`test_seed_data.py`, `test_incident_and_chat.py`)
  - Benchmark evaluation suite (`test_benchmark.py`)
- **Frontend Build**: `tsc && vite build` succeeds with zero errors.

---

## 7. Quickstart Guide

### Prerequisites
- Python 3.12+ (or `uv`)
- Node.js 18+
- FalkorDB (Docker or FalkorDB Cloud)

### 1. Launch FalkorDB (Local Docker)
```bash
docker run --rm -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest
```

### 2. Configure Backend
```bash
cd backend
cp .env.example .env
# Set GRAPH_BACKEND=falkordb and host credentials
uv sync
uv run python scripts/seed_demo_data.py
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Launch Frontend
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to explore the **VentureAudit** M&A due diligence graph, run multi-agent investigations, inspect cognitive memory tiers, and trace explainable paths through FalkorDB.
