export type AgentRole =
  | 'coordinator'
  | 'researcher'
  | 'analyst'
  | 'critic'
  | 'planner'
  | 'synthesizer';

export type AgentStatus = 'idle' | 'thinking' | 'executing' | 'waiting' | 'completed' | 'error';

export type TaskStatus = 'pending' | 'ready' | 'running' | 'completed' | 'failed' | 'cancelled';

export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';

export type RunStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';

export interface Project {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

export interface Run {
  id: string;
  project_id: string;
  goal: string;
  status: RunStatus;
  started_at: string;
  completed_at?: string;
  task_count: number;
  completed_task_count: number;
  findings_count: number;
  conflicts_count: number;
}

export interface Task {
  id: string;
  run_id: string;
  title: string;
  description: string;
  assigned_role: AgentRole;
  assigned_agent_id?: string;
  status: TaskStatus;
  priority: TaskPriority;
  dependencies: string[];
  result?: Record<string, unknown>;
  error?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface Agent {
  id: string;
  role: AgentRole;
  name: string;
  status: AgentStatus;
  current_task_id?: string;
  step_count: number;
}

export interface Memory {
  id: string;
  project_id: string;
  run_id?: string;
  agent_id?: string;
  agent_role?: string;
  task_id?: string;
  content: string;
  memory_type: 'fact' | 'observation' | 'rule' | 'hypothesis' | 'summary';
  confidence: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface Claim {
  id: string;
  project_id: string;
  run_id?: string;
  agent_id?: string;
  agent_role?: string;
  text: string;
  confidence: number;
  status: 'proposed' | 'supported' | 'challenged' | 'contradicted' | 'verified';
  supporting_source_ids: string[];
  contradicting_claim_ids: string[];
  created_at: string;
}

export interface GraphNode {
  id: string;
  label: string;
  title: string;
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
  properties: Record<string, unknown>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Recommendation {
  title: string;
  description: string;
  priority: string;
  supporting_claim_ids: string[];
  risks: string[];
}

export interface ConflictItem {
  claim_a_id: string;
  claim_a_text: string;
  claim_b_id: string;
  claim_b_text: string;
  status?: string;
  notes?: string;
  dispute_reason?: string;
  recommendation?: string;
  claim_a_sources?: Array<{ title: string; uri: string }>;
  claim_b_sources?: Array<{ title: string; uri: string }>;
}

export interface Report {
  id: string;
  project_id: string;
  run_id: string;
  title: string;
  executive_summary: string;
  findings: string[];
  recommendations: Recommendation[];
  unresolved_conflicts: ConflictItem[];
  sources: Record<string, unknown>[];
  confidence_assessment: string;
  created_at: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  version: string;
  environment: string;
  graph_backend: 'local' | 'falkordb';
  database: {
    status: string;
    backend: string;
    initialized: boolean;
    project_count?: number;
    node_count?: number;
    edge_count?: number;
    host?: string;
    error?: string;
  };
}

export interface ExplainabilityStep {
  step_number: number;
  agent_role: string;
  action: string;
  finding: string;
  confidence: number;
  source_citation?: string;
}

export interface ExplanationResponse {
  target_id: string;
  target_title: string;
  confidence_assessment: string;
  narrative_explanation: string;
  steps: ExplainabilityStep[];
  sources: Array<{ id: string; title: string; uri: string }>;
  contradictions: ConflictItem[];
  subgraph: GraphData;
}
