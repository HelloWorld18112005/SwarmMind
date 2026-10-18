# SwarmMind Security, Isolation & Governance

SwarmMind enforces enterprise-grade security boundaries across graph storage, agent execution, and credential handling.

---

## 🛡️ Core Security Architecture

### 1. Multi-Tenant Physical Multigraph Isolation
Rather than using soft filtering (e.g. `WHERE p.tenant_id = $id`), SwarmMind leverages FalkorDB's native multigraph topology:
- Every project/tenant is mapped to an isolated FalkorDB graph: `swarmmind_{clean_project_id}`.
- Cross-tenant queries are structurally impossible at the database engine level.
- Deleting a project cleanly invokes `GRAPH.DELETE`, scrubbing all associated tenant nodes and relationships without affecting other workspaces.

### 2. Secret Redaction Engine (`app.security.redaction`)
Before any text content, source snippet, or memory is persisted to FalkorDB:
- All common API keys and access tokens are detected via regular expression matching:
  - OpenAI / Anthropic keys (`sk-[A-Za-z0-9_-]{32,}`)
  - Google Cloud / Gemini keys (`AIzaSy[A-Za-z0-9_-]{33}`)
  - AWS Access Keys (`AKIA[0-9A-Z]{16}`)
  - Generic Bearer tokens and private credentials
- Matches are sanitized to `[REDACTED_SECRET]` before persistence, preventing credential leaks into the shared graph memory.

### 3. Cypher Injection Defense (`app.security.sanitization`)
- All Cypher queries strictly use parameterized Cypher syntax (`$project_id`, `$claim_id`, `$delta`).
- Any dynamic identifiers (such as graph names) undergo strict regex character filtering (`^[a-zA-Z0-9_-]+$`) to prevent graph escape vectors.

### 4. Financial Budgets & Token Accounting
- Swarm runs are governed by token budgets and duration guardrails:
  - Default input pricing: `$0.50` per 1M tokens.
  - Default output pricing: `$1.50` per 1M tokens.
  - Per-run ceiling: Maximum 20 agent steps and 600-second execution timeout.
  - Runs exceeding budgets trigger automatic graceful termination, preventing runaway API expenditures.
