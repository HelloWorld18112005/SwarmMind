CREATE_PROJECT_CYPHER = """
MERGE (p:Project {id: $id})
ON CREATE SET p.name = $name, p.description = $description, p.created_at = $created_at, p.updated_at = $updated_at
ON MATCH SET p.name = $name, p.description = $description, p.updated_at = $updated_at
RETURN p
"""

GET_PROJECT_CYPHER = """
MATCH (p:Project {id: $id})
RETURN p
"""

LIST_PROJECTS_CYPHER = """
MATCH (p:Project)
RETURN p ORDER BY p.created_at DESC
"""

DELETE_PROJECT_CYPHER = """
MATCH (p:Project {id: $id})
OPTIONAL MATCH (p)-[r*0..3]-(related)
DETACH DELETE p, related
"""

CREATE_RUN_CYPHER = """
MATCH (p:Project {id: $project_id})
MERGE (r:Run {id: $id})
ON CREATE SET r.project_id = $project_id, r.goal = $goal, r.status = $status, r.started_at = $started_at
MERGE (p)-[:HAS_RUN]->(r)
RETURN r
"""

GET_RUN_CYPHER = """
MATCH (r:Run {id: $id})
RETURN r
"""

LIST_RUNS_CYPHER = """
MATCH (p:Project {id: $project_id})-[:HAS_RUN]->(r:Run)
RETURN r ORDER BY r.started_at DESC
"""

UPDATE_RUN_STATUS_CYPHER = """
MATCH (r:Run {id: $id})
SET r.status = $status, r.completed_at = $completed_at
RETURN r
"""

CREATE_TASK_CYPHER = """
MATCH (r:Run {id: $run_id})
MERGE (t:Task {id: $id})
ON CREATE SET t.run_id = $run_id, t.title = $title, t.description = $description,
              t.assigned_role = $assigned_role, t.status = $status, t.priority = $priority,
              t.created_at = $created_at
MERGE (r)-[:HAS_TASK]->(t)
RETURN t
"""

CREATE_MEMORY_CYPHER = """
MATCH (p:Project {id: $project_id})
MERGE (m:Memory {id: $id})
ON CREATE SET m.project_id = $project_id, m.run_id = $run_id, m.agent_id = $agent_id,
              m.agent_role = $agent_role, m.content = $content, m.memory_type = $memory_type,
              m.confidence = $confidence, m.created_at = $created_at, m.updated_at = $updated_at
MERGE (p)-[:ABOUT]->(m)
RETURN m
"""

GET_MEMORIES_BY_PROJECT_CYPHER = """
MATCH (m:Memory {project_id: $project_id})
RETURN m ORDER BY m.created_at DESC LIMIT $limit
"""

MERGE_RELATIONSHIP_CYPHER = """
MATCH (a {id: $source_id}), (b {id: $target_id})
MERGE (a)-[r:%s]->(b)
RETURN r
"""

GET_PROJECT_GRAPH_CYPHER = """
MATCH (n {project_id: $project_id})-[r]-(m {project_id: $project_id})
RETURN n, r, m LIMIT $limit
"""

TRAVERSE_FROM_NODE_CYPHER = """
MATCH path = (start {id: $node_id})-[*1..2]-(connected)
RETURN path LIMIT 50
"""

FIND_CONTRADICTIONS_CYPHER = """
MATCH (c1:Claim {project_id: $project_id})-[r:CONTRADICTS]-(c2:Claim {project_id: $project_id})
RETURN c1.id AS claim_a_id, c1.text AS claim_a_text,
       c2.id AS claim_b_id, c2.text AS claim_b_text,
       r.notes AS notes
"""

MULTI_HOP_PROVENANCE_CYPHER = """
MATCH path = (start {id: $node_id})-[*1..4]-(connected)
WHERE any(lbl IN labels(connected) WHERE lbl IN ['Claim', 'Source', 'Memory', 'Task', 'Agent'])
RETURN path LIMIT $limit
"""

SHORTEST_PATH_CYPHER = """
MATCH (start {id: $start_id}), (endNode {id: $end_id})
MATCH path = shortestPath((start)-[*..8]-(endNode))
RETURN path
"""

DISPUTES_WITH_EVIDENCE_CYPHER = """
MATCH (c1:Claim {project_id: $project_id})-[r:CONTRADICTS]-(c2:Claim {project_id: $project_id})
OPTIONAL MATCH (c1)-[:SUPPORTED_BY|CITES]->(s1:Source)
OPTIONAL MATCH (c2)-[:SUPPORTED_BY|CITES]->(s2:Source)
RETURN c1.id AS claim_a_id, c1.text AS claim_a_text, s1.title AS source_a_title, s1.uri AS source_a_uri,
       c2.id AS claim_b_id, c2.text AS claim_b_text, s2.title AS source_b_title, s2.uri AS source_b_uri,
       r.notes AS dispute_reason, r.recommendation AS recommendation
"""
