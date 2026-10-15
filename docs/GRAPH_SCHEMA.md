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
| `PRODUCED` | `Agent` | `Memory` | `Artifact` | Agent provenance for finding |
| `SUPPORTS` | `Source` | `Memory` | `Claim` | Evidence supporting a claim |
| `CONTRADICTS` | `Claim` | `Claim` | Explicit contradiction/conflict |
| `DERIVED_FROM` | `Memory` | `Claim` | `Memory` | `Source` | Lineage of deductions |
| `ABOUT` | `Memory` | `Claim` | `Project` | `Task` | `Decision` | Topical categorization |
| `SHARES_WITH` | `Agent` | `Memory` | Selective agent context |
| `INFORMED_BY` | `Decision` | `Claim` | `Memory` | Justification for decisions |
| `CREATED` | `Run` | `Artifact` | Run deliverable output |
