# Testing and Quality Verification Guide

This guide details the automated test suite, quality benchmarks, and verification procedures for SwarmMind.

---

## 🧪 Test Suite Overview

SwarmMind includes **34 comprehensive unit and integration tests** validating:
1. **Multi-Agent Orchestration**: DAG task scheduling, concurrent execution, dependency resolution, and state transitions.
2. **Cognitive Memory Subsystem**: 3-tier memory (Semantic bi-temporal validity, Episodic run reflection, Procedural dynamic reinforcement).
3. **Graph Persistence & Algorithms**: Both `LocalGraphAdapter` and `FalkorDBAdapter`, including PageRank and shortest-path traversals.
4. **Security & Data Isolation**: API key redaction (`sk-...`, `AIzaSy...`), Cypher parameterization injection defense, and multi-tenant graph isolation.
5. **REST API & SSE Endpoints**: Full CRUD for projects, runs, tasks, claims, memories, graph inspection, and chat turns.
6. **M&A Due Diligence & Production Outage Seeds**: Verification of VentureAudit ($45M ApexAI deal) and Incident Investigation datasets.

---

## 🚀 Running the Tests

### 1. In-Memory Mode (Fast, Zero Dependencies)
Run all 34 tests in sub-second offline mode:
```bash
cd backend
GRAPH_BACKEND=local uv run pytest tests/unit
```
Expected output:
```text
======================= 34 passed, 421 warnings in 0.42s =======================
```

### 2. FalkorDB Docker / Cloud Mode
To execute tests against a live FalkorDB instance:
```bash
# 1. Start FalkorDB locally
docker run --rm -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest

# 2. Run test suite with FalkorDB backend
cd backend
GRAPH_BACKEND=falkordb FALKORDB_HOST=localhost FALKORDB_SSL=false uv run pytest tests/unit
```

---

## 🎯 Quality Evaluation Benchmark

SwarmMind includes an automated evaluation benchmark (`app.evaluation.benchmark`) that scores the system against three strict quality gates:
1. **Contradiction Recall Rate (>= 90%)**: Verifies whether the Critic agent successfully detects seeded evidential conflicts (e.g. Founder 100% proprietary claim vs GPLv3 copyleft contamination).
2. **Citation Grounding Rate (>= 75%)**: Verifies that every empirical claim is anchored to primary source documents (`[:SUPPORTS]` or `[:CITES]`).
3. **Task Completion Rate (>= 80%)**: Verifies that all dependency-ordered tasks in the DAG executed to completion.

### Executing the Benchmark
```bash
cd backend
GRAPH_BACKEND=local uv run python -m app.evaluation.benchmark
```

Expected output:
```text
==================================================
        SWARMMIND QUALITY BENCHMARK REPORT        
==================================================
Project ID:               proj-apexai-audit
Claims Grounded:          4/4 (100.0%)
Contradiction Recall:     2/1 (100.0%)
Tasks Completed:          6/6 (100.0%)
Sources Integrated:       4
--------------------------------------------------
OVERALL EVALUATION GATE:  PASSED [100%]
==================================================
```

---

## 🌐 Frontend Verification

Validate that the React 18 + Vite + TypeScript application builds with zero errors:
```bash
cd frontend
npm run build
```
Expected output:
```text
vite v5.4.x building for production...
✓ 1652 modules transformed.
dist/index.html                   0.88 kB
dist/assets/index-xxx.css        30.16 kB
dist/assets/index-xxx.js        404.73 kB
✓ built in ~1.5s
```

---

## 🔍 Pre-Flight Verification Checklist

Before demoing or submitting:
- [x] All 34 pytest tests pass: `GRAPH_BACKEND=local uv run pytest tests/unit`
- [x] Evaluation benchmark passes with 100% score: `GRAPH_BACKEND=local uv run python -m app.evaluation.benchmark`
- [x] Frontend builds with zero TypeScript errors: `npm run build`
- [x] Seed data populates cleanly: `GRAPH_BACKEND=local uv run python scripts/seed_demo_data.py`
- [x] Health endpoint responds with `status: "healthy"`: `curl http://localhost:8000/api/health`
