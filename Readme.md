# 🧠 SwarmMind — Auditable, Graph-Grounded Multi-Agent AI Collaboration

[![FalkorDB Graph Hacks](https://img.shields.io/badge/FalkorDB-Graph%20Hacks-red?style=for-the-badge&logo=redis)](https://app.falkordb.cloud)
[![Tests: 33 Passed](https://img.shields.io/badge/Tests-33%20Passed-brightgreen?style=for-the-badge)](docs/TESTING.md)
[![Quality Benchmark: 100%](https://img.shields.io/badge/Benchmark-100%25%20Passed-blue?style=for-the-badge)](docs/TESTING.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](#)

> **An AI team whose members collaborate through a shared, inspectable, persistent FalkorDB knowledge graph.**
> Built for the **FalkorDB Graph Hacks Hackathon**.

---

## ⚡ Quickstart in 60 Seconds (Zero Docker / Offline Mode)

SwarmMind runs completely out-of-the-box in local development mode without requiring Docker or cloud credentials.

### 1. Launch Backend (FastAPI + Python 3.11+)
```bash
# Windows 1-click:
run_backend.bat

# Or manual:
cd backend
python -m venv venv
venv\Scripts\activate  # On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### 2. Launch Frontend (React + Vite + Tailwind CSS)
```bash
# Windows 1-click:
run_frontend.bat

# Or manual:
cd frontend
npm install
npm run dev
```

Visit **`http://localhost:5173`** to explore the pre-seeded Signature Demo ("AI Tutoring Startup Evaluation")!

---

## ☁️ Connecting to FalkorDB Cloud (1-Step Setup)

When you are ready to connect to FalkorDB Cloud:

1. Create a free graph database at [FalkorDB Cloud](https://app.falkordb.cloud).
2. Update `backend/.env`:
   ```dotenv
   GRAPH_BACKEND=falkordb
   FALKORDB_HOST=<your-instance-subdomain>.falkordb.cloud
   FALKORDB_PORT=6379
   FALKORDB_PASSWORD=<your-database-password>
   FALKORDB_SSL=true
   FALKORDB_GRAPH=swarmmind
   ```
3. Test connectivity and query latency with our built-in diagnostic tool:
   ```bash
   python backend/scripts/test_cloud_connection.py
   ```
4. Seed the signature demo into your cloud instance:
   ```bash
   python backend/scripts/seed_demo_data.py
   ```
5. Restart your backend and refresh your browser. SwarmMind is now live on FalkorDB Cloud!

---

## 🌟 The Core Vision: Why Graph Memory Beats Chat History

Traditional multi-agent frameworks (CrewAI, AutoGen, LangGraph) pass long strings of text between agents in an ephemeral context window. Over time:
- **Critical findings get lost** in context bloat.
- **Contradictory evidence is silently overwritten** by whichever agent generated the latest response.
- **No provenance audit trail**: impossible to verify which agent originated a claim or which source backed it.

### The SwarmMind Paradigm
SwarmMind provides every agent with access to a shared **FalkorDB graph memory**:
- **Role-Specialized Agents**: Coordinator, Researcher, Analyst, Critic, Planner, and Synthesizer.
- **Explicit Dispute Preservation (`CONTRADICTS`)**: When two findings disagree (e.g. market sizing estimates of $5.2B vs $800M), SwarmMind preserves both in the graph with dispute reasons and mitigation recommendations rather than deleting earlier facts.
- **Deterministic Multi-Hop Explainability**: Every recommendation can be traced backward through graph relationships (`INFORMED_BY -> ABOUT -> SUPPORTS -> Source`).
- **Secret Redaction & Injection Shield**: Automatically scrubs API keys (`sk-...`, `AIzaSy...`) prior to graph persistence and uses parameterized Cypher queries exclusively.

---

## 🏛️ System Architecture

```text
┌────────────────────────────────────────────────────────────────┐
│               Frontend: React + Vite + TypeScript              │
│   • Workspace Feed  • Interactive React Flow Graph Explorer    │
│   • Memory Library  • Multi-Hop Provenance Modal • Reports     │
└───────────────────────────────┬────────────────────────────────┘
                                │ HTTP REST + SSE Streaming
┌───────────────────────────────▼────────────────────────────────┐
│                  Backend: Python + FastAPI                     │
│  • Swarm Orchestration Engine (DAG Scheduler + State Machine)  │
│  • Budget Accounting ($0.50/M input, $1.50/M output)           │
│  • Explainability Service (BFS Shortest Path + Provenance)     │
│  • Secret Redaction & Sanitization Boundary                    │
└───────────────────────────────┬────────────────────────────────┘
                                │ GraphRepository Interface
                ┌───────────────┴───────────────┐
                ▼                               ▼
     ┌─────────────────────┐         ┌─────────────────────┐
     │  LocalGraphAdapter  │         │   FalkorDB Cloud    │
     │  (Offline Dev Mode) │         │ (Production Engine) │
     └─────────────────────┘         └─────────────────────┘
```

---

## 📊 FalkorDB Graph Schema

### Entity Nodes
- `User`: Project owner.
- `Project`: Persistent workspace.
- `Run`: Multi-agent investigation run.
- `Agent`: Specialized team member.
- `Task`: Work assigned in the dependency DAG.
- `Memory`: Attributed shared knowledge (`fact`, `insight`, `policy`).
- `Claim`: Evaluated statement with confidence scores.
- `Source`: Primary evidence source (`title`, `uri`, `source_type`).
- `Decision`: Strategic recommendation.

### Relationships
- `(User)-[:OWNS]->(Project)`
- `(Project)-[:HAS_RUN]->(Run)`
- `(Run)-[:INCLUDES_AGENT]->(Agent)`
- `(Run)-[:HAS_TASK]->(Task)`
- `(Task)-[:DEPENDS_ON]->(Task)`
- `(Agent)-[:PRODUCED]->(Memory|Claim)`
- `(Source)-[:SUPPORTS]->(Claim)`
- `(Claim)-[:CONTRADICTS]->(Claim)` *(Disputes explicitly preserved!)*
- `(Decision)-[:INFORMED_BY]->(Claim)`

---

## 🎯 Evaluation Benchmark & Quality Gates

SwarmMind includes an automated evaluation suite (`python -m app.evaluation.benchmark`):

```text
============================================================
              SWARMMIND QUALITY BENCHMARK REPORT
============================================================
  Metric                           Score      Target    Status
------------------------------------------------------------
  Contradiction Recall Rate       100.0%      >=90.0%    PASS
  Citation Grounding Rate         100.0%      >=95.0%    PASS
  Task Completion Rate            100.0%     >=100.0%    PASS
  DAG Dependency Validity         100.0%     >=100.0%    PASS
============================================================
  OVERALL STATUS: ALL EVALUATION GATES PASSED (100.0%)
============================================================
```

Run all 33 unit and integration tests:
```bash
python -m pytest backend/tests
```

---

## 📚 Complete Documentation Suite

- 📖 [**Hackathon Submission Manifesto**](docs/HACKATHON_SUBMISSION.md) — Executive summary, judges guide, and deep-dive.
- 📐 [**System Architecture**](docs/ARCHITECTURE.md) — Detailed technical architecture and data flow.
- 🕸️ [**Graph Schema & Cypher Queries**](docs/GRAPH_SCHEMA.md) — Node labels, relationship types, and Cypher query catalogue.
- 🔌 [**REST & SSE API Reference**](docs/API.md) — Complete endpoint schemas and examples.
- 🤖 [**Agent Swarm & Prompts**](docs/AGENTS.md) — Role definitions, tool access matrix, and state machine.
- 🛡️ [**Security & Governance**](docs/SECURITY.md) — Secret redaction engine, Cypher injection defenses, and financial budgets.
- 🧪 [**Testing & Quality Guide**](docs/TESTING.md) — Test suites, quality benchmark results, and verification commands.

---

## 🏆 Hackathon Submission Checklist

- [x] **P0: Foundation & Contracts**: Clean structure, zero-Docker offline mode, health checks.
- [x] **P1: Graph Memory Subsystem**: Dual adapters (`LocalGraphAdapter` & `FalkorDBAdapter`), seed dataset.
- [x] **P2: LLM Adapter & Agent Swarm**: 6 specialized roles, typed structured outputs.
- [x] **P3: Swarm Orchestration Engine**: DAG scheduler, state machine, retries, SSE streaming.
- [x] **P4: Full Frontend Experience**: React Flow graph explorer, slide-over inspector, report viewer with 1-click export.
- [x] **P5: Multi-Hop Explainability**: Cypher path tracing, BFS shortest paths, provenance modals.
- [x] **P6: Quality, Security & Budgets**: Secret redaction (`sk-...`, `AIzaSy...`), Cypher injection defense, automated benchmark suite (100% score).
- [x] **P7: Release & FalkorDB Cloud Ready**: Cloud diagnostic scripts, quickstart launchers, complete documentation suite.

---

## 📄 License
MIT License. Built for the FalkorDB Graph Hacks Hackathon.