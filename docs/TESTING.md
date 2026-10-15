# SwarmMind Testing & Quality Verification Guide

SwarmMind includes a comprehensive automated test harness covering unit tests, contract tests, security isolation tests, and an evaluation benchmark suite.

---

## 1. Automated Test Suites

### Backend Unit & Integration Tests (33 Passed)
Execute the complete test suite:
```bash
python -m pytest backend/tests
```

#### Test Inventory
| Test Suite | File | Coverage |
|---|---|---|
| **Agents & Roles** | `backend/tests/unit/test_agents.py` | Role registration, prompt formatting, structured JSON output validation |
| **Quality Benchmark** | `backend/tests/unit/test_benchmark.py` | Contradiction recall, citation grounding, DAG ordering |
| **Budget Controls** | `backend/tests/unit/test_budgets.py` | Step bounding, token counting, cost calculation, timeout limits |
| **Configuration** | `backend/tests/unit/test_config.py` | Environment variable parsing, default fallback values |
| **Conflict Detection** | `backend/tests/unit/test_conflicts.py` | Jaccard similarity, contradiction recording, dispute retrieval |
| **Explainability** | `backend/tests/unit/test_explainability.py` | Multi-hop provenance tracing, shortest path BFS, dispute evidence |
| **Graph Adapter** | `backend/tests/unit/test_graph_adapter.py` | CRUD operations, schema initialization, relationship queries |
| **Graph API** | `backend/tests/unit/test_graph_api.py` | Subgraph filtering, shortest-path endpoint, conflict endpoint |
| **System Health** | `backend/tests/unit/test_health.py` | Health check endpoint, database status response |
| **LLM Provider** | `backend/tests/unit/test_llm_adapter.py` | Mock, Gemini, and OpenAI provider adapters, retry policies |
| **Memory Subsystem**| `backend/tests/unit/test_memory_service.py` | Memory creation, retrieval, deduplication, correction |
| **Swarm Orchestration**| `backend/tests/unit/test_orchestration.py` | DAG scheduler, dependency checks, state machine transitions, event bus |
| **Projects API** | `backend/tests/unit/test_projects.py` | Project creation, update, listing, deletion |
| **Report Generation** | `backend/tests/unit/test_report_service.py` | Synthesis, markdown formatting, dispute preservation |
| **Security & Isolation**| `backend/tests/unit/test_security_isolation.py` | Cross-project isolation, secret redaction (`sk-...`, `AIzaSy...`), Cypher sanitization |
| **Seed Dataset** | `backend/tests/unit/test_seed_data.py` | Signature demo dataset integrity ($5.2B vs $800M contradiction) |

---

## 2. Quality Benchmark Suite

SwarmMind includes a dedicated quality benchmark that evaluates the multi-agent system against four strict evaluation gates:

Execute the benchmark directly:
```bash
python -m app.evaluation.benchmark
```

### Benchmark Results
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

---

## 3. Frontend Type Verification & Build

Verify frontend TypeScript compilation and bundle integrity:
```bash
cd frontend
npm run build
```
- Expectation: `0 TypeScript errors`, clean Vite production bundle generated.
