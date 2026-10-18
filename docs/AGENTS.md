# SwarmMind Agent Swarm Architecture & Prompt Matrix

SwarmMind deploys a collaborative team of role-specialized AI agents whose cognition, coordination, and memory are grounded in **FalkorDB**.

---

## 🤖 The Specialized Agent Roles

| Role | Name / Title | Core Responsibility | Primary Graph Read/Write Actions |
|---|---|---|---|
| **Coordinator** | `M&A Lead Partner` / `Incident Commander` | Decomposes high-level goals into a directed acyclic task graph (DAG). Monitors task states, dependencies, and handoffs. | Writes `(:Task)` and `[:DEPENDS_ON]` edges. Reads overall project progress via `[:HAS_TASK]`. |
| **Researcher** | `IP & Forensics Auditor` / `Telemetry Inspector` | Ingests primary sources (pitch decks, Git SBOMs, court filings, Terraform manifests) and extracts empirical claims with confidence scores. | Writes `(:Source)`, `(:Claim)`, and `(Source)-[:SUPPORTS]->(Claim)`. |
| **Analyst** | `Systems & Valuation Analyst` / `Kernel Analyst` | Evaluates quantitative claims, analyzes architecture telemetry, checks uptime models, and determines valuation impact. | Reads `(:Claim)` nodes. Writes `(:Memory {type: 'insight'})` and `(Claim)-[:ABOUT]->(Project)`. |
| **Critic** | `Contradiction & Escrow Critic` / `Contradiction Verifier` | Cross-examines all findings for factual contradictions, license contamination, or unverified claims. Executes the procedural reinforcement loop. | Writes `(Claim)-[:CONTRADICTS]->(Claim)`. Adjusts procedural rule confidence: `+0.08` on verify, `-0.15` on dispute. |
| **Planner** | `Deal Structuring Strategist` / `Database Architect` | Formulates risk mitigation frameworks, escrow withholding covenants, and remediation roadmaps. | Reads active disputes. Writes `(:Memory {type: 'policy'})` and `(:Decision)`. |
| **Synthesizer** | `Due Diligence Synthesizer` / `Post-Mortem Synthesizer` | Evaluates evidence authority via native FalkorDB PageRank (`algo.pageRank`) to anchor executive summaries in the most heavily evidenced claims. | Calls `CALL algo.pageRank('Claim', 'SUPPORTS')`. Writes final `(:Artifact)` and links episode reflections via `[:RECORDED_EPISODE]`. |

---

## 🧠 Cognitive Memory Injection into Agent Prompts

Before every agent reasoning step, SwarmMind queries FalkorDB to condition the agent's context window on:
1. **Active Procedural Rules**: Heuristics with confidence $\ge 0.55$ derived from prior successful runs.
2. **Past Episodic Lessons**: Outcomes and challenges flagged in previous workspace runs.

### Cypher Query for Prompt Conditioning:
```cypher
MATCH (m:Memory {memory_type: 'procedural'})
WHERE m.confidence >= $min_confidence AND (m.invalid_at IS NULL OR m.invalid_at = '')
  AND ($project_id IS NULL OR $project_id = '' OR m.project_id = $project_id)
RETURN m.id AS id, m.instruction AS instruction, m.confidence AS confidence
ORDER BY m.confidence DESC LIMIT 5
```

### Injected Prompt Structure:
```text
[System Prompt for Role]

### Active Operational Heuristics (Learned from prior runs):
- Cross-reference all founder proprietary IP assertions against the Git SBOM for GPL/AGPL copyleft triggers before approving valuation. (confidence: 0.68)
- Verify multi-region uptime claims against raw cloud infrastructure configurations rather than marketing materials. (confidence: 0.60)

### Past Episodic Lessons & Challenges in Workspace:
- Prior run [run-apexai-audit-eval]: challenged - Detected material founder misrepresentation on proprietary IP and infrastructure reliability; triggered escrow withholding protocol.
```

---

## 🔄 Dynamic Procedural Reinforcement Loop

SwarmMind agents don't follow static instructions; their heuristics evolve based on empirical validation:
- When the **Critic** verifies a claim supported by a procedural rule, it executes:
  ```cypher
  MATCH (m:Memory {memory_type: 'procedural', project_id: $project_id})
  SET m.confidence = CASE WHEN m.confidence + 0.08 > 1.0 THEN 1.0 ELSE m.confidence + 0.08 END,
      m.successes = coalesce(m.successes, 0) + 1
  ```
- When the **Critic** discovers a factual contradiction or invalid claim, it penalizes the governing rule:
  ```cypher
  MATCH (m:Memory {memory_type: 'procedural', project_id: $project_id})
  SET m.confidence = CASE WHEN m.confidence - 0.15 < 0.0 THEN 0.0 ELSE m.confidence - 0.15 END,
      m.failures = coalesce(m.failures, 0) + 1
  ```
- Rules that fall below $0.55$ confidence are automatically evicted from future prompt injection.
