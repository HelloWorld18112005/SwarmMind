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
OPTIONAL MATCH (p)-[:HAS_RUN]->(r:Run)
OPTIONAL MATCH (r)-[:HAS_TASK]->(t:Task)
OPTIONAL MATCH (p)-[:ABOUT]->(item)
DETACH DELETE p, r, t, item
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

RECORD_TASK_HANDOFF_CYPHER = """
MATCH (t1:Task {id: $from_task}), (t2:Task {id: $to_task})
MERGE (t1)-[r:HANDED_OFF_TO {at: timestamp(), context: $context}]->(t2)
SET r.from_agent = $from_agent, r.to_agent = $to_agent, r.timestamp = $timestamp
RETURN r
"""

CREATE_MEMORY_CYPHER = """
MATCH (p:Project {id: $project_id})
MERGE (m:Memory {id: $id})
ON CREATE SET m.project_id = $project_id, m.run_id = $run_id, m.agent_id = $agent_id,
              m.agent_role = $agent_role, m.content = $content, m.memory_type = $memory_type,
              m.confidence = $confidence, m.instruction = $instruction,
              m.successes = $successes, m.failures = $failures,
              m.valid_at = $valid_at, m.invalid_at = $invalid_at,
              m.created_at = $created_at, m.updated_at = $updated_at
ON MATCH SET m.content = $content, m.memory_type = $memory_type,
             m.confidence = $confidence, m.instruction = $instruction,
             m.successes = $successes, m.failures = $failures,
             m.valid_at = $valid_at, m.invalid_at = $invalid_at,
             m.updated_at = $updated_at
MERGE (p)-[:ABOUT]->(m)
RETURN m
"""

GET_MEMORIES_BY_PROJECT_CYPHER = """
MATCH (m:Memory {project_id: $project_id})
WHERE m.invalid_at IS NULL OR m.invalid_at = ''
RETURN m ORDER BY m.created_at DESC LIMIT $limit
"""

SUPERSEDE_MEMORY_CYPHER = """
MATCH (old_m:Memory {id: $old_id}), (new_m:Memory {id: $new_id})
SET old_m.invalid_at = timestamp()
MERGE (new_m)-[r:SUPERSEDES]->(old_m)
RETURN r
"""

GET_PROCEDURAL_RULES_CYPHER = """
MATCH (m:Memory {memory_type: 'procedural'})
WHERE m.confidence >= $min_confidence AND (m.invalid_at IS NULL OR m.invalid_at = '')
  AND ($project_id IS NULL OR $project_id = '' OR m.project_id = $project_id)
RETURN m.id AS id, m.instruction AS instruction, m.confidence AS confidence, m
ORDER BY m.confidence DESC LIMIT $limit
"""

ADJUST_PROCEDURAL_CONFIDENCE_CYPHER = """
MATCH (m:Memory {memory_type: 'procedural'})
WHERE ($project_id IS NULL OR $project_id = '' OR m.project_id = $project_id)
SET m.confidence = CASE
    WHEN m.confidence + $delta > 1.0 THEN 1.0
    WHEN m.confidence + $delta < 0.0 THEN 0.0
    ELSE m.confidence + $delta
END,
m.successes = CASE WHEN $delta > 0 THEN coalesce(m.successes, 0) + 1 ELSE coalesce(m.successes, 0) END,
m.failures = CASE WHEN $delta < 0 THEN coalesce(m.failures, 0) + 1 ELSE coalesce(m.failures, 0) END,
m.updated_at = $updated_at
RETURN m
"""

RECORD_EPISODE_CYPHER = """
MATCH (r:Run {id: $run_id}), (m:Memory {id: $memory_id})
MERGE (r)-[e:RECORDED_EPISODE {outcome: $outcome, at: timestamp()}]->(m)
SET e.recorded_at = $recorded_at
RETURN e
"""

GET_EPISODES_CYPHER = """
MATCH (r:Run)-[e:RECORDED_EPISODE]->(m:Memory)
WHERE ($project_id IS NULL OR $project_id = '' OR r.project_id = $project_id)
RETURN r.id AS run_id, e.outcome AS outcome, m.id AS memory_id, m.content AS content, coalesce(e.at, e.recorded_at) AS recorded_at
ORDER BY coalesce(e.at, e.recorded_at) DESC LIMIT $limit
"""

CREATE_TURN_CYPHER = """
MATCH (r:Run {id: $run_id})
CREATE (t:Turn {
  id: $turn_id,
  role: $role,
  content: $content,
  timestamp: timestamp(),
  agent_id: $agent_id
})
MERGE (r)-[:HAS_TURN]->(t)
WITH t
OPTIONAL MATCH (prev:Turn {id: $prev_turn_id})
FOREACH (_ IN CASE WHEN prev IS NOT NULL THEN [1] ELSE [] END |
  MERGE (prev)-[:NEXT_TURN]->(t)
)
RETURN t
"""

LINK_TURN_MENTION_CYPHER = """
MATCH (t:Turn {id: $turn_id}), (c:Claim {id: $claim_id})
MERGE (t)-[r:MENTIONS]->(c)
RETURN r
"""

GET_CONVERSATION_HISTORY_CYPHER = """
MATCH (r:Run {id: $run_id})-[:HAS_TURN]->(first:Turn)
WHERE NOT ()-[:NEXT_TURN]->(first)
MATCH path = (first)-[:NEXT_TURN*0..50]->(t:Turn)
OPTIONAL MATCH (t)-[:MENTIONS]->(c:Claim)
RETURN t, collect(DISTINCT c.id) AS mentioned_claim_ids
ORDER BY length(path) ASC
"""

LIST_TURNS_CYPHER = """
MATCH (r:Run {id: $run_id})-[:HAS_TURN]->(t:Turn)
OPTIONAL MATCH (prev:Turn)-[:NEXT_TURN]->(t)
OPTIONAL MATCH (t)-[:MENTIONS]->(c:Claim)
RETURN t, prev.id AS prev_id, collect(DISTINCT c.id) AS mentioned_claim_ids
ORDER BY coalesce(t.timestamp, t.created_at) ASC
"""

PAGERANK_CLAIMS_CYPHER = """
CALL algo.pageRank('Claim', 'SUPPORTS') YIELD node, score
RETURN node.id AS claim_id, node.text AS text, score
ORDER BY score DESC LIMIT $limit
"""

SHORTEST_PATH_ALGO_CYPHER = """
MATCH (src {id: $start_id}), (dst {id: $end_id})
CALL algo.SPpaths({
  sourceNode: src,
  targetNode: dst,
  relTypes: ['SUPPORTS', 'CONTRADICTS', 'DERIVED_FROM', 'INFORMED_BY'],
  relDirection: 'both',
  pathCount: 1
}) YIELD path
RETURN [n IN nodes(path) | coalesce(n.title, n.text, n.summary, n.id)] AS explainable_path
"""

MERGE_RELATIONSHIP_CYPHER = """
MATCH (a {id: $source_id}), (b {id: $target_id})
MERGE (a)-[r:%s]->(b)
RETURN r
"""

GET_PROJECT_GRAPH_CYPHER = """
MATCH path = (p:Project {id: $project_id})-[*1..3]-(connected)
RETURN path LIMIT $limit
"""

TRAVERSE_FROM_NODE_CYPHER = """
MATCH path = (start {id: $node_id})-[*1..2]-(connected)
RETURN path LIMIT 50
"""

FIND_CONTRADICTIONS_CYPHER = """
MATCH (c1:Claim {project_id: $project_id})-[r:CONTRADICTS]->(c2:Claim {project_id: $project_id})
RETURN c1.id AS claim_a_id, c1.text AS claim_a_text,
       c2.id AS claim_b_id, c2.text AS claim_b_text,
       r.notes AS notes
"""

MULTI_HOP_PROVENANCE_CYPHER = """
MATCH path = (start {id: $node_id})-[*1..4]-(connected)
WHERE any(lbl IN labels(connected) WHERE lbl IN ['Claim', 'Source', 'Memory', 'Task', 'Agent', 'Project', 'Turn'])
RETURN path LIMIT $limit
"""

SHORTEST_PATH_CYPHER = """
MATCH (start {id: $start_id}), (endNode {id: $end_id})
MATCH path = shortestPath((start)-[*..8]-(endNode))
RETURN path
"""

DISPUTES_WITH_EVIDENCE_CYPHER = """
MATCH (c1:Claim {project_id: $project_id})-[r:CONTRADICTS]->(c2:Claim {project_id: $project_id})
OPTIONAL MATCH (s1:Source)-[:SUPPORTS|CITES]-(c1)
OPTIONAL MATCH (s2:Source)-[:SUPPORTS|CITES]-(c2)
RETURN c1.id AS claim_a_id, c1.text AS claim_a_text, s1.title AS source_a_title, s1.uri AS source_a_uri,
       c2.id AS claim_b_id, c2.text AS claim_b_text, s2.title AS source_b_title, s2.uri AS source_b_uri,
       r.notes AS dispute_reason, r.recommendation AS recommendation
"""
