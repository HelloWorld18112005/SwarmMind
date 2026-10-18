# SwarmMind Graph Schema & Cypher Specifications

## Node Types

| Label | Primary Key | Key Attributes | Description |
|---|---|---|---|
| `User` | `id` | `name`, `email` | Project owner |
| `Project` | `id` | `name`, `description`, `created_at` | Scoped collaborative workspace |
| `Run` | `id` | `project_id`, `status`, `goal`, `started_at`, `completed_at` | One investigation lifecycle |
| `Agent` | `id` | `role`, `name`, `model` | Active agent in run |
| `Task` | `id` | `title`, `status`, `priority`, `agent_role` | Granular unit of work |
| `Memory` | `id` | `project_id`, `content`, `memory_type`, `created_at` | Shared persistent fact |
| `Claim` | `id` | `text`, `confidence`, `status`, `verification_status` | Evaluated proposition |
| `Source` | `id` | `title`, `uri`, `source_type` | Document/URL reference |
| `Turn` | `id` | `run_id`, `role`, `content`, `agent_id`, `timestamp` | Persistent conversational turn |
| `Decision` | `id` | `summary`, `status`, `created_at` | Synthesized conclusion |
| `Artifact` | `id` | `title`, `artifact_type`, `content` | Generated report/deliverable |

## Relationship Types

| Relationship | Source Label | Target Label | Semantics |
|---|---|---|---|
| `OWNS` | `User` | `Project` | User owns project workspace |
| `HAS_RUN` | `Project` | `Run` | Project execution history |
| `INCLUDES_AGENT` | `Run` | `Agent` | Team member participating in run |
| `HAS_TASK` | `Run` | `Task` | Task plan item |
| `ASSIGNED_TO` | `Task` | `Agent` | Agent assigned to task |
| `DEPENDS_ON` | `Task` | `Task` | Prerequisite task dependency |
| `HANDED_OFF_TO` | `Task` | `Task` | Inter-agent task handoff with execution context and timestamp |
| `HAS_TURN` | `Run` | `Turn` | Links run to first turn in conversation chain |
| `NEXT_TURN` | `Turn` | `Turn` | Sequential ordered turn linked-list in graph |
| `MENTIONS` | `Turn` | `Claim` / `Memory` / `Source` | Citation and grounding of chat turn to graph entities |
| `RECORDED_EPISODE`| `Run` | `Memory` | Links execution run to retrospective episodic memories |
| `SUPERSEDES` | `Memory` | `Memory` | Semantic versioning where newer knowledge invalidates older facts |
| `PRODUCED` | `Agent` | `Memory` / `Artifact` | Agent provenance for finding |
| `SUPPORTS` | `Source` / `Memory` | `Claim` | Evidence supporting a claim |
| `CONTRADICTS` | `Claim` | `Claim` | Explicit contradiction/conflict between claims |
| `DERIVED_FROM` | `Memory` | `Claim` / `Memory` / `Source` | Lineage of deductions |
| `ABOUT` | `Memory` / `Claim` | `Project` / `Task` / `Decision` | Topical categorization |
| `SHARES_WITH` | `Agent` | `Memory` | Selective agent context |
| `INFORMED_BY` | `Decision` | `Claim` / `Memory` | Justification for decisions |
| `CREATED` | `Run` | `Artifact` | Run deliverable output |

## Cognitive Memory Tiers

SwarmMind implements a 3-tier cognitive memory architecture:
1. **Semantic Memory (`memory_type='semantic'`):** Shared domain facts with bi-temporal timestamps (`valid_at`, `invalid_at`). When conflicting or updated facts emerge, a `[:SUPERSEDES]` relationship is created and the obsolete memory is stamped with `invalid_at`.
2. **Episodic Memory (`memory_type='episodic'`):** Retrospective run summaries connected via `(Run)-[:RECORDED_EPISODE]->(Memory)`, allowing multi-run reflection and context transfer.
3. **Procedural Memory (`memory_type='procedural'`):** Operational heuristics and guidelines evaluated dynamically. Uses an automated reinforcement loop: $+0.08$ confidence boost when rules lead to verified claims, $-0.15$ penalty when rules lead to contradictions. Highly confident rules (`confidence >= 0.50`) are injected into agent system prompts under `### Active Operational Heuristics (Learned from prior runs)`.

## Native FalkorDB Graph Algorithms

1. **PageRank Centrality (`CALL algo.pageRank('Claim', 'SUPPORTS')`):**
   Calculates claim authority based on incoming support citations. Synthesizer agents anchor final executive findings in the highest-scoring claims.
2. **Shortest-Path Traversal (`CALL algo.SPpaths($start_id, $end_id, 'SUPPORTS|CONTRADICTS|DERIVED_FROM')`):**
   Traverses the explainability path between any two nodes, returning the exact sequence of identifiers powering the interactive Provenance Modal in the UI.

