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
from app.schemas.chat import Turn


class LocalGraphAdapter(GraphRepository):
    """In-memory GraphRepository simulating Cypher traversal and relationships for offline testing."""

    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}
        self._runs: dict[str, Run] = {}
        self._tasks: dict[str, Task] = {}
        self._memories: dict[str, Memory] = {}
        self._claims: dict[str, Claim] = {}
        self._sources: dict[str, Source] = {}
        self._turns: dict[str, Turn] = {}
        self._episodes: list[dict[str, Any]] = []
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
            "database": "local",
            "nodes": len(self._nodes),
            "edges": len(self._edges),
            "initialized": self._is_initialized,
            "project_count": len(self._projects),
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

            # Cascade delete all runs, tasks, memories, claims, sources belonging to this project
            run_ids = {r.id for r in self._runs.values() if r.project_id == project_id}
            for r_id in run_ids:
                self._runs.pop(r_id, None)

            task_ids = {t.id for t in self._tasks.values() if t.project_id == project_id}
            for t_id in task_ids:
                self._tasks.pop(t_id, None)

            claim_ids = {c.id for c in self._claims.values() if c.project_id == project_id}
            for c_id in claim_ids:
                self._claims.pop(c_id, None)

            source_ids = {s.id for s in self._sources.values() if s.project_id == project_id}
            for s_id in source_ids:
                self._sources.pop(s_id, None)

            mem_ids = {m.id for m in self._memories.values() if m.project_id == project_id}
            for m_id in mem_ids:
                self._memories.pop(m_id, None)

            # Clean nodes and edges
            to_remove_nodes = {
                n_id for n_id, n in self._nodes.items()
                if n_id == project_id
                or n.properties.get("project_id") == project_id
                or n_id in run_ids
                or n_id in task_ids
                or n_id in claim_ids
                or n_id in mem_ids
                or n_id in source_ids
            }
            for n_id in to_remove_nodes:
                self._nodes.pop(n_id, None)

            self._edges = [
                e for e in self._edges
                if e.source not in to_remove_nodes and e.target not in to_remove_nodes
            ]
            return True

    async def clear_all(self) -> None:
        async with self._lock:
            self._projects.clear()
            self._runs.clear()
            self._tasks.clear()
            self._memories.clear()
            self._claims.clear()
            self._sources.clear()
            self._turns.clear()
            self._episodes.clear()
            self._nodes.clear()
            self._edges.clear()

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
            # Filter out invalidated / superseded memories
            results = [m for m in self._memories.values() if m.project_id == project_id and not m.invalid_at]
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
            if updates.instruction is not None:
                memory.instruction = updates.instruction
            if updates.confidence is not None:
                memory.confidence = updates.confidence
            if updates.valid_at is not None:
                memory.valid_at = updates.valid_at
            if updates.invalid_at is not None:
                memory.invalid_at = updates.invalid_at
            if updates.successes is not None:
                memory.successes = updates.successes
            if updates.failures is not None:
                memory.failures = updates.failures
            memory.updated_at = datetime.utcnow()
            if memory_id in self._nodes:
                self._nodes[memory_id].title = memory.content[:40]
                self._nodes[memory_id].properties["content"] = memory.content
                self._nodes[memory_id].properties["confidence"] = memory.confidence
            return memory

    async def delete_memory(self, memory_id: str) -> bool:
        async with self._lock:
            if memory_id not in self._memories:
                return False
            del self._memories[memory_id]
            self._nodes.pop(memory_id, None)
            self._edges = [e for e in self._edges if e.source != memory_id and e.target != memory_id]
            return True

    async def supersede_memory(self, old_memory_id: str, new_memory: Memory) -> Memory:
        async with self._lock:
            old_mem = self._memories.get(old_memory_id)
            if old_mem:
                old_mem.invalid_at = datetime.utcnow()
                if old_memory_id in self._nodes:
                    self._nodes[old_memory_id].properties["invalid_at"] = old_mem.invalid_at.isoformat()
            await self.save_memory(new_memory)
            await self.record_relationship(new_memory.id, old_memory_id, "SUPERSEDES")
            return new_memory

    async def get_procedural_memories(self, project_id: str, min_confidence: float = 0.55, limit: int = 5) -> list[Memory]:
        async with self._lock:
            procs = [
                m for m in self._memories.values()
                if m.project_id == project_id
                and m.memory_type == "procedural"
                and m.confidence >= min_confidence
                and not m.invalid_at
            ]
            return sorted(procs, key=lambda m: m.confidence, reverse=True)[:limit]

    async def adjust_procedural_confidence(self, project_id: str, delta: float) -> list[Memory]:
        async with self._lock:
            updated_list: list[Memory] = []
            for m in self._memories.values():
                if m.project_id == project_id and m.memory_type == "procedural":
                    m.confidence = max(0.0, min(1.0, m.confidence + delta))
                    if delta > 0:
                        m.successes += 1
                    elif delta < 0:
                        m.failures += 1
                    m.updated_at = datetime.utcnow()
                    if m.id in self._nodes:
                        self._nodes[m.id].properties["confidence"] = m.confidence
                        self._nodes[m.id].properties["successes"] = m.successes
                        self._nodes[m.id].properties["failures"] = m.failures
                    updated_list.append(m)
            return updated_list

    async def record_episode(self, run_id: str, memory_id: str, outcome: str) -> None:
        async with self._lock:
            episode = {
                "run_id": run_id,
                "memory_id": memory_id,
                "outcome": outcome,
                "recorded_at": datetime.utcnow().isoformat(),
            }
            self._episodes.append(episode)
            self._edges.append(
                GraphEdge(
                    id=f"edge-{run_id}-episode-{memory_id}",
                    source=run_id,
                    target=memory_id,
                    relationship="RECORDED_EPISODE",
                    properties={"outcome": outcome},
                )
            )

    async def get_episodes(self, project_id: str, limit: int = 10) -> list[dict[str, Any]]:
        async with self._lock:
            run_ids = {r.id for r in self._runs.values() if r.project_id == project_id}
            episodes = [ep for ep in self._episodes if ep["run_id"] in run_ids]
            # Attach memory content
            for ep in episodes:
                mem = self._memories.get(ep["memory_id"])
                if mem:
                    ep["content"] = mem.content
            return episodes[:limit]

    async def create_turn(self, turn: Turn) -> Turn:
        async with self._lock:
            self._turns[turn.id] = turn
            self._nodes[turn.id] = GraphNode(
                id=turn.id,
                label="Turn",
                title=f"[{turn.role}] {turn.content[:35]}",
                properties={"role": turn.role, "content": turn.content, "run_id": turn.run_id},
            )
            # Link Run -> Turn
            self._edges.append(
                GraphEdge(
                    id=f"edge-{turn.run_id}-has_turn-{turn.id}",
                    source=turn.run_id,
                    target=turn.id,
                    relationship="HAS_TURN",
                )
            )
            # Link Prev Turn -> Turn
            if turn.prev_turn_id:
                self._edges.append(
                    GraphEdge(
                        id=f"edge-{turn.prev_turn_id}-next_turn-{turn.id}",
                        source=turn.prev_turn_id,
                        target=turn.id,
                        relationship="NEXT_TURN",
                    )
                )
            # Link Turn -> Claim mentions
            for cid in turn.mentioned_claim_ids:
                if cid in self._claims:
                    self._edges.append(
                        GraphEdge(
                            id=f"edge-{turn.id}-mentions-{cid}",
                            source=turn.id,
                            target=cid,
                            relationship="MENTIONS",
                        )
                    )
            return turn

    async def list_turns(self, run_id: str) -> list[Turn]:
        async with self._lock:
            turns = [t for t in self._turns.values() if t.run_id == run_id]
            return sorted(turns, key=lambda t: t.created_at)

    async def get_conversation_history(self, run_id: str) -> list[Turn]:
        """Traverse conversation turns in sequence order."""
        return await self.list_turns(run_id)

    async def record_turn_mention(self, turn_id: str, claim_id: str) -> None:
        async with self._lock:
            self._edges.append(
                GraphEdge(
                    id=f"edge-{turn_id}-mentions-{claim_id}",
                    source=turn_id,
                    target=claim_id,
                    relationship="MENTIONS",
                )
            )

    async def record_task_handoff(
        self,
        from_task_id: str,
        to_task_id: str,
        from_agent: str = "",
        to_agent: str = "",
        context: str = "",
    ) -> None:
        async with self._lock:
            self._edges.append(
                GraphEdge(
                    id=f"edge-handoff-{from_task_id}-{to_task_id}",
                    source=from_task_id,
                    target=to_task_id,
                    relationship="HANDED_OFF_TO",
                    properties={
                        "from_agent": from_agent,
                        "to_agent": to_agent,
                        "context": context,
                        "at": datetime.utcnow().isoformat(),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            )

    async def get_claim_authority(self, project_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Rank claims by centrality using graph in-degree support."""
        async with self._lock:
            claims = [c for c in self._claims.values() if c.project_id == project_id]
            scored = []
            for c in claims:
                in_degree = sum(1 for e in self._edges if e.target == c.id and e.relationship in ("SUPPORTS", "DERIVED_FROM", "CITES"))
                score = round(c.confidence * (1.0 + 0.3 * in_degree), 3)
                scored.append({"claim_id": c.id, "text": c.text, "claim": c.text, "score": score})
            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:limit]

    # Backward-compatible alias
    rank_evidence_authority = get_claim_authority

    async def trace_evidence_path(self, project_id: str, start_id: str, end_id: str) -> list[str]:
        path_data = await self.find_shortest_path(project_id, start_id, end_id)
        if not path_data.nodes:
            return [start_id, end_id]
        return [n.title for n in path_data.nodes]

    # Backward-compatible alias
    async def trace_shortest_path_algo(self, project_id: str, claim_a_id: str, claim_b_id: str) -> list[str]:
        return await self.trace_evidence_path(project_id, claim_a_id, claim_b_id)

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
            if claim.project_id:
                self._edges.append(
                    GraphEdge(
                        id=f"edge-{claim.project_id}-about-{claim.id}",
                        source=claim.project_id,
                        target=claim.id,
                        relationship="ABOUT",
                    )
                )
            if claim.agent_id:
                self._edges.append(
                    GraphEdge(
                        id=f"edge-{claim.agent_id}-produced-{claim.id}",
                        source=claim.agent_id,
                        target=claim.id,
                        relationship="PRODUCED",
                    )
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
