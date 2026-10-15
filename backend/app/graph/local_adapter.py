import asyncio
from datetime import datetime
from typing import Any
import uuid

from app.graph.base import GraphRepository
from app.schemas.project import Project, ProjectUpdate
from app.schemas.run import Run
from app.schemas.task import Task
from app.schemas.memory import Memory, MemoryUpdate
from app.schemas.claim import Claim, Source
from app.schemas.graph import GraphData, GraphNode, GraphEdge


class LocalGraphAdapter(GraphRepository):
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._projects: dict[str, Project] = {}
        self._runs: dict[str, Run] = {}
        self._tasks: dict[str, Task] = {}
        self._memories: dict[str, Memory] = {}
        self._claims: dict[str, Claim] = {}
        self._sources: dict[str, Source] = {}
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []
        self._is_initialized = False

    async def initialize(self) -> None:
        async with self._lock:
            self._is_initialized = True

    async def close(self) -> None:
        async with self._lock:
            self._is_initialized = False

    async def check_health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "backend": "local",
            "initialized": self._is_initialized,
            "project_count": len(self._projects),
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
        }

    async def create_project(self, project: Project) -> Project:
        async with self._lock:
            self._projects[project.id] = project
            self._nodes[project.id] = GraphNode(
                id=project.id,
                label="Project",
                title=project.name,
                properties={"description": project.description, "created_at": project.created_at.isoformat()},
            )
            return project

    async def get_project(self, project_id: str) -> Project | None:
        async with self._lock:
            return self._projects.get(project_id)

    async def list_projects(self) -> list[Project]:
        async with self._lock:
            return sorted(self._projects.values(), key=lambda p: p.created_at, reverse=True)

    async def update_project(self, project_id: str, updates: ProjectUpdate) -> Project | None:
        async with self._lock:
            project = self._projects.get(project_id)
            if not project:
                return None
            if updates.name is not None:
                project.name = updates.name
            if updates.description is not None:
                project.description = updates.description
            project.updated_at = datetime.utcnow()
            if project.id in self._nodes:
                self._nodes[project.id].title = project.name
                self._nodes[project.id].properties["description"] = project.description
            return project

    async def delete_project(self, project_id: str) -> bool:
        async with self._lock:
            if project_id not in self._projects:
                return False
            del self._projects[project_id]
            self._nodes.pop(project_id, None)
            self._edges = [e for e in self._edges if e.source != project_id and e.target != project_id]
            return True

    async def create_run(self, run: Run) -> Run:
        async with self._lock:
            self._runs[run.id] = run
            self._nodes[run.id] = GraphNode(
                id=run.id,
                label="Run",
                title=f"Run: {run.goal[:30]}...",
                properties={"status": run.status, "goal": run.goal, "project_id": run.project_id},
            )
            if run.project_id in self._projects:
                edge_id = f"edge-{run.project_id}-has_run-{run.id}"
                self._edges.append(
                    GraphEdge(
                        id=edge_id,
                        source=run.project_id,
                        target=run.id,
                        relationship="HAS_RUN",
                    )
                )
            return run

    async def get_run(self, run_id: str) -> Run | None:
        async with self._lock:
            return self._runs.get(run_id)

    async def list_runs(self, project_id: str) -> list[Run]:
        async with self._lock:
            return [r for r in self._runs.values() if r.project_id == project_id]

    async def update_run_status(self, run_id: str, status: str, completed_at: datetime | None = None) -> Run | None:
        async with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return None
            run.status = status
            if completed_at:
                run.completed_at = completed_at
            if run_id in self._nodes:
                self._nodes[run_id].properties["status"] = status
            return run

    async def create_task(self, task: Task) -> Task:
        async with self._lock:
            self._tasks[task.id] = task
            self._nodes[task.id] = GraphNode(
                id=task.id,
                label="Task",
                title=task.title,
                properties={
                    "status": task.status,
                    "priority": task.priority,
                    "assigned_role": task.assigned_role,
                    "run_id": task.run_id,
                },
            )
            self._edges.append(
                GraphEdge(
                    id=f"edge-{task.run_id}-has_task-{task.id}",
                    source=task.run_id,
                    target=task.id,
                    relationship="HAS_TASK",
                )
            )
            for dep_id in task.dependencies:
                self._edges.append(
                    GraphEdge(
                        id=f"edge-{task.id}-depends_on-{dep_id}",
                        source=task.id,
                        target=dep_id,
                        relationship="DEPENDS_ON",
                    )
                )
            return task

    async def get_task(self, task_id: str) -> Task | None:
        async with self._lock:
            return self._tasks.get(task_id)

    async def list_tasks(self, run_id: str) -> list[Task]:
        async with self._lock:
            return [t for t in self._tasks.values() if t.run_id == run_id]

    async def update_task_status(self, task_id: str, status: str, result: dict[str, Any] | None = None, error: str | None = None) -> Task | None:
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            task.status = status
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            if status == "running" and not task.started_at:
                task.started_at = datetime.utcnow()
            elif status in ("completed", "failed", "cancelled") and not task.completed_at:
                task.completed_at = datetime.utcnow()
            if task_id in self._nodes:
                self._nodes[task_id].properties["status"] = status
            return task

    async def save_memory(self, memory: Memory) -> Memory:
        async with self._lock:
            self._memories[memory.id] = memory
            self._nodes[memory.id] = GraphNode(
                id=memory.id,
                label="Memory",
                title=memory.content[:40] + ("..." if len(memory.content) > 40 else ""),
                properties={
                    "content": memory.content,
                    "memory_type": memory.memory_type,
                    "confidence": memory.confidence,
                    "project_id": memory.project_id,
                    "agent_role": memory.agent_role,
                },
            )
            self._edges.append(
                GraphEdge(
                    id=f"edge-{memory.project_id}-about-{memory.id}",
                    source=memory.project_id,
                    target=memory.id,
                    relationship="ABOUT",
                )
            )
            if memory.agent_id:
                self._edges.append(
                    GraphEdge(
                        id=f"edge-{memory.agent_id}-produced-{memory.id}",
                        source=memory.agent_id,
                        target=memory.id,
                        relationship="PRODUCED",
                    )
                )
            return memory

    async def get_memory(self, memory_id: str) -> Memory | None:
        async with self._lock:
            return self._memories.get(memory_id)

    async def list_memories(self, project_id: str, query: str | None = None, limit: int = 50) -> list[Memory]:
        async with self._lock:
            results = [m for m in self._memories.values() if m.project_id == project_id]
            if query:
                q_lower = query.lower()
                results = [m for m in results if q_lower in m.content.lower()]
            return sorted(results, key=lambda m: m.created_at, reverse=True)[:limit]

    async def update_memory(self, memory_id: str, updates: MemoryUpdate) -> Memory | None:
        async with self._lock:
            memory = self._memories.get(memory_id)
            if not memory:
                return None
            if updates.content is not None:
                memory.content = updates.content
            if updates.memory_type is not None:
                memory.memory_type = updates.memory_type
            if updates.confidence is not None:
                memory.confidence = updates.confidence
            memory.updated_at = datetime.utcnow()
            if memory_id in self._nodes:
                self._nodes[memory_id].title = memory.content[:40]
                self._nodes[memory_id].properties["content"] = memory.content
            return memory

    async def delete_memory(self, memory_id: str) -> bool:
        async with self._lock:
            if memory_id not in self._memories:
                return False
            del self._memories[memory_id]
            self._nodes.pop(memory_id, None)
            self._edges = [e for e in self._edges if e.source != memory_id and e.target != memory_id]
            return True

    async def save_claim(self, claim: Claim) -> Claim:
        async with self._lock:
            self._claims[claim.id] = claim
            self._nodes[claim.id] = GraphNode(
                id=claim.id,
                label="Claim",
                title=claim.text[:40] + ("..." if len(claim.text) > 40 else ""),
                properties={
                    "text": claim.text,
                    "confidence": claim.confidence,
                    "status": claim.status,
                    "project_id": claim.project_id,
                },
            )
            for src_id in claim.supporting_source_ids:
                self._edges.append(
                    GraphEdge(
                        id=f"edge-{src_id}-supports-{claim.id}",
                        source=src_id,
                        target=claim.id,
                        relationship="SUPPORTS",
                    )
                )
            for contra_id in claim.contradicting_claim_ids:
                self._edges.append(
                    GraphEdge(
                        id=f"edge-{claim.id}-contradicts-{contra_id}",
                        source=claim.id,
                        target=contra_id,
                        relationship="CONTRADICTS",
                    )
                )
            return claim

    async def get_claim(self, claim_id: str) -> Claim | None:
        async with self._lock:
            return self._claims.get(claim_id)

    async def list_claims(self, project_id: str, run_id: str | None = None) -> list[Claim]:
        async with self._lock:
            claims = [c for c in self._claims.values() if c.project_id == project_id]
            if run_id:
                claims = [c for c in claims if c.run_id == run_id]
            return claims

    async def record_contradiction(self, claim_a_id: str, claim_b_id: str, notes: str = "") -> None:
        async with self._lock:
            edge_id = f"contra-{claim_a_id}-{claim_b_id}"
            self._edges.append(
                GraphEdge(
                    id=edge_id,
                    source=claim_a_id,
                    target=claim_b_id,
                    relationship="CONTRADICTS",
                    properties={"notes": notes, "detected_at": datetime.utcnow().isoformat()},
                )
            )
            if claim_a_id in self._claims:
                self._claims[claim_a_id].status = "contradicted"
                if claim_b_id not in self._claims[claim_a_id].contradicting_claim_ids:
                    self._claims[claim_a_id].contradicting_claim_ids.append(claim_b_id)
            if claim_b_id in self._claims:
                self._claims[claim_b_id].status = "contradicted"
                if claim_a_id not in self._claims[claim_b_id].contradicting_claim_ids:
                    self._claims[claim_b_id].contradicting_claim_ids.append(claim_a_id)

    async def save_source(self, source: Source) -> Source:
        async with self._lock:
            self._sources[source.id] = source
            self._nodes[source.id] = GraphNode(
                id=source.id,
                label="Source",
                title=source.title,
                properties={"uri": source.uri, "source_type": source.source_type},
            )
            return source

    async def record_relationship(self, source_id: str, target_id: str, rel_type: str, properties: dict[str, Any] | None = None) -> None:
        async with self._lock:
            edge_id = f"edge-{source_id}-{rel_type.lower()}-{target_id}-{uuid.uuid4().hex[:6]}"
            self._edges.append(
                GraphEdge(
                    id=edge_id,
                    source=source_id,
                    target=target_id,
                    relationship=rel_type,
                    properties=properties or {},
                )
            )

    async def get_project_graph(self, project_id: str, node_types: list[str] | None = None, limit: int = 150) -> GraphData:
        async with self._lock:
            project_nodes: list[GraphNode] = []
            for n in self._nodes.values():
                if n.id == project_id or n.properties.get("project_id") == project_id:
                    if node_types is None or n.label in node_types:
                        project_nodes.append(n)

            node_ids = {n.id for n in project_nodes}
            relevant_edges = [e for e in self._edges if e.source in node_ids and e.target in node_ids]
            return GraphData(nodes=project_nodes[:limit], edges=relevant_edges[:limit])

    async def traverse_graph(self, project_id: str, node_id: str, depth: int = 2) -> GraphData:
        async with self._lock:
            if node_id not in self._nodes:
                return GraphData()

            visited_node_ids = {node_id}
            frontier = {node_id}
            traversed_edges: list[GraphEdge] = []

            for _ in range(depth):
                next_frontier = set()
                for edge in self._edges:
                    if edge.source in frontier and edge.target not in visited_node_ids:
                        traversed_edges.append(edge)
                        visited_node_ids.add(edge.target)
                        next_frontier.add(edge.target)
                    elif edge.target in frontier and edge.source not in visited_node_ids:
                        traversed_edges.append(edge)
                        visited_node_ids.add(edge.source)
                        next_frontier.add(edge.source)
                frontier = next_frontier

            nodes = [self._nodes[nid] for nid in visited_node_ids if nid in self._nodes]
            return GraphData(nodes=nodes, edges=traversed_edges)

    async def find_contradictions(self, project_id: str) -> list[dict[str, Any]]:
        async with self._lock:
            results: list[dict[str, Any]] = []
            for edge in self._edges:
                if edge.relationship == "CONTRADICTS":
                    claim_a = self._claims.get(edge.source)
                    claim_b = self._claims.get(edge.target)
                    if claim_a and claim_b and (claim_a.project_id == project_id or claim_b.project_id == project_id):
                        results.append({
                            "claim_a_id": claim_a.id,
                            "claim_a_text": claim_a.text,
                            "claim_b_id": claim_b.id,
                            "claim_b_text": claim_b.text,
                            "notes": edge.properties.get("notes", ""),
                        })
            return results
