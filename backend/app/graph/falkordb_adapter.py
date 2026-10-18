from datetime import datetime
import asyncio
import logging
from typing import Any

from falkordb.asyncio import FalkorDB
from redis.asyncio import BlockingConnectionPool

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
    RECORD_TASK_HANDOFF_CYPHER,
    CREATE_MEMORY_CYPHER,
    GET_MEMORIES_BY_PROJECT_CYPHER,
    SUPERSEDE_MEMORY_CYPHER,
    GET_PROCEDURAL_RULES_CYPHER,
    ADJUST_PROCEDURAL_CONFIDENCE_CYPHER,
    RECORD_EPISODE_CYPHER,
    GET_EPISODES_CYPHER,
    CREATE_TURN_CYPHER,
    LIST_TURNS_CYPHER,
    LINK_TURN_MENTION_CYPHER,
    GET_CONVERSATION_HISTORY_CYPHER,
    PAGERANK_CLAIMS_CYPHER,
    SHORTEST_PATH_ALGO_CYPHER,
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
from app.schemas.chat import Turn
from app.schemas.graph import GraphData, GraphNode, GraphEdge

logger = logging.getLogger(__name__)


class EmptyQueryResult:
    def __init__(self) -> None:
        self.result_set: list[Any] = []


class FalkorDBAdapter(GraphRepository):
    """High-concurrency FalkorDB adapter supporting physical multi-tenancy and native graph algorithms."""

    def __init__(
        self,
        host: str,
        port: int = 6379,
        username: str = "",
        password: str = "",
        ssl: bool = False,
        graph_name: str = "swarmmind",
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssl = ssl
        self.graph_name = graph_name
        self._pool: BlockingConnectionPool | None = None
        self.db: FalkorDB | None = None
        self._driver: FalkorDB | None = None
        self._is_initialized = False
        self._entity_to_project: dict[str, str] = {}
        self._initialized_graphs: set[str] = set()

    def get_graph(self, project_id: str | None = None) -> Any:
        """Physical multigraph isolation per project/tenant."""
        driver = self.db or self._driver
        if not driver:
            raise ConnectionError("FalkorDB driver is not initialized.")
        if not project_id:
            return driver.select_graph(self.graph_name)
        clean_id = str(project_id).strip().replace("-", "_")
        if clean_id.startswith("swarmmind_"):
            return driver.select_graph(clean_id)
        return driver.select_graph(f"swarmmind_{clean_id}")

    def _get_graph(self, project_id: str | None = None) -> Any:
        return self.get_graph(project_id)

    async def _ensure_indexes(self, graph: Any, graph_name: str) -> None:
        if graph_name in self._initialized_graphs:
            return
        for idx_stmt in INDEX_STATEMENTS:
            try:
                await graph.query(idx_stmt)
            except Exception as idx_err:
                logger.debug(f"Index check note on {graph_name}: {idx_err}")
        self._initialized_graphs.add(graph_name)

    async def _run(self, cypher: str, params: dict[str, Any] | None = None, project_id: str | None = None) -> Any:
        """Execute a write query natively async (GRAPH.QUERY)."""
        graph = self.get_graph(project_id)
        await self._ensure_indexes(graph, graph.name)
        return await graph.query(cypher, params or {})

    async def _read(self, cypher: str, params: dict[str, Any] | None = None, project_id: str | None = None) -> Any:
        """Execute a read-only query natively async (GRAPH.RO_QUERY)."""
        graph = self.get_graph(project_id)
        try:
            return await graph.ro_query(cypher, params or {})
        except Exception as e:
            if "empty key" in str(e).lower() or "does not exist" in str(e).lower():
                return EmptyQueryResult()
            raise

    async def _resolve_project_id(self, entity_id: str, candidate_query: str | None = None) -> str | None:
        """Resolve entity ID to its parent project graph."""
        if entity_id in self._entity_to_project:
            return self._entity_to_project[entity_id]

        driver = self.db or self._driver
        if not driver:
            return None

        try:
            graphs = await driver.list_graphs()
            for g_item in graphs:
                g_name = g_item.decode() if isinstance(g_item, bytes) else str(g_item)
                if not (g_name == self.graph_name or g_name.startswith("swarmmind_") or g_name.startswith("swarmmind:")):
                    continue
                g = driver.select_graph(g_name)
                cypher = candidate_query or "MATCH (n {id: $id}) RETURN n.project_id AS pid"
                res = await g.ro_query(cypher, {"id": entity_id})
                if res.result_set:
                    row = res.result_set[0]
                    pid = row[0] if (row and row[0]) else g_name.replace("swarmmind_", "").replace("swarmmind:", "")
                    self._entity_to_project[entity_id] = str(pid)
                    return str(pid)
        except Exception as e:
            logger.debug(f"Could not resolve project for entity '{entity_id}': {e}")

        return None

    async def initialize(self) -> None:
        if not self.host:
            raise ValueError(
                "FalkorDB host is not configured. Set FALKORDB_HOST in .env or switch GRAPH_BACKEND=local."
            )

        try:
            pool_kwargs: dict[str, Any] = {
                "host": self.host,
                "port": self.port,
                "max_connections": 32,
            }
            if self.username:
                pool_kwargs["username"] = self.username
            if self.password:
                pool_kwargs["password"] = self.password
            if self.ssl:
                from redis.asyncio.connection import SSLConnection
                pool_kwargs["connection_class"] = SSLConnection

            self._pool = BlockingConnectionPool(**pool_kwargs)
            self.db = FalkorDB(connection_pool=self._pool)
            self._driver = self.db

            # Ensure default graph exists and is indexed
            default_g = self.get_graph()
            await self._ensure_indexes(default_g, self.graph_name)

            self._is_initialized = True
            logger.info(
                f"Connected to FalkorDB at {self.host}:{self.port} "
                f"(ssl={self.ssl}, max_connections=32, physical multigraph isolation enabled)"
            )
        except Exception as e:
            self._is_initialized = False
            logger.error(f"Failed to connect to FalkorDB: {e}")
            raise ConnectionError(
                f"Could not connect to FalkorDB at {self.host}:{self.port}. "
                f"Ensure Docker is running: docker run -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest\n"
                f"Error: {e}"
            ) from e

    async def close(self) -> None:
        driver = self.db or self._driver
        if driver:
            try:
                await driver.aclose()
            except Exception as e:
                logger.warning(f"Error closing FalkorDB driver: {e}")
            self.db = None
            self._driver = None
        if self._pool:
            try:
                await self._pool.disconnect()
            except Exception as e:
                logger.warning(f"Error closing Redis pool: {e}")
            self._pool = None
        self._is_initialized = False

    async def check_health(self) -> dict[str, Any]:
        driver = self.db or self._driver
        if not self._is_initialized or not driver:
            return {
                "status": "unhealthy",
                "database": "falkordb",
                "host": self.host,
                "error": "Not connected or initialized",
            }
        try:
            g = self.get_graph(self.graph_name)
            node_count = 0
            edge_count = 0

            # Query GRAPH.INFO for the active graph
            try:
                info_res = await g.execute_command("GRAPH.INFO", g.name)
                if isinstance(info_res, (list, tuple)):
                    info_dict: dict[str, Any] = {}
                    for i in range(0, len(info_res) - 1, 2):
                        k = info_res[i].decode() if isinstance(info_res[i], bytes) else str(info_res[i])
                        info_dict[k] = info_res[i + 1]
                    node_count = int(info_dict.get("Nodes", info_dict.get("Nodes created", info_dict.get("Number of nodes", 0))))
                    edge_count = int(info_dict.get("Relationships", info_dict.get("Relations created", info_dict.get("Number of edges", 0))))
            except Exception as info_err:
                logger.debug(f"GRAPH.INFO command parse note: {info_err}, falling back to count query")
                n_res = await g.ro_query("MATCH (n) RETURN count(n)")
                node_count = int(n_res.result_set[0][0]) if n_res.result_set else 0
                e_res = await g.ro_query("MATCH ()-[r]->() RETURN count(r)")
                edge_count = int(e_res.result_set[0][0]) if e_res.result_set else 0

            graphs = await driver.list_graphs()
            graph_list = [g_name.decode() if isinstance(g_name, bytes) else str(g_name) for g_name in graphs]

            return {
                "status": "healthy",
                "database": "falkordb",
                "nodes": node_count,
                "edges": edge_count,
                "host": self.host,
                "port": self.port,
                "graph": self.graph_name,
                "ssl": self.ssl,
                "multi_tenancy": True,
                "tenant_graphs": graph_list,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "falkordb",
                "host": self.host,
                "error": str(e),
            }

    # ─────────────────────────── Projects ────────────────────────────

    async def create_project(self, project: Project) -> Project:
        params = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }
        self._entity_to_project[project.id] = project.id
        await self._run(CREATE_PROJECT_CYPHER, params, project_id=project.id)
        return project

    async def get_project(self, project_id: str) -> Project | None:
        res = await self._read(GET_PROJECT_CYPHER, {"id": project_id}, project_id=project_id)
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
        driver = self.db or self._driver
        if not driver:
            return []
        try:
            graphs = await driver.list_graphs()
        except Exception as e:
            logger.error(f"Failed to list graphs: {e}")
            return []

        projects: list[Project] = []
        seen_ids: set[str] = set()

        for g_item in graphs:
            g_name = g_item.decode() if isinstance(g_item, bytes) else str(g_item)
            if not (g_name == self.graph_name or g_name.startswith("swarmmind_") or g_name.startswith("swarmmind:")):
                continue
            try:
                g = driver.select_graph(g_name)
                res = await g.ro_query(LIST_PROJECTS_CYPHER)
                for row in res.result_set:
                    node = row[0]
                    pid = node.properties.get("id")
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        self._entity_to_project[pid] = pid
                        projects.append(
                            Project(
                                id=pid,
                                name=node.properties.get("name"),
                                description=node.properties.get("description", ""),
                                created_at=datetime.fromisoformat(node.properties.get("created_at")),
                                updated_at=datetime.fromisoformat(node.properties.get("updated_at")),
                            )
                        )
            except Exception as e:
                logger.debug(f"Failed to inspect graph '{g_name}' for projects: {e}")

        projects.sort(key=lambda p: p.created_at, reverse=True)
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
        try:
            graph = self.get_graph(project_id)
            await graph.delete()
            self._initialized_graphs.discard(graph.name)
            self._entity_to_project.pop(project_id, None)
            return True
        except Exception as e:
            logger.warning(f"Error deleting tenant graph for project '{project_id}': {e}")
            await self._run(DELETE_PROJECT_CYPHER, {"id": project_id}, project_id=project_id)
            return True

    async def clear_all(self) -> None:
        try:
            projects = await self.list_projects()
            for p in projects:
                await self.delete_project(p.id)
        except Exception as e:
            logger.warning(f"Error during clear_all: {e}")

    # ─────────────────────────── Runs ────────────────────────────────

    async def create_run(self, run: Run) -> Run:
        self._entity_to_project[run.id] = run.project_id
        params = {
            "id": run.id,
            "project_id": run.project_id,
            "goal": run.goal,
            "status": run.status,
            "started_at": run.started_at.isoformat(),
        }
        await self._run(CREATE_RUN_CYPHER, params, project_id=run.project_id)
        return run

    async def get_run(self, run_id: str) -> Run | None:
        proj_id = await self._resolve_project_id(run_id, "MATCH (r:Run {id: $id}) RETURN r.project_id AS pid")
        res = await self._read(GET_RUN_CYPHER, {"id": run_id}, project_id=proj_id)
        if not res.result_set:
            return None
        node = res.result_set[0][0]
        completed = node.properties.get("completed_at")
        p_id = node.properties.get("project_id") or proj_id or ""
        self._entity_to_project[run_id] = p_id
        return Run(
            id=node.properties.get("id"),
            project_id=p_id,
            goal=node.properties.get("goal"),
            status=node.properties.get("status"),
            started_at=datetime.fromisoformat(node.properties.get("started_at")),
            completed_at=datetime.fromisoformat(completed) if completed else None,
        )

    async def list_runs(self, project_id: str) -> list[Run]:
        res = await self._read(LIST_RUNS_CYPHER, {"project_id": project_id}, project_id=project_id)
        runs: list[Run] = []
        for row in res.result_set:
            node = row[0]
            completed = node.properties.get("completed_at")
            rid = node.properties.get("id")
            self._entity_to_project[rid] = project_id
            runs.append(
                Run(
                    id=rid,
                    project_id=node.properties.get("project_id"),
                    goal=node.properties.get("goal"),
                    status=node.properties.get("status"),
                    started_at=datetime.fromisoformat(node.properties.get("started_at")),
                    completed_at=datetime.fromisoformat(completed) if completed else None,
                )
            )
        return runs

    async def update_run_status(self, run_id: str, status: str, completed_at: datetime | None = None) -> Run | None:
        proj_id = await self._resolve_project_id(run_id)
        params = {
            "id": run_id,
            "status": status,
            "completed_at": completed_at.isoformat() if completed_at else None,
        }
        await self._run(UPDATE_RUN_STATUS_CYPHER, params, project_id=proj_id)
        return await self.get_run(run_id)

    # ─────────────────────────── Tasks ───────────────────────────────

    async def create_task(self, task: Task) -> Task:
        proj_id = await self._resolve_project_id(task.run_id)
        self._entity_to_project[task.id] = proj_id or ""
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
        await self._run(CREATE_TASK_CYPHER, params, project_id=proj_id)
        for dep in task.dependencies:
            await self.record_relationship(task.id, dep, "DEPENDS_ON", project_id=proj_id)
        return task

    async def get_task(self, task_id: str) -> Task | None:
        proj_id = await self._resolve_project_id(task_id, "MATCH (t:Task {id: $id}) RETURN t.run_id AS pid")
        query = "MATCH (t:Task {id: $id}) RETURN t"
        res = await self._read(query, {"id": task_id}, project_id=proj_id)
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
        proj_id = await self._resolve_project_id(run_id)
        query = "MATCH (r:Run {id: $run_id})-[:HAS_TASK]->(t:Task) RETURN t ORDER BY t.created_at"
        res = await self._read(query, {"run_id": run_id}, project_id=proj_id)
        tasks: list[Task] = []
        for row in res.result_set:
            node = row[0]
            tid = node.properties.get("id")
            if proj_id:
                self._entity_to_project[tid] = proj_id
            tasks.append(
                Task(
                    id=tid,
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

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> Task | None:
        proj_id = await self._resolve_project_id(task_id)
        query = "MATCH (t:Task {id: $id}) SET t.status = $status RETURN t"
        await self._run(query, {"id": task_id, "status": status}, project_id=proj_id)
        return await self.get_task(task_id)

    async def record_task_handoff(
        self,
        from_task_id: str,
        to_task_id: str,
        from_agent: str = "",
        to_agent: str = "",
        context: str = "",
    ) -> None:
        proj_id = await self._resolve_project_id(from_task_id)
        params = {
            "from_task": from_task_id,
            "to_task": to_task_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._run(RECORD_TASK_HANDOFF_CYPHER, params, project_id=proj_id)

    # ─────────────────────────── Memory ──────────────────────────────

    async def save_memory(self, memory: Memory) -> Memory:
        self._entity_to_project[memory.id] = memory.project_id
        params = {
            "id": memory.id,
            "project_id": memory.project_id,
            "run_id": memory.run_id or "",
            "agent_id": memory.agent_id or "",
            "agent_role": memory.agent_role or "",
            "content": memory.content,
            "memory_type": memory.memory_type,
            "instruction": memory.instruction or "",
            "confidence": memory.confidence,
            "successes": memory.successes,
            "failures": memory.failures,
            "valid_at": memory.valid_at.isoformat() if memory.valid_at else datetime.utcnow().isoformat(),
            "invalid_at": memory.invalid_at.isoformat() if memory.invalid_at else "",
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
        }
        await self._run(CREATE_MEMORY_CYPHER, params, project_id=memory.project_id)
        if memory.agent_id:
            await self.record_relationship(memory.agent_id, memory.id, "PRODUCED", project_id=memory.project_id)
        return memory

    async def get_memory(self, memory_id: str) -> Memory | None:
        proj_id = await self._resolve_project_id(memory_id, "MATCH (m:Memory {id: $id}) RETURN m.project_id AS pid")
        query = "MATCH (m:Memory {id: $id}) RETURN m"
        res = await self._read(query, {"id": memory_id}, project_id=proj_id)
        if not res.result_set:
            return None
        node = res.result_set[0][0]
        v_at = node.properties.get("valid_at")
        iv_at = node.properties.get("invalid_at")
        return Memory(
            id=node.properties.get("id"),
            project_id=node.properties.get("project_id"),
            run_id=node.properties.get("run_id") or None,
            agent_id=node.properties.get("agent_id") or None,
            agent_role=node.properties.get("agent_role") or None,
            content=node.properties.get("content"),
            memory_type=node.properties.get("memory_type", "semantic"),
            instruction=node.properties.get("instruction") or None,
            confidence=float(node.properties.get("confidence", 0.8)),
            successes=int(node.properties.get("successes", 0)),
            failures=int(node.properties.get("failures", 0)),
            valid_at=datetime.fromisoformat(v_at) if v_at else None,
            invalid_at=datetime.fromisoformat(iv_at) if iv_at else None,
            created_at=datetime.fromisoformat(node.properties.get("created_at")),
            updated_at=datetime.fromisoformat(node.properties.get("updated_at")),
        )

    async def list_memories(self, project_id: str, query: str | None = None, limit: int = 50) -> list[Memory]:
        res = await self._read(GET_MEMORIES_BY_PROJECT_CYPHER, {"project_id": project_id, "limit": limit}, project_id=project_id)
        memories: list[Memory] = []
        for row in res.result_set:
            node = row[0]
            v_at = node.properties.get("valid_at")
            iv_at = node.properties.get("invalid_at")
            memories.append(
                Memory(
                    id=node.properties.get("id"),
                    project_id=node.properties.get("project_id"),
                    run_id=node.properties.get("run_id") or None,
                    agent_id=node.properties.get("agent_id") or None,
                    agent_role=node.properties.get("agent_role") or None,
                    content=node.properties.get("content"),
                    memory_type=node.properties.get("memory_type", "semantic"),
                    instruction=node.properties.get("instruction") or None,
                    confidence=float(node.properties.get("confidence", 0.8)),
                    successes=int(node.properties.get("successes", 0)),
                    failures=int(node.properties.get("failures", 0)),
                    valid_at=datetime.fromisoformat(v_at) if v_at else None,
                    invalid_at=datetime.fromisoformat(iv_at) if iv_at else None,
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
        if updates.instruction is not None:
            mem.instruction = updates.instruction
        if updates.confidence is not None:
            mem.confidence = updates.confidence
        if updates.valid_at is not None:
            mem.valid_at = updates.valid_at
        if updates.invalid_at is not None:
            mem.invalid_at = updates.invalid_at
        if updates.successes is not None:
            mem.successes = updates.successes
        if updates.failures is not None:
            mem.failures = updates.failures
        mem.updated_at = datetime.utcnow()
        await self.save_memory(mem)
        return mem

    async def delete_memory(self, memory_id: str) -> bool:
        proj_id = await self._resolve_project_id(memory_id)
        query = "MATCH (m:Memory {id: $id}) DETACH DELETE m"
        await self._run(query, {"id": memory_id}, project_id=proj_id)
        return True

    async def supersede_memory(self, old_memory_id: str, new_memory: Memory) -> Memory:
        proj_id = new_memory.project_id
        await self.save_memory(new_memory)
        params = {
            "old_id": old_memory_id,
            "new_id": new_memory.id,
        }
        await self._run(SUPERSEDE_MEMORY_CYPHER, params, project_id=proj_id)
        return new_memory

    async def get_procedural_memories(self, project_id: str, min_confidence: float = 0.55, limit: int = 5) -> list[Memory]:
        res = await self._read(
            GET_PROCEDURAL_RULES_CYPHER,
            {"project_id": project_id, "min_confidence": min_confidence, "limit": limit},
            project_id=project_id,
        )
        procs: list[Memory] = []
        for row in res.result_set:
            node = row[3] if len(row) > 3 else row[0]
            v_at = node.properties.get("valid_at")
            iv_at = node.properties.get("invalid_at")
            procs.append(
                Memory(
                    id=node.properties.get("id"),
                    project_id=node.properties.get("project_id"),
                    run_id=node.properties.get("run_id") or None,
                    content=node.properties.get("content"),
                    memory_type="procedural",
                    instruction=node.properties.get("instruction") or node.properties.get("content"),
                    confidence=float(node.properties.get("confidence", 0.6)),
                    successes=int(node.properties.get("successes", 0)),
                    failures=int(node.properties.get("failures", 0)),
                    valid_at=datetime.fromisoformat(v_at) if v_at else None,
                    invalid_at=datetime.fromisoformat(iv_at) if iv_at else None,
                    created_at=datetime.fromisoformat(node.properties.get("created_at")),
                    updated_at=datetime.fromisoformat(node.properties.get("updated_at")),
                )
            )
        return procs

    async def adjust_procedural_confidence(self, project_id: str, delta: float) -> list[Memory]:
        params = {
            "project_id": project_id,
            "delta": delta,
            "updated_at": datetime.utcnow().isoformat(),
        }
        res = await self._run(ADJUST_PROCEDURAL_CONFIDENCE_CYPHER, params, project_id=project_id)
        updated_list: list[Memory] = []
        for row in res.result_set:
            node = row[0]
            updated_list.append(
                Memory(
                    id=node.properties.get("id"),
                    project_id=node.properties.get("project_id"),
                    content=node.properties.get("content"),
                    memory_type="procedural",
                    instruction=node.properties.get("instruction") or node.properties.get("content"),
                    confidence=float(node.properties.get("confidence", 0.6)),
                    successes=int(node.properties.get("successes", 0)),
                    failures=int(node.properties.get("failures", 0)),
                    created_at=datetime.fromisoformat(node.properties.get("created_at")),
                    updated_at=datetime.fromisoformat(node.properties.get("updated_at")),
                )
            )
        return updated_list

    async def record_episode(self, run_id: str, memory_id: str, outcome: str) -> None:
        proj_id = await self._resolve_project_id(run_id)
        params = {
            "run_id": run_id,
            "memory_id": memory_id,
            "outcome": outcome,
            "recorded_at": datetime.utcnow().isoformat(),
        }
        await self._run(RECORD_EPISODE_CYPHER, params, project_id=proj_id)

    async def get_episodes(self, project_id: str, limit: int = 10) -> list[dict[str, Any]]:
        res = await self._read(GET_EPISODES_CYPHER, {"project_id": project_id, "limit": limit}, project_id=project_id)
        episodes: list[dict[str, Any]] = []
        for row in res.result_set:
            episodes.append({
                "run_id": row[0],
                "outcome": row[1],
                "memory_id": row[2],
                "content": row[3],
                "recorded_at": row[4],
            })
        return episodes

    # ─────────────────────────── Conversation Turns ────────────────────

    async def create_turn(self, turn: Turn) -> Turn:
        proj_id = await self._resolve_project_id(turn.run_id)
        self._entity_to_project[turn.id] = proj_id or ""
        params = {
            "run_id": turn.run_id,
            "turn_id": turn.id,
            "role": turn.role,
            "content": turn.content,
            "agent_id": getattr(turn, "agent_id", "") or "",
            "prev_turn_id": turn.prev_turn_id or "",
        }
        await self._run(CREATE_TURN_CYPHER, params, project_id=proj_id)
        for cid in turn.mentioned_claim_ids:
            await self.record_turn_mention(turn.id, cid)
        return turn

    async def list_turns(self, run_id: str) -> list[Turn]:
        proj_id = await self._resolve_project_id(run_id)
        res = await self._read(LIST_TURNS_CYPHER, {"run_id": run_id}, project_id=proj_id)
        turns: list[Turn] = []
        for row in res.result_set:
            node = row[0]
            prev_id = row[1] if len(row) > 1 and row[1] else None
            m_ids = [cid for cid in (row[2] if len(row) > 2 and row[2] else []) if cid]
            tid = node.properties.get("id")
            c_at = node.properties.get("created_at")
            t_stamp = node.properties.get("timestamp")
            created_dt = datetime.fromisoformat(c_at) if c_at else (datetime.fromtimestamp(t_stamp / 1000.0) if t_stamp else datetime.utcnow())
            t = Turn(
                id=tid,
                run_id=run_id,
                role=node.properties.get("role"),
                content=node.properties.get("content"),
                prev_turn_id=prev_id,
                mentioned_claim_ids=m_ids,
                created_at=created_dt,
            )
            turns.append(t)
        return turns

    async def get_conversation_history(self, run_id: str) -> list[Turn]:
        """Traverse (r:Run)-[:HAS_TURN]->(first:Turn)-[:NEXT_TURN*0..50]->(t:Turn) in order."""
        proj_id = await self._resolve_project_id(run_id)
        try:
            res = await self._read(GET_CONVERSATION_HISTORY_CYPHER, {"run_id": run_id}, project_id=proj_id)
            if res.result_set:
                turns: list[Turn] = []
                for row in res.result_set:
                    node = row[0]
                    m_ids = [cid for cid in (row[1] if len(row) > 1 and row[1] else []) if cid]
                    tid = node.properties.get("id")
                    c_at = node.properties.get("created_at")
                    t_stamp = node.properties.get("timestamp")
                    created_dt = datetime.fromisoformat(c_at) if c_at else (datetime.fromtimestamp(t_stamp / 1000.0) if t_stamp else datetime.utcnow())
                    turns.append(
                        Turn(
                            id=tid,
                            run_id=run_id,
                            role=node.properties.get("role"),
                            content=node.properties.get("content"),
                            mentioned_claim_ids=m_ids,
                            created_at=created_dt,
                        )
                    )
                return turns
        except Exception as e:
            logger.debug(f"get_conversation_history graph traversal note: {e}")

        # Fallback to standard turn list
        return await self.list_turns(run_id)

    async def record_turn_mention(self, turn_id: str, claim_id: str) -> None:
        proj_id = await self._resolve_project_id(turn_id)
        await self._run(LINK_TURN_MENTION_CYPHER, {"turn_id": turn_id, "claim_id": claim_id}, project_id=proj_id)

    # ─────────────────────────── Claims ──────────────────────────────

    async def save_claim(self, claim: Claim) -> Claim:
        cypher = """
        MATCH (p:Project {id: $project_id})
        MERGE (c:Claim {id: $id})
        ON CREATE SET c.project_id = $project_id, c.run_id = $run_id, c.agent_id = $agent_id,
                      c.agent_role = $agent_role, c.text = $text, c.confidence = $confidence,
                      c.status = $status, c.created_at = $created_at
        ON MATCH SET c.text = $text, c.confidence = $confidence, c.status = $status
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
        self._entity_to_project[claim.id] = claim.project_id
        await self._run(cypher, params, project_id=claim.project_id)
        for s_id in claim.supporting_source_ids:
            await self.record_relationship(s_id, claim.id, "SUPPORTS", project_id=claim.project_id)
        for c_id in claim.contradicting_claim_ids:
            await self.record_relationship(claim.id, c_id, "CONTRADICTS", project_id=claim.project_id)
        return claim

    async def get_claim(self, claim_id: str) -> Claim | None:
        proj_id = await self._resolve_project_id(claim_id, "MATCH (c:Claim {id: $id}) RETURN c.project_id AS pid")
        query = """
        MATCH (c:Claim {id: $id})
        OPTIONAL MATCH (s:Source)-[:SUPPORTS|CITES]-(c)
        OPTIONAL MATCH (c)-[:CONTRADICTS]-(other:Claim)
        RETURN c, collect(DISTINCT s.id) AS source_ids, collect(DISTINCT other.id) AS contra_ids
        """
        res = await self._read(query, {"id": claim_id}, project_id=proj_id)
        if not res.result_set:
            return None
        node, source_ids, contra_ids = res.result_set[0]
        return Claim(
            id=node.properties.get("id"),
            project_id=node.properties.get("project_id"),
            run_id=node.properties.get("run_id") or None,
            agent_id=node.properties.get("agent_id") or None,
            agent_role=node.properties.get("agent_role") or None,
            text=node.properties.get("text"),
            confidence=float(node.properties.get("confidence", 0.7)),
            status=node.properties.get("status", "proposed"),
            supporting_source_ids=[sid for sid in source_ids if sid],
            contradicting_claim_ids=[cid for cid in contra_ids if cid],
            created_at=datetime.fromisoformat(node.properties.get("created_at")),
        )

    async def list_claims(self, project_id: str, run_id: str | None = None) -> list[Claim]:
        query = """
        MATCH (c:Claim {project_id: $project_id})
        OPTIONAL MATCH (s:Source)-[:SUPPORTS|CITES]-(c)
        OPTIONAL MATCH (c)-[:CONTRADICTS]-(other:Claim)
        RETURN c, collect(DISTINCT s.id) AS source_ids, collect(DISTINCT other.id) AS contra_ids
        """
        res = await self._read(query, {"project_id": project_id}, project_id=project_id)
        claims: list[Claim] = []
        for row in res.result_set:
            node, source_ids, contra_ids = row
            cid = node.properties.get("id")
            self._entity_to_project[cid] = project_id
            claims.append(
                Claim(
                    id=cid,
                    project_id=node.properties.get("project_id"),
                    run_id=node.properties.get("run_id") or None,
                    agent_id=node.properties.get("agent_id") or None,
                    agent_role=node.properties.get("agent_role") or None,
                    text=node.properties.get("text"),
                    confidence=float(node.properties.get("confidence", 0.7)),
                    status=node.properties.get("status", "proposed"),
                    supporting_source_ids=[sid for sid in source_ids if sid],
                    contradicting_claim_ids=[cid for cid in contra_ids if cid],
                    created_at=datetime.fromisoformat(node.properties.get("created_at")),
                )
            )
        if run_id:
            claims = [c for c in claims if c.run_id == run_id]
        return claims

    async def record_contradiction(self, claim_a_id: str, claim_b_id: str, notes: str = "") -> None:
        proj_id = await self._resolve_project_id(claim_a_id)
        cypher = """
        MATCH (a:Claim {id: $claim_a_id}), (b:Claim {id: $claim_b_id})
        MERGE (a)-[r:CONTRADICTS]->(b)
        SET r.notes = $notes, r.detected_at = $detected_at, a.status = 'contradicted', b.status = 'contradicted'
        RETURN r
        """
        await self._run(
            cypher,
            {
                "claim_a_id": claim_a_id,
                "claim_b_id": claim_b_id,
                "notes": notes,
                "detected_at": datetime.utcnow().isoformat(),
            },
            project_id=proj_id,
        )

    async def save_source(self, source: Source) -> Source:
        cypher = """
        MERGE (s:Source {id: $id})
        ON CREATE SET s.title = $title, s.uri = $uri, s.source_type = $source_type
        RETURN s
        """
        proj_id = await self._resolve_project_id(source.id)
        await self._run(
            cypher,
            {"id": source.id, "title": source.title, "uri": source.uri, "source_type": source.source_type},
            project_id=proj_id,
        )
        return source

    # ─────────────────────────── Relationships ────────────────────────

    async def record_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
        project_id: str | None = None,
    ) -> None:
        proj_id = project_id or await self._resolve_project_id(source_id) or await self._resolve_project_id(target_id)
        safe_rel = "".join(c for c in rel_type.upper() if c.isalnum() or c == "_")
        cypher = MERGE_RELATIONSHIP_CYPHER % safe_rel
        await self._run(cypher, {"source_id": source_id, "target_id": target_id}, project_id=proj_id)

    def _extract_from_path(
        self,
        path: Any,
        nodes_dict: dict[str, GraphNode],
        edges_dict: dict[str, GraphEdge],
        node_types: list[str] | None = None,
    ) -> None:
        if not path:
            return
        path_nodes = path.nodes() if callable(getattr(path, "nodes", None)) else getattr(path, "nodes", [])
        path_edges = path.edges() if callable(getattr(path, "edges", None)) else getattr(path, "edges", [])

        internal_to_eid: dict[int, str] = {}
        for n in path_nodes:
            eid = n.properties.get("id")
            if not eid:
                continue
            internal_to_eid[n.id] = eid
            label = n.labels[0] if (hasattr(n, "labels") and n.labels) else "Entity"
            if node_types and label not in node_types:
                continue
            if eid not in nodes_dict:
                nodes_dict[eid] = GraphNode(
                    id=eid,
                    label=label,
                    title=n.properties.get("name") or n.properties.get("title") or n.properties.get("text", "")[:35],
                    properties=dict(n.properties),
                )

        for r in path_edges:
            src_eid = internal_to_eid.get(r.src_node) or str(r.src_node)
            dst_eid = internal_to_eid.get(r.dest_node) or str(r.dest_node)
            edge_id = f"edge-{src_eid}-{r.relation}-{dst_eid}"
            if edge_id not in edges_dict:
                edges_dict[edge_id] = GraphEdge(
                    id=edge_id,
                    source=src_eid,
                    target=dst_eid,
                    relationship=r.relation,
                    properties=dict(getattr(r, "properties", {})),
                )

    # ─────────────────────────── Native Graph Algorithms ──────────────

    async def get_claim_authority(self, project_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Rank claims by centrality using native FalkorDB PageRank (algo.pageRank)."""
        try:
            res = await self._read(PAGERANK_CLAIMS_CYPHER, {"limit": limit}, project_id=project_id)
            results = []
            for row in res.result_set:
                results.append({
                    "claim_id": row[0],
                    "text": row[1],
                    "claim": row[1],
                    "score": round(float(row[2]), 4),
                })
            if results:
                return results
        except Exception as e:
            logger.warning(f"algo.pageRank failed on graph '{project_id}': {e}. Falling back to in-degree centrality.")

        claims = await self.list_claims(project_id)
        return [{"claim_id": c.id, "text": c.text, "claim": c.text, "score": c.confidence} for c in claims[:limit]]

    # Backward-compatible alias
    rank_evidence_authority = get_claim_authority

    async def trace_evidence_path(self, project_id: str, start_id: str, end_id: str) -> list[str]:
        """Explainable shortest path between two nodes using native FalkorDB SPpaths (algo.SPpaths)."""
        try:
            res = await self._read(
                SHORTEST_PATH_ALGO_CYPHER,
                {"start_id": start_id, "end_id": end_id},
                project_id=project_id,
            )
            if res.result_set and res.result_set[0] and res.result_set[0][0]:
                return [str(item) for item in res.result_set[0][0]]
        except Exception as e:
            logger.warning(f"algo.SPpaths failed: {e}. Falling back to standard Cypher shortestPath.")

        path_data = await self.find_shortest_path(project_id, start_id, end_id)
        return [n.title for n in path_data.nodes] if path_data.nodes else [start_id, end_id]

    # Backward-compatible alias
    async def trace_shortest_path_algo(self, project_id: str, claim_a_id: str, claim_b_id: str) -> list[str]:
        return await self.trace_evidence_path(project_id, claim_a_id, claim_b_id)

    # ─────────────────────────── Graph Queries ────────────────────────

    async def get_project_graph(
        self,
        project_id: str,
        node_types: list[str] | None = None,
        limit: int = 150,
    ) -> GraphData:
        res = await self._read(GET_PROJECT_GRAPH_CYPHER, {"project_id": project_id, "limit": limit}, project_id=project_id)
        nodes_dict: dict[str, GraphNode] = {}
        edges_dict: dict[str, GraphEdge] = {}

        for row in res.result_set:
            path = row[0]
            self._extract_from_path(path, nodes_dict, edges_dict, node_types)

        if project_id not in nodes_dict:
            proj = await self.get_project(project_id)
            if proj:
                nodes_dict[project_id] = GraphNode(
                    id=proj.id,
                    label="Project",
                    title=proj.name,
                    properties={"name": proj.name, "description": proj.description},
                )

        return GraphData(nodes=list(nodes_dict.values()), edges=list(edges_dict.values()))

    async def traverse_graph(self, project_id: str, node_id: str, depth: int = 2) -> GraphData:
        return await self.trace_provenance(project_id, node_id, max_depth=depth)

    # ─────────── Multi-Hop Explainability & Path Tracing ──────────────

    async def trace_provenance(self, project_id: str, node_id: str, max_depth: int = 4) -> GraphData:
        """Multi-hop provenance traversal up to max_depth hops from node_id."""
        res = await self._read(MULTI_HOP_PROVENANCE_CYPHER, {"node_id": node_id, "limit": 80}, project_id=project_id)
        nodes_dict: dict[str, GraphNode] = {}
        edges_dict: dict[str, GraphEdge] = {}

        for row in res.result_set:
            path = row[0]
            self._extract_from_path(path, nodes_dict, edges_dict)

        if node_id not in nodes_dict:
            start_res = await self._read("MATCH (n {id: $id}) RETURN n", {"id": node_id}, project_id=project_id)
            if start_res.result_set:
                n = start_res.result_set[0][0]
                lbl = n.labels[0] if (hasattr(n, "labels") and n.labels) else "Entity"
                nodes_dict[node_id] = GraphNode(
                    id=node_id,
                    label=lbl,
                    title=n.properties.get("name") or n.properties.get("title") or n.properties.get("text", "")[:35],
                    properties=dict(n.properties),
                )

        return GraphData(nodes=list(nodes_dict.values()), edges=list(edges_dict.values()))

    async def find_shortest_path(self, project_id: str, start_id: str, end_id: str) -> GraphData:
        """Shortest path between two nodes using Cypher shortestPath."""
        res = await self._read(SHORTEST_PATH_CYPHER, {"start_id": start_id, "end_id": end_id}, project_id=project_id)
        nodes_dict: dict[str, GraphNode] = {}
        edges_dict: dict[str, GraphEdge] = {}

        for row in res.result_set:
            path = row[0]
            self._extract_from_path(path, nodes_dict, edges_dict)

        return GraphData(nodes=list(nodes_dict.values()), edges=list(edges_dict.values()))

    async def find_contradictions(self, project_id: str) -> list[dict[str, Any]]:
        res = await self._read(FIND_CONTRADICTIONS_CYPHER, {"project_id": project_id}, project_id=project_id)
        results: list[dict[str, Any]] = []
        for row in res.result_set:
            results.append({
                "claim_a_id": row[0],
                "claim_a_text": row[1],
                "claim_b_id": row[2],
                "claim_b_text": row[3],
                "notes": row[4] or "",
            })
        return results

    async def get_disputes_with_evidence(self, project_id: str) -> list[dict[str, Any]]:
        """Retrieve contradicting claim pairs with their supporting sources."""
        res = await self._read(DISPUTES_WITH_EVIDENCE_CYPHER, {"project_id": project_id}, project_id=project_id)
        results: list[dict[str, Any]] = []
        for row in res.result_set:
            results.append({
                "claim_a_id": row[0] or "",
                "claim_a_text": row[1] or "",
                "claim_b_id": row[4] or "",
                "claim_b_text": row[5] or "",
                "claim_a_sources": [{"title": row[2] or "", "uri": row[3] or ""}] if row[2] else [],
                "claim_b_sources": [{"title": row[6] or "", "uri": row[7] or ""}] if row[6] else [],
                "dispute_reason": row[8] or "Evidence conflict detected",
                "recommendation": row[9] or "Preserve dispute in graph memory",
            })
        return results
