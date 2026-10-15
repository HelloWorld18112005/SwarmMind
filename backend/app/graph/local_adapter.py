from datetime import datetime
import asyncio
from collections import deque
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
    """In-memory GraphRepository simulating Cypher traversal and relationships for offline testing."""

    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}
        self._runs: dict[str, Run] = {}
        self._tasks: dict[str, Task] = {}
        self._memories: dict[str, Memory] = {}
        self._claims: dict[str, Claim] = {}
        self._sources: dict[str, Source] = {}
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []
        self._lock = asyncio.Lock()
        self._is_initialized = False

    async def initialize(self) -> None:
        self._is_initialized = True

    async def close(self) -> None:
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
                properties={"name": project.name, "description": project.description, "project_id": project.id},
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
            proj = self._projects.get(project_id)
            if not proj:
                return None
            if updates.name is not None:
                proj.name = updates.name
            if updates.description is not None:
                proj.description = updates.description
            proj.updated_at = datetime.utcnow()
            if project_id in self._nodes:
                self._nodes[project_id].title = proj.name
                self._nodes[project_id].properties["name"] = proj.name
                self._nodes[project_id].properties["description"] = proj.description
            return proj

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
                title=run.goal[:35] + ("..." if len(run.goal) > 35 else ""),
                properties={"goal": run.goal, "status": run.status, "project_id": run.project_id},
            )
            self._edges.append(
                GraphEdge(
                    id=f"edge-{run.project_id}-has_run-{run.id}",
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
            runs = [r for r in self._runs.values() if r.project_id == project_id]
            return sorted(runs, key=lambda r: r.started_at, reverse=True)

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
                    "assigned_role": task.assigned_role,
                    "status": task.status,
                    "priority": task.priority,
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
            tasks = [t for t in self._tasks.values() if t.run_id == run_id]
            return sorted(tasks, key=lambda t: t.created_at)

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> Task | None:
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
            elif status in ("completed", "failed", "cancelled"):
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
                    "agent_role": claim.agent_role,
                },
            )
            for src_id in claim.supporting_source_ids:
                self._edges.append(
                    GraphEdge(
                        id=f"edge-{claim.id}-cites-{src_id}",
                        source=claim.id,
                        target=src_id,
                        relationship="CITES",
                    )
                )
            return claim

    async def get_claim(self, claim_id: str) -> Claim | None:
        async with self._lock:
            return self._claims.get(claim_id)

    async def list_claims(self, project_id: str, run_id: str | None = None) -> list[Claim]:
        async with self._lock:
            results = [c for c in self._claims.values() if c.project_id == project_id]
            if run_id:
                results = [c for c in results if c.run_id == run_id]
            return sorted(results, key=lambda c: c.created_at, reverse=True)

    async def record_contradiction(self, claim_a_id: str, claim_b_id: str, notes: str = "") -> None:
        async with self._lock:
            edge_id = f"edge-{claim_a_id}-contradicts-{claim_b_id}"
            self._edges.append(
                GraphEdge(
                    id=edge_id,
                    source=claim_a_id,
                    target=claim_b_id,
                    relationship="CONTRADICTS",
                    properties={"notes": notes},
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
        return await self.trace_provenance(project_id, node_id, max_depth=depth)

    async def trace_provenance(self, project_id: str, node_id: str, max_depth: int = 4) -> GraphData:
        async with self._lock:
            if node_id not in self._nodes:
                return GraphData()

            visited_node_ids = {node_id}
            frontier = {node_id}
            traversed_edges: list[GraphEdge] = []

            for _ in range(max_depth):
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
                if not frontier:
                    break

            nodes = [self._nodes[nid] for nid in visited_node_ids if nid in self._nodes]
            return GraphData(nodes=nodes, edges=traversed_edges)

    async def find_shortest_path(self, project_id: str, start_id: str, end_id: str) -> GraphData:
        async with self._lock:
            if start_id not in self._nodes or end_id not in self._nodes:
                return GraphData()

            if start_id == end_id:
                return GraphData(nodes=[self._nodes[start_id]], edges=[])

            # BFS finding shortest path
            queue: deque[tuple[str, list[GraphEdge]]] = deque([(start_id, [])])
            visited = {start_id}

            while queue:
                curr_node_id, path_edges = queue.popleft()
                if curr_node_id == end_id:
                    path_nodes_set = {start_id, end_id}
                    for edge in path_edges:
                        path_nodes_set.add(edge.source)
                        path_nodes_set.add(edge.target)
                    nodes = [self._nodes[nid] for nid in path_nodes_set if nid in self._nodes]
                    return GraphData(nodes=nodes, edges=path_edges)

                # Find all neighbors
                for edge in self._edges:
                    neighbor_id = None
                    if edge.source == curr_node_id and edge.target not in visited:
                        neighbor_id = edge.target
                    elif edge.target == curr_node_id and edge.source not in visited:
                        neighbor_id = edge.source

                    if neighbor_id:
                        visited.add(neighbor_id)
                        queue.append((neighbor_id, path_edges + [edge]))

            return GraphData()

    async def find_contradictions(self, project_id: str) -> list[dict[str, Any]]:
        return await self.get_disputes_with_evidence(project_id)

    async def get_disputes_with_evidence(self, project_id: str) -> list[dict[str, Any]]:
        async with self._lock:
            results: list[dict[str, Any]] = []
            for edge in self._edges:
                if edge.relationship == "CONTRADICTS":
                    claim_a = self._claims.get(edge.source)
                    claim_b = self._claims.get(edge.target)
                    if claim_a and claim_b:
                        sources_a = [self._sources[sid] for sid in claim_a.supporting_source_ids if sid in self._sources]
                        sources_b = [self._sources[sid] for sid in claim_b.supporting_source_ids if sid in self._sources]

                        results.append({
                            "claim_a_id": claim_a.id,
                            "claim_a_text": claim_a.text,
                            "claim_a_confidence": claim_a.confidence,
                            "claim_a_sources": [{"title": s.title, "uri": s.uri} for s in sources_a],
                            "claim_b_id": claim_b.id,
                            "claim_b_text": claim_b.text,
                            "claim_b_confidence": claim_b.confidence,
                            "claim_b_sources": [{"title": s.title, "uri": s.uri} for s in sources_b],
                            "notes": edge.properties.get("notes", "Evidence conflict detected by Critic."),
                            "dispute_reason": edge.properties.get("notes", "Evidence conflict detected by Critic."),
                            "recommendation": edge.properties.get("recommendation", "Preserve dispute in graph memory."),
                        })
            return results
