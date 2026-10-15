from enum import Enum


class NodeLabel(str, Enum):
    USER = "User"
    PROJECT = "Project"
    RUN = "Run"
    AGENT = "Agent"
    TASK = "Task"
    MEMORY = "Memory"
    CLAIM = "Claim"
    SOURCE = "Source"
    DECISION = "Decision"
    ARTIFACT = "Artifact"


class RelationshipType(str, Enum):
    OWNS = "OWNS"
    HAS_RUN = "HAS_RUN"
    INCLUDES_AGENT = "INCLUDES_AGENT"
    HAS_TASK = "HAS_TASK"
    ASSIGNED_TO = "ASSIGNED_TO"
    DEPENDS_ON = "DEPENDS_ON"
    PRODUCED = "PRODUCED"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    DERIVED_FROM = "DERIVED_FROM"
    ABOUT = "ABOUT"
    SHARES_WITH = "SHARES_WITH"
    INFORMED_BY = "INFORMED_BY"
    CREATED = "CREATED"


INDEX_STATEMENTS = [
    "CREATE INDEX FOR (p:Project) ON (p.id)",
    "CREATE INDEX FOR (r:Run) ON (r.id)",
    "CREATE INDEX FOR (t:Task) ON (t.id)",
    "CREATE INDEX FOR (m:Memory) ON (m.id)",
    "CREATE INDEX FOR (m:Memory) ON (m.project_id)",
    "CREATE INDEX FOR (c:Claim) ON (c.id)",
    "CREATE INDEX FOR (c:Claim) ON (c.project_id)",
    "CREATE INDEX FOR (s:Source) ON (s.id)",
]
