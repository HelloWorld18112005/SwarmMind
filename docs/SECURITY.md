# SwarmMind Security, Privacy & Isolation Architecture

SwarmMind enforces multi-layered enterprise security controls across multi-agent communications, graph database interactions, and user workspaces.

---

## 1. Secret Redaction Engine

Because multi-agent swarms ingest heterogeneous text from tools, web pages, and model completions, sensitive credentials must never leak into persistent graph storage or shared agent memory.

SwarmMind implements an in-process, high-performance regex sanitizer located at [`backend/app/security/redaction.py`](file:///c:/Users/ankur/Desktop/swarmmind/backend/app/security/redaction.py).

### Protected Credential Patterns

| Secret Type | Regex Pattern | Redaction Output |
|---|---|---|
| **OpenAI API Key** | `sk-[a-zA-Z0-9_-]{20,}` | `sk-***[REDACTED]***` |
| **Google Gemini Key** | `AIzaSy[a-zA-Z0-9_-]{33}` | `AIzaSy***[REDACTED]***` |
| **FalkorDB / Redis Password** | `(?:password\|passwd\|pwd)\s*[:=]\s*['"]?([^'"\s&;]+)['"]?` | `password=***[REDACTED]***` |
| **Bearer Authorization Token** | `Bearer\s+[a-zA-Z0-9_\-\.]{16,}` | `Bearer ***[REDACTED]***` |
| **Generic Secret Assignments** | `(?:api[_-]?key\|secret)\s*[:=]\s*['"]?([^'"\s&;]+)['"]?` | `key=***[REDACTED]***` |

### Enforcement Point
Secret redaction is hooked into `MemoryService.save_memory()` and `MemoryService.create_claim()`. Any memory or claim written to either `LocalGraphAdapter` or `FalkorDBAdapter` is scrubbed prior to persistence.

---

## 2. Cypher Injection Prevention & Query Parameterization

All database reads and writes execute through parameterized Cypher queries:
- Query identifiers (`labels`, `relationship_types`) are strictly sanitized via [`app/security/sanitization.py`](file:///c:/Users/ankur/Desktop/swarmmind/backend/app/security/sanitization.py), permitting only alphanumeric characters and underscores (`[A-Za-z0-9_]`).
- All user-supplied strings, goals, memory texts, IDs, and filters are bound as Cypher parameters (e.g. `MATCH (p:Project {id: $id})`), eliminating Cypher string interpolation vulnerabilities.

---

## 3. Workspace & Cross-Project Isolation

SwarmMind enforces strict boundary isolation between projects:
- Every Cypher query and memory lookup is explicitly filtered by `project_id`.
- Automated test [`backend/tests/unit/test_security_isolation.py`](file:///c:/Users/ankur/Desktop/swarmmind/backend/tests/unit/test_security_isolation.py) verifies that claims, memories, and graph nodes created in Project A are completely inaccessible from queries originating in Project B.

---

## 4. Execution Budget & Financial Governance

To prevent runaway agent loops, denial of wallet, or infinite recursion:
1. **Agent Step Limit**: Hard maximum of 20 execution steps per run (`MAX_AGENT_STEPS = 20`).
2. **Execution Timeout**: 10-minute wall-clock cap (`MAX_RUN_DURATION_SECONDS = 600`).
3. **Concurrency Bounding**: Maximum of 3 concurrent agent tasks (`MAX_CONCURRENT_AGENTS = 3`).
4. **Token & Cost Accounting**: Live financial tracking computed at:
   - Input: **$0.50 per 1M tokens**
   - Output: **$1.50 per 1M tokens**
   - Live telemetry exposed via `GET /api/runs/{run_id}/budget` and displayed in the frontend workspace header.
