from datetime import datetime
import logging
from typing import Any

from app.graph.base import GraphRepository
from app.graph.schema import INDEX_STATEMENTS
from app.graph.queries import (
    CREATE_PROJECT_CYPHER,
    GET_PROJECT_CYPHER,
    LIST_PROJECTS_CYPHER,
    DELETE_PROJECT_CYPHER,
    CREATE_RUN_CYPHER,
    GET_RUN_CYPHER,
    LIST_RUNS_CYPHER,
    UPDATE_RUN_STATUS_CYPHER,
    CREATE_TASK_CYPHER,
    CREATE_MEMORY_CYPHER,
    GET_MEMORIES_BY_PROJECT_CYPHER,
    MERGE_RELATIONSHIP_CYPHER,
    GET_PROJECT_GRAPH_CYPHER,
    TRAVERSE_FROM_NODE_CYPHER,
    FIND_CONTRADICTIONS_CYPHER,
    MULTI_HOP_PROVENANCE_CYPHER,
    SHORTEST_PATH_CYPHER,
    DISPUTES_WITH_EVIDENCE_CYPHER,
)
from app.schemas.project import Project, ProjectUpdate
from app.schemas.run import Run
from app.schemas.task import Task
from app.schemas.memory import Memory, MemoryUpdate
from app.schemas.claim import Claim, Source
from app.schemas.graph import GraphData, GraphNode, GraphEdge

logger = logging.getLogger(__name__)


class FalkorDBAdapter(GraphRepository):
    def __init__(
        self,
        host: str,
        port: int = 6379,
        username: str = "",
        password: str = "",
        ssl: bool = True,
        graph_name: str = "swarmmind",
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssl = ssl
        self.graph_name = graph_name
        self._driver: Any = None
        self._graph: Any = None
        self._is_initialized = False

    async def initialize(self) -> None:
        if not self.host:
            raise ValueError(
                "FalkorDB host is not configured. Set FALKORDB_HOST in .env or switch GRAPH_BACKEND=local."
            )

        try:
            from falkordb import FalkorDB

            self._driver = FalkorDB(
                host=self.host,
                port=self.port,
                username=self.username if self.username else None,
                password=self.password if self.password else None,
                ssl=self.ssl,
            )
            self._graph = self._driver.select_graph(self.graph_name)

            for idx_stmt in INDEX_STATEMENTS:
                try:
                    self._graph.query(idx_stmt)
                except Exception as idx_err:
                    logger.debug(f"Index statement note: {idx_err}")

            self._is_initialized = True
            logger.info(f"Connected to FalkorDB instance at {self.host}:{self.port}, graph: {self.graph_name}")
        except Exception as e:
            self._is_initialized = False
            logger.error(f"Failed to connect to FalkorDB Cloud: {e}")
            raise ConnectionError(
                f"Could not connect to FalkorDB Cloud at {self.host}:{self.port}. "
                f"Check credentials and network access: {e}"
            ) from e

    async def close(self) -> None:
        if self._driver:
            try:
                self._driver.close()
            except Exception as e:
                logger.warning(f"Error closing FalkorDB connection: {e}")
            self._is_initialized = False

    async def check_health(self) -> dict[str, Any]:
        if not self._is_initialized or not self._graph:
            return {
                "status": "unhealthy",
                "backend": "falkordb",
                "host": self.host,
                "error": "Not connected or initialized",
            }
        try:
            res = self._graph.query("RETURN 1 AS ping")
            return {
                "status": "healthy",
                "backend": "falkordb",
                "host": self.host,
                "graph": self.graph_name,
                "ping": res.result_set[0][0] if res.result_set else 1,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "falkordb",
                "host": self.host,
                "error": str(e),
            }

    async def create_project(self, project: Project) -> Project:
        params = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }
        self._graph.query(CREATE_PROJECT_CYPHER, params)
        return project

    async def get_project(self, project_id: str) -> Project | None:
        res = self._graph.query(GET_PROJECT_CYPHER, {"id": project_id})
        if not res.result_set:
            return None
        node = res.result_set[0][0]
        return Project(
            id=node.properties.get("id"),
            name=node.properties.get("name"),
            description=node.properties.get("description", ""),
            created_at=datetime.fromisoformat(node.properties.get("created_at")),
            updated_at=datetime.fromisoformat(node.properties.get("updated_at")),
        )

    async def list_projects(self) -> list[Project]:
        res = self._graph.query(LIST_PROJECTS_CYPHER)
        projects: list[Project] = []
        for row in res.result_set:
            node = row[0]
            projects.append(
                Project(
                    id=node.properties.get("id"),
                    name=node.properties.get("name"),
                    description=node.properties.get("description", ""),
                    created_at=datetime.fromisoformat(node.properties.get("created_at")),
                    updated_at=datetime.fromisoformat(node.properties.get("updated_at")),
                )
            )
        return projects

    async def update_project(self, project_id: str, updates: ProjectUpdate) -> Project | None:
        existing = await self.get_project(project_id)
        if not existing:
            return None
        if updates.name is not None:
            existing.name = updates.name
        if updates.description is not None:
            existing.description = updates.description
        existing.updated_at = datetime.utcnow()
        await self.create_project(existing)
        return existing

    async def delete_project(self, project_id: str) -> bool:
        self._graph.query(DELETE_PROJECT_CYPHER, {"id": project_id})
        return True

    async def create_run(self, run: Run) -> Run:
        params = {
            "id": run.id,
            "project_id": run.project_id,
            "goal": run.goal,
            "status": run.status,
            "started_at": run.started_at.isoformat(),
        }
        self._graph.query(CREATE_RUN_CYPHER, params)
        return run

    async def get_run(self, run_id: str) -> Run | None:
        res = self._graph.query(GET_RUN_CYPHER, {"id": run_id})
        if not res.result_set:
            return None
        node = res.result_set[0][0]
        completed = node.properties.get("completed_at")
        return Run(
            id=node.properties.get("id"),
            project_id=node.properties.get("project_id"),
            goal=node.properties.get("goal"),
            status=node.properties.get("status"),
            started_at=datetime.fromisoformat(node.properties.get("started_at")),
            completed_at=datetime.fromisoformat(completed) if completed else None,
        )

    async def list_runs(self, project_id: str) -> list[Run]:
        res = self._graph.query(LIST_RUNS_CYPHER, {"project_id": project_id})
        runs: list[Run] = []
        for row in res.result_set:
            node = row[0]
            completed = node.properties.get("completed_at")
            runs.append(
                Run(
                    id=node.properties.get("id"),
                    project_id=node.properties.get("project_id"),
                    goal=node.properties.get("goal"),
                    status=node.properties.get("status"),
                    started_at=datetime.fromisoformat(node.properties.get("started_at")),
                    completed_at=datetime.fromisoformat(completed) if completed else None,
                )
            )
        return runs

    async def update_run_status(self, run_id: str, status: str, completed_at: datetime | None = None) -> Run | None:
        params = {
            "id": run_id,
            "status": status,
            "completed_at": completed_at.isoformat() if completed_at else None,
        }
        self._graph.query(UPDATE_RUN_STATUS_CYPHER, params)
        return await self.get_run(run_id)

    async def create_task(self, task: Task) -> Task:
        params = {
            "id": task.id,
            "run_id": task.run_id,
            "title": task.title,
            "description": task.description,
            "assigned_role": task.assigned_role,
            "status": task.status,
            "priority": task.priority,
            "created_at": task.created_at.isoformat(),
        }
        self._graph.query(CREATE_TASK_CYPHER, params)
        for dep in task.dependencies:
            await self.record_relationship(task.id, dep, "DEPENDS_ON")
        return task

    async def get_task(self, task_id: str) -> Task | None:
        query = "MATCH (t:Task {id: $id}) RETURN t"
        res = self._graph.query(query, {"id": task_id})
        if not res.result_set:
            return None
        node = res.result_set[0][0]
        return Task(
            id=node.properties.get("id"),
            run_id=node.properties.get("run_id"),
            title=node.properties.get("title"),
            description=node.properties.get("description", ""),
            assigned_role=node.properties.get("assigned_role"),
            status=node.properties.get("status"),
            priority=node.properties.get("priority", "medium"),
            created_at=datetime.fromisoformat(node.properties.get("created_at")),
        )

    async def list_tasks(self, run_id: str) -> list[Task]:
        query = "MATCH (r:Run {id: $run_id})-[:HAS_TASK]->(t:Task) RETURN t ORDER BY t.created_at"
        res = self._graph.query(query, {"run_id": run_id})
        tasks: list[Task] = []
        for row in res.result_set:
            node = row[0]
            tasks.append(
                Task(
                    id=node.properties.get("id"),
                    run_id=node.properties.get("run_id"),
                    title=node.properties.get("title"),
                    description=node.properties.get("description", ""),
                    assigned_role=node.properties.get("assigned_role"),
                    status=node.properties.get("status"),
                    priority=node.properties.get("priority", "medium"),
                    created_at=datetime.fromisoformat(node.properties.get("created_at")),
                )
            )
        return tasks

    async def update_task_status(self, task_id: str, status: str, result: dict[str, Any] | None = None, error: str | None = None) -> Task | None:
        query = "MATCH (t:Task {id: $id}) SET t.status = $status RETURN t"
        self._graph.query(query, {"id": task_id, "status": status})
        return await self.get_task(task_id)

    async def save_memory(self, memory: Memory) -> Memory:
        params = {
            "id": memory.id,
            "project_id": memory.project_id,
            "run_id": memory.run_id or "",
            "agent_id": memory.agent_id or "",
            "agent_role": memory.agent_role or "",
            "content": memory.content,
            "memory_type": memory.memory_type,
            "confidence": memory.confidence,
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
        }
        self._graph.query(CREATE_MEMORY_CYPHER, params)
        if memory.agent_id:
            await self.record_relationship(memory.agent_id, memory.id, "PRODUCED")
        return memory

    async def get_memory(self, memory_id: str) -> Memory | None:
        query = "MATCH (m:Memory {id: $id}) RETURN m"
        res = self._graph.query(query, {"id": memory_id})
        if not res.result_set:
            return None
        node = res.result_set[0][0]
        return Memory(
            id=node.properties.get("id"),
            project_id=node.properties.get("project_id"),
            run_id=node.properties.get("run_id") or None,
            agent_id=node.properties.get("agent_id") or None,
            agent_role=node.properties.get("agent_role") or None,
            content=node.properties.get("content"),
            memory_type=node.properties.get("memory_type", "fact"),
            confidence=float(node.properties.get("confidence", 0.8)),
            created_at=datetime.fromisoformat(node.properties.get("created_at")),
            updated_at=datetime.fromisoformat(node.properties.get("updated_at")),
        )

    async def list_memories(self, project_id: str, query: str | None = None, limit: int = 50) -> list[Memory]:
        res = self._graph.query(GET_MEMORIES_BY_PROJECT_CYPHER, {"project_id": project_id, "limit": limit})
        memories: list[Memory] = []
        for row in res.result_set:
            node = row[0]
            memories.append(
                Memory(
                    id=node.properties.get("id"),
                    project_id=node.properties.get("project_id"),
                    run_id=node.properties.get("run_id") or None,
                    agent_id=node.properties.get("agent_id") or None,
                    agent_role=node.properties.get("agent_role") or None,
                    content=node.properties.get("content"),
                    memory_type=node.properties.get("memory_type", "fact"),
                    confidence=float(node.properties.get("confidence", 0.8)),
                    created_at=datetime.fromisoformat(node.properties.get("created_at")),
                    updated_at=datetime.fromisoformat(node.properties.get("updated_at")),
                )
            )
        if query:
            q_lower = query.lower()
            memories = [m for m in memories if q_lower in m.content.lower()]
        return memories

    async def update_memory(self, memory_id: str, updates: MemoryUpdate) -> Memory | None:
        mem = await self.get_memory(memory_id)
        if not mem:
            return None
        if updates.content is not None:
            mem.content = updates.content
        if updates.memory_type is not None:
            mem.memory_type = updates.memory_type
        if updates.confidence is not None:
            mem.confidence = updates.confidence
        mem.updated_at = datetime.utcnow()
        await self.save_memory(mem)
        return mem

    async def delete_memory(self, memory_id: str) -> bool:
        query = "MATCH (m:Memory {id: $id}) DETACH DELETE m"
        self._graph.query(query, {"id": memory_id})
        return True

    async def save_claim(self, claim: Claim) -> Claim:
        cypher = """
        MATCH (p:Project {id: $project_id})
        MERGE (c:Claim {id: $id})
        ON CREATE SET c.project_id = $project_id, c.run_id = $run_id, c.agent_id = $agent_id,
                      c.agent_role = $agent_role, c.text = $text, c.confidence = $confidence,
                      c.status = $status, c.created_at = $created_at
        MERGE (p)-[:ABOUT]->(c)
        RETURN c
        """
        params = {
            "id": claim.id,
            "project_id": claim.project_id,
            "run_id": claim.run_id or "",
            "agent_id": claim.agent_id or "",
            "agent_role": claim.agent_role or "",
            "text": claim.text,
            "confidence": claim.confidence,
            "status": claim.status,
            "created_at": claim.created_at.isoformat(),
        }
        self._graph.query(cypher, params)
        for s_id in claim.supporting_source_ids:
            await self.record_relationship(s_id, claim.id, "SUPPORTS")
        for c_id in claim.contradicting_claim_ids:
            await self.record_relationship(claim.id, c_id, "CONTRADICTS")
        return claim

    async def get_claim(self, claim_id: str) -> Claim | None:
        query = "MATCH (c:Claim {id: $id}) RETURN c"
        res = self._graph.query(query, {"id": claim_id})
        if not res.result_set:
            return None
        node = res.result_set[0][0]
        return Claim(
            id=node.properties.get("id"),
            project_id=node.properties.get("project_id"),
            run_id=node.properties.get("run_id") or None,
            agent_id=node.properties.get("agent_id") or None,
            agent_role=node.properties.get("agent_role") or None,
            text=node.properties.get("text"),
            confidence=float(node.properties.get("confidence", 0.7)),
            status=node.properties.get("status", "proposed"),
            created_at=datetime.fromisoformat(node.properties.get("created_at")),
        )

    async def list_claims(self, project_id: str, run_id: str | None = None) -> list[Claim]:
        query = "MATCH (c:Claim {project_id: $project_id}) RETURN c"
        res = self._graph.query(query, {"project_id": project_id})
        claims: list[Claim] = []
        for row in res.result_set:
            node = row[0]
            claims.append(
                Claim(
                    id=node.properties.get("id"),
                    project_id=node.properties.get("project_id"),
                    run_id=node.properties.get("run_id") or None,
                    agent_id=node.properties.get("agent_id") or None,
                    agent_role=node.properties.get("agent_role") or None,
                    text=node.properties.get("text"),
                    confidence=float(node.properties.get("confidence", 0.7)),
                    status=node.properties.get("status", "proposed"),
                    created_at=datetime.fromisoformat(node.properties.get("created_at")),
                )
            )
        if run_id:
            claims = [c for c in claims if c.run_id == run_id]
        return claims

    async def record_contradiction(self, claim_a_id: str, claim_b_id: str, notes: str = "") -> None:
        cypher = """
        MATCH (a:Claim {id: $claim_a_id}), (b:Claim {id: $claim_b_id})
        MERGE (a)-[r:CONTRADICTS]->(b)
        SET r.notes = $notes, r.detected_at = $detected_at, a.status = 'contradicted', b.status = 'contradicted'
        RETURN r
        """
        self._graph.query(
            cypher,
            {
                "claim_a_id": claim_a_id,
                "claim_b_id": claim_b_id,
                "notes": notes,
                "detected_at": datetime.utcnow().isoformat(),
            },
        )

    async def save_source(self, source: Source) -> Source:
        cypher = """
        MERGE (s:Source {id: $id})
        ON CREATE SET s.title = $title, s.uri = $uri, s.source_type = $source_type
        RETURN s
        """
        self._graph.query(
            cypher,
            {"id": source.id, "title": source.title, "uri": source.uri, "source_type": source.source_type},
        )
        return source

    async def record_relationship(self, source_id: str, target_id: str, rel_type: str, properties: dict[str, Any] | None = None) -> None:
        safe_rel = "".join(c for c in rel_type.upper() if c.isalnum() or c == "_")
        cypher = MERGE_RELATIONSHIP_CYPHER % safe_rel
        self._graph.query(cypher, {"source_id": source_id, "target_id": target_id})

    async def get_project_graph(self, project_id: str, node_types: list[str] | None = None, limit: int = 150) -> GraphData:
        res = self._graph.query(GET_PROJECT_GRAPH_CYPHER, {"project_id": project_id, "limit": limit})
        nodes_dict: dict[str, GraphNode] = {}
        edges_list: list[GraphEdge] = []

        for row in res.result_set:
            node_a, rel, node_b = row[0], row[1], row[2]
            for n in (node_a, node_b):
                if n.properties.get("id") not in nodes_dict:
                    nodes_dict[n.properties.get("id")] = GraphNode(
                        id=n.properties.get("id"),
                        label=list(n.labels)[0] if n.labels else "Entity",
                        title=n.properties.get("name") or n.properties.get("title") or n.properties.get("text", "")[:30],
                        properties=dict(n.properties),
                    )
            edges_list.append(
                GraphEdge(
                    id=f"edge-{node_a.properties.get('id')}-{rel.relation}-{node_b.properties.get('id')}",
                    source=node_a.properties.get("id"),
                    target=node_b.properties.get("id"),
                    relationship=rel.relation,
                    properties=dict(rel.properties),
                )
            )

        return GraphData(nodes=list(nodes_dict.values()), edges=edges_list)

    async def traverse_graph(self, project_id: str, node_id: str, depth: int = 2) -> GraphData:
        res = self._graph.query(TRAVERSE_FROM_NODE_CYPHER, {"node_id": node_id})
        nodes_dict: dict[str, GraphNode] = {}
        edges_list: list[GraphEdge] = []

        for row in res.result_set:
            path = row[0]
            for n in path.nodes:
                if n.properties.get("id") not in nodes_dict:
                    nodes_dict[n.properties.get("id")] = GraphNode(
                        id=n.properties.get("id"),
                        label=list(n.labels)[0] if n.labels else "Entity",
                        title=n.properties.get("name") or n.properties.get("title") or n.properties.get("text", "")[:30],
                        properties=dict(n.properties),
                    )
            for r in path.edges:
                edges_list.append(
                    GraphEdge(
                        id=f"edge-{r.src_node}-{r.relation}-{r.dest_node}",
                        source=str(r.src_node),
                        target=str(r.dest_node),
                        relationship=r.relation,
                        properties=dict(r.properties),
                    )
                )

        return GraphData(nodes=list(nodes_dict.values()), edges=edges_list)

    async def find_contradictions(self, project_id: str) -> list[dict[str, Any]]:
        return await self.get_disputes_with_evidence(project_id)

    async def trace_provenance(self, project_id: str, node_id: str, max_depth: int = 4) -> GraphData:
        try:
            res = self._graph.query(MULTI_HOP_PROVENANCE_CYPHER, {"node_id": node_id, "limit": 50})
            nodes_dict: dict[str, GraphNode] = {}
            edges_list: list[GraphEdge] = []

            for row in res.result_set:
                path = row[0]
                for n in path.nodes:
                    nid = n.properties.get("id")
                    if nid and nid not in nodes_dict:
                        nodes_dict[nid] = GraphNode(
                            id=nid,
                            label=list(n.labels)[0] if n.labels else "Entity",
                            title=n.properties.get("name") or n.properties.get("title") or n.properties.get("text", "")[:30],
                            properties=dict(n.properties),
                        )
                for r in path.edges:
                    edges_list.append(
                        GraphEdge(
                            id=f"edge-{r.src_node}-{r.relation}-{r.dest_node}",
                            source=str(r.src_node),
                            target=str(r.dest_node),
                            relationship=r.relation,
                            properties=dict(r.properties),
                        )
                    )
            return GraphData(nodes=list(nodes_dict.values()), edges=edges_list)
        except Exception as e:
            logger.warning(f"Error executing trace_provenance: {e}")
            return await self.traverse_graph(project_id, node_id, depth=max_depth)

    async def find_shortest_path(self, project_id: str, start_id: str, end_id: str) -> GraphData:
        try:
            res = self._graph.query(SHORTEST_PATH_CYPHER, {"start_id": start_id, "end_id": end_id})
            if not res.result_set:
                return GraphData()
            path = res.result_set[0][0]
            nodes_dict: dict[str, GraphNode] = {}
            edges_list: list[GraphEdge] = []

            for n in path.nodes:
                nid = n.properties.get("id")
                if nid and nid not in nodes_dict:
                    nodes_dict[nid] = GraphNode(
                        id=nid,
                        label=list(n.labels)[0] if n.labels else "Entity",
                        title=n.properties.get("name") or n.properties.get("title") or n.properties.get("text", "")[:30],
                        properties=dict(n.properties),
                    )
            for r in path.edges:
                edges_list.append(
                    GraphEdge(
                        id=f"edge-{r.src_node}-{r.relation}-{r.dest_node}",
                        source=str(r.src_node),
                        target=str(r.dest_node),
                        relationship=r.relation,
                        properties=dict(r.properties),
                    )
                )
            return GraphData(nodes=list(nodes_dict.values()), edges=edges_list)
        except Exception as e:
            logger.warning(f"Error executing find_shortest_path: {e}")
            return GraphData()

    async def get_disputes_with_evidence(self, project_id: str) -> list[dict[str, Any]]:
        try:
            res = self._graph.query(DISPUTES_WITH_EVIDENCE_CYPHER, {"project_id": project_id})
            results: list[dict[str, Any]] = []
            for row in res.result_set:
                results.append({
                    "claim_a_id": row[0],
                    "claim_a_text": row[1],
                    "claim_a_confidence": 0.85,
                    "claim_a_sources": [{"title": row[2], "uri": row[3]}] if row[2] else [],
                    "claim_b_id": row[4],
                    "claim_b_text": row[5],
                    "claim_b_confidence": 0.75,
                    "claim_b_sources": [{"title": row[6], "uri": row[7]}] if row[6] else [],
                    "notes": row[8] or "Contradiction detected",
                    "dispute_reason": row[8] or "Contradiction detected",
                    "recommendation": row[9] or "Preserve dispute in graph memory",
                })
            return results
        except Exception as e:
            logger.warning(f"Error querying disputes with evidence: {e}")
            res = self._graph.query(FIND_CONTRADICTIONS_CYPHER, {"project_id": project_id})
            return [
                {
                    "claim_a_id": row[0],
                    "claim_a_text": row[1],
                    "claim_a_confidence": 0.85,
                    "claim_a_sources": [],
                    "claim_b_id": row[2],
                    "claim_b_text": row[3],
                    "claim_b_confidence": 0.75,
                    "claim_b_sources": [],
                    "notes": row[4] or "",
                    "dispute_reason": row[4] or "",
                    "recommendation": "Preserve dispute",
                }
                for row in res.result_set
            ]

