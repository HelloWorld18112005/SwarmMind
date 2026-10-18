import json
from pathlib import Path
from datetime import datetime
from typing import Any
from app.graph.base import GraphRepository
from app.schemas.project import Project
from app.schemas.run import Run
from app.schemas.agent import Agent
from app.schemas.task import Task
from app.schemas.claim import Claim, Source
from app.schemas.memory import Memory
from app.schemas.chat import Turn


async def seed_demo_project(repo: GraphRepository) -> dict[str, str]:
    """Seed the VentureAudit M&A Technical & IP Due Diligence project into the active graph repository.

    Scenario: Autonomous M&A Technical & IP Due Diligence on 'ApexAI' ($45M Deal Escrow).
    Contains: Project, Run, 6 Agents, 6 Tasks with dependencies & handoffs, 4 Sources,
              4 Claims, explicit CONTRADICTS disputes, and 3-Tier Cognitive Memories
              (Semantic, Episodic, Procedural).
    """
    proj_id = "proj-apexai-audit"
    run_id = "run-apexai-audit-eval"

    # 1. Project
    project = Project(
        id=proj_id,
        name="ApexAI Acquisition Technical & Legal Audit ($45M Deal Escrow)",
        description="Autonomous M&A technical, legal, and IP due diligence on ApexAI. Audit proprietary IP against open-source copyleft licenses, verify cloud infrastructure resilience, check undisclosed litigation, and establish escrow withholding risk matrix.",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await repo.create_project(project)

    # 2. Run
    run = Run(
        id=run_id,
        project_id=proj_id,
        goal="Conduct full acquisition due diligence on ApexAI. Audit proprietary IP claims against open-source licenses, verify infrastructure resilience, check regulatory disclosures, and produce an escrow risk matrix.",
        status="completed",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        task_count=6,
        completed_task_count=6,
        findings_count=4,
        conflicts_count=2,
    )
    await repo.create_run(run)

    # 3. Agents
    agents_spec = [
        ("agent-ma-coord", "coordinator", "M&A Lead Partner"),
        ("agent-ma-research", "researcher", "IP & Forensics Auditor"),
        ("agent-ma-analyst", "analyst", "Systems & Valuation Analyst"),
        ("agent-ma-critic", "critic", "Contradiction & Escrow Critic"),
        ("agent-ma-planner", "planner", "Deal Structuring Strategist"),
        ("agent-ma-synth", "synthesizer", "Due Diligence Synthesizer"),
    ]
    for a_id, role, name in agents_spec:
        agent = Agent(id=a_id, role=role, name=name, status="completed")
        await repo.record_relationship(run_id, a_id, "INCLUDES_AGENT")

    # 4. Tasks with dependencies
    tasks = [
        Task(
            id="task-1-coord",
            run_id=run_id,
            title="Decompose M&A Audit Scope & Assign Due Diligence Roles",
            description="Establish research boundaries, metrics, and assign specialized agent roles for ApexAI acquisition review.",
            assigned_role="coordinator",
            assigned_agent_id="agent-ma-coord",
            status="completed",
            priority="critical",
            dependencies=[],
        ),
        Task(
            id="task-2-ip-audit",
            run_id=run_id,
            title="Audit Founder Representations vs Engineering Git SBOM",
            description="Extract founder IP claims from pitch deck and compare against SBOM for GPL/copyleft contamination.",
            assigned_role="researcher",
            assigned_agent_id="agent-ma-research",
            status="completed",
            priority="critical",
            dependencies=["task-1-coord"],
        ),
        Task(
            id="task-3-infra-check",
            run_id=run_id,
            title="Inspect Cloud Infrastructure Resilience & Single-Region Risks",
            description="Audit AWS Terraform configs and CloudWatch telemetry to verify 99.99% multi-region uptime claim.",
            assigned_role="analyst",
            assigned_agent_id="agent-ma-analyst",
            status="completed",
            priority="high",
            dependencies=["task-1-coord"],
        ),
        Task(
            id="task-4-critic",
            run_id=run_id,
            title="Cross-Examine Founder Claims vs Legal Injunctions & Code BOM",
            description="Detect contradictions between founder claims and reality: GPL copyleft contamination & Delaware injunction.",
            assigned_role="critic",
            assigned_agent_id="agent-ma-critic",
            status="completed",
            priority="critical",
            dependencies=["task-2-ip-audit", "task-3-infra-check"],
        ),
        Task(
            id="task-5-escrow-matrix",
            run_id=run_id,
            title="Formulate $45M Deal Escrow Risk Matrix & Withholding Terms",
            description="Determine escrow holdback percentage and license remediation covenants before deal execution.",
            assigned_role="planner",
            assigned_agent_id="agent-ma-planner",
            status="completed",
            priority="high",
            dependencies=["task-4-critic"],
        ),
        Task(
            id="task-6-synth",
            run_id=run_id,
            title="Synthesize Final Acquisition Due Diligence Report & Provenance",
            description="Compile final audit findings, dispute provenance trails, and executive escrow recommendation.",
            assigned_role="synthesizer",
            assigned_agent_id="agent-ma-synth",
            status="completed",
            priority="critical",
            dependencies=["task-5-escrow-matrix"],
        ),
    ]

    for t in tasks:
        await repo.create_task(t)

    # Record Task Handoffs
    await repo.record_task_handoff("task-1-coord", "task-2-ip-audit", "coordinator", "researcher")
    await repo.record_task_handoff("task-1-coord", "task-3-infra-check", "coordinator", "analyst")
    await repo.record_task_handoff("task-2-ip-audit", "task-4-critic", "researcher", "critic")
    await repo.record_task_handoff("task-3-infra-check", "task-4-critic", "analyst", "critic")
    await repo.record_task_handoff("task-4-critic", "task-5-escrow-matrix", "critic", "planner")
    await repo.record_task_handoff("task-5-escrow-matrix", "task-6-synth", "planner", "synthesizer")

    # 5. Sources
    sources_data = [
        ("src_deck", "ApexAI Founder Pitch Deck & Management Representations", "https://dealroom.ventureaudit.internal/apexai/deck-q3-2026.pdf", "pitch_deck"),
        ("src_git_bom", "Engineering SBOM & Git Repository Deep Audit", "https://audit.ventureaudit.internal/reports/apexai-sbom-git-audit.json", "code_audit"),
        ("src_legal", "Delaware Chancery Court Docket (Case #2026-0842-JTL)", "https://courts.delaware.gov/chancery/dockets/2026-0842-jtl", "court_docket"),
        ("src_infra", "Terraform State & AWS CloudWatch Telemetry Dump", "https://infra-audit.ventureaudit.internal/aws/apexai-tfstate-dump.json", "infrastructure_audit"),
    ]
    for s_id, title, uri, s_type in sources_data:
        src = Source(id=s_id, title=title, uri=uri, source_type=s_type)
        await repo.save_source(src)

    # 6. Claims & Explicit Contradictions
    claim_prop = Claim(
        id="claim-founder-prop",
        project_id=proj_id,
        run_id=run_id,
        agent_id="agent-ma-research",
        agent_role="researcher",
        text="Founder Pitch Deck asserts ApexAI Core Engine is 100% proprietary with zero external copyleft dependencies and 99.99% multi-region cloud uptime.",
        confidence=0.88,
        status="contradicted",
        supporting_source_ids=["src_deck"],
    )
    await repo.save_claim(claim_prop)

    claim_gpl = Claim(
        id="claim-gpl-copyleft",
        project_id=proj_id,
        run_id=run_id,
        agent_id="agent-ma-research",
        agent_role="researcher",
        text="Engineering SBOM reveals core/routing_engine dynamically links ffmpeg & libx264 under GPLv3, triggering viral copyleft contamination of commercial engine.",
        confidence=0.98,
        status="verified",
        supporting_source_ids=["src_git_bom"],
    )
    await repo.save_claim(claim_gpl)

    claim_legal = Claim(
        id="claim-legal-injunction",
        project_id=proj_id,
        run_id=run_id,
        agent_id="agent-ma-research",
        agent_role="researcher",
        text="Delaware Chancery Court docket reveals an undisclosed preliminary injunction over proprietary model weights trained on scraped competitor data.",
        confidence=0.95,
        status="verified",
        supporting_source_ids=["src_legal"],
    )
    await repo.save_claim(claim_legal)

    claim_infra = Claim(
        id="claim-infra-singleregion",
        project_id=proj_id,
        run_id=run_id,
        agent_id="agent-ma-analyst",
        agent_role="analyst",
        text="Terraform configs confirm single-region us-east-1 deployment with zero read replicas, invalidating founder 99.99% multi-region uptime representation.",
        confidence=0.96,
        status="verified",
        supporting_source_ids=["src_infra"],
    )
    await repo.save_claim(claim_infra)

    # Record the key CONTRADICTIONS:
    # 1. Founder 100% proprietary claim vs GPLv3 viral copyleft
    await repo.record_contradiction(
        claim_a_id="claim-founder-prop",
        claim_b_id="claim-gpl-copyleft",
        notes="Critical IP Conflict: Founder representations assert 100% proprietary zero-copyleft engine, directly contradicted by Git SBOM finding GPLv3 dynamic link in core/routing_engine.",
    )

    # 2. Founder 99.99% multi-region uptime vs Single-region us-east-1 RDS
    await repo.record_contradiction(
        claim_a_id="claim-founder-prop",
        claim_b_id="claim-infra-singleregion",
        notes="Infrastructure Conflict: Founder claimed 99.99% multi-region cloud uptime, but AWS Terraform state confirms single-region us-east-1 instance with zero read replicas (measured 99.12%).",
    )

    # 7. 3-Tier Cognitive Memories
    # Procedural Rules seeded with confidence: 0.60
    proc_rules = [
        Memory(
            id="mem-proc-ip-sbom",
            project_id=proj_id,
            run_id=run_id,
            agent_id="agent-ma-critic",
            agent_role="critic",
            task_id="task-4-critic",
            content="Cross-reference all founder proprietary IP assertions against the Git SBOM for GPL/AGPL copyleft triggers before approving valuation.",
            instruction="Cross-reference all founder proprietary IP assertions against the Git SBOM for GPL/AGPL copyleft triggers before approving valuation.",
            memory_type="procedural",
            confidence=0.60,
            successes=1,
            failures=0,
            tags=["ip", "licensing", "due-diligence"],
        ),
        Memory(
            id="mem-proc-infra-uptime",
            project_id=proj_id,
            run_id=run_id,
            agent_id="agent-ma-analyst",
            agent_role="analyst",
            task_id="task-3-infra-check",
            content="Verify multi-region uptime claims against raw cloud infrastructure configurations rather than marketing materials.",
            instruction="Verify multi-region uptime claims against raw cloud infrastructure configurations rather than marketing materials.",
            memory_type="procedural",
            confidence=0.60,
            successes=1,
            failures=0,
            tags=["infrastructure", "cloud", "uptime"],
        ),
        Memory(
            id="mem-proc-litigation-escrow",
            project_id=proj_id,
            run_id=run_id,
            agent_id="agent-ma-planner",
            agent_role="planner",
            task_id="task-5-escrow-matrix",
            content="Flag any undisclosed litigation as a high-risk escrow withholding blocker.",
            instruction="Flag any undisclosed litigation as a high-risk escrow withholding blocker.",
            memory_type="procedural",
            confidence=0.60,
            successes=1,
            failures=0,
            tags=["legal", "escrow", "compliance"],
        ),
    ]
    for p in proc_rules:
        await repo.save_memory(p)

    # Semantic Memories (valid_at set)
    mem_semantic = Memory(
        id="mem-semantic-escrow-withholding",
        project_id=proj_id,
        run_id=run_id,
        agent_id="agent-ma-planner",
        agent_role="planner",
        task_id="task-5-escrow-matrix",
        content="Valuation Adjustment: Withhold $12M in deal escrow until GPLv3 dynamic link in core/routing_engine is replaced with MIT-licensed alternative and Delaware injunction is resolved.",
        memory_type="semantic",
        confidence=0.96,
        tags=["escrow", "valuation", "m-and-a"],
        valid_at=datetime.utcnow(),
    )
    await repo.save_memory(mem_semantic)

    # Episodic Memory linked to Run with outcome
    mem_episode = Memory(
        id="mem-ep-apexai-audit",
        project_id=proj_id,
        run_id=run_id,
        agent_id="agent-ma-synth",
        agent_role="synthesizer",
        task_id="task-6-synth",
        content="Due Diligence Episode: Detected material founder misrepresentation on proprietary IP and infrastructure reliability; triggered escrow withholding protocol.",
        memory_type="episodic",
        confidence=0.95,
        tags=["episode", "due-diligence", "audit"],
    )
    await repo.save_memory(mem_episode)
    await repo.record_episode(run_id, "mem-ep-apexai-audit", "disputed")

    # 8. Turns (Conversation Chain)
    turn1 = Turn(
        id="turn-audit-1",
        run_id=run_id,
        role="user",
        content="Can we proceed with closing the $45M ApexAI acquisition based on the founder's pitch deck representations?",
        prev_turn_id=None,
        mentioned_claim_ids=[],
    )
    await repo.create_turn(turn1)

    turn2 = Turn(
        id="turn-audit-2",
        run_id=run_id,
        role="assistant",
        content="Due diligence has uncovered material discrepancies. The Git SBOM audit detected GPLv3 copyleft contamination in core/routing_engine, and AWS configurations show a single-region deployment, directly contradicting founder claims. An escrow withholding of $12M is advised.",
        prev_turn_id="turn-audit-1",
        mentioned_claim_ids=["claim-founder-prop", "claim-gpl-copyleft"],
    )
    await repo.create_turn(turn2)

    return {
        "status": "seeded",
        "project_id": proj_id,
        "run_id": run_id,
        "tasks_count": str(len(tasks)),
        "claims_count": str(len(sources_data)),
        "contradictions_count": "2",
        "memories_count": str(len(proc_rules) + 2),
        "turns_count": "2",
    }


async def seed_incident_demo_project(repo: GraphRepository) -> dict[str, str]:
    """Seed the Production Incident & Architecture Investigation demo into the active graph repository."""
    proj_id = "proj-incident-investigation"
    run1_id = "run-incident-root-cause"
    run2_id = "run-incident-remediation"

    project = Project(
        id=proj_id,
        name="Production Incident & Architecture Investigation",
        description="High-concurrency outage analysis: Redis/FalkorDB connection pool exhaustion and P99 latency remediation.",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await repo.create_project(project)

    run1 = Run(
        id=run1_id,
        project_id=proj_id,
        goal="Investigate P99 latency spike to 4200ms and connection pool exhaustion under 25k req/s traffic spike.",
        status="completed",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        task_count=5,
        completed_task_count=5,
        findings_count=3,
        conflicts_count=1,
    )
    await repo.create_run(run1)

    agents_r1 = [
        ("agent-inc-coord-1", "coordinator", "Incident Commander"),
        ("agent-inc-research-1", "researcher", "Telemetry Inspector"),
        ("agent-inc-analyst-1", "analyst", "Kernel & Sockets Analyst"),
        ("agent-inc-critic-1", "critic", "Contradiction Verifier"),
        ("agent-inc-synth-1", "synthesizer", "Post-Mortem Synthesizer"),
    ]
    for a_id, role, name in agents_r1:
        await repo.record_relationship(run1_id, a_id, "INCLUDES_AGENT")

    tasks_r1 = [
        Task(
            id="task-inc-1-triage",
            run_id=run1_id,
            title="Triage Telemetry & Isolate Failure Boundary",
            description="Examine API gateway latency percentiles, error rates, and downstream service calls.",
            assigned_role="coordinator",
            assigned_agent_id="agent-inc-coord-1",
            status="completed",
            priority="critical",
            dependencies=[],
        ),
        Task(
            id="task-inc-2-metrics",
            run_id=run1_id,
            title="Gather Prometheus Metrics for DB Resource Utilization",
            description="Inspect Redis CPU, RAM, and query throughput graphs from monitoring dashboard.",
            assigned_role="researcher",
            assigned_agent_id="agent-inc-research-1",
            status="completed",
            priority="high",
            dependencies=["task-inc-1-triage"],
        ),
        Task(
            id="task-inc-3-socket",
            run_id=run1_id,
            title="Inspect Kernel Socket Queues & Client Pool Leases",
            description="Check /proc/net/tcp backlog, socket drop counters, and async connection pool waits.",
            assigned_role="analyst",
            assigned_agent_id="agent-inc-analyst-1",
            status="completed",
            priority="high",
            dependencies=["task-inc-1-triage"],
        ),
        Task(
            id="task-inc-4-critic",
            run_id=run1_id,
            title="Cross-Examine Metrics against Socket Backlog",
            description="Detect contradictory signals between healthy dashboard metrics and severe socket queue saturation.",
            assigned_role="critic",
            assigned_agent_id="agent-inc-critic-1",
            status="completed",
            priority="critical",
            dependencies=["task-inc-2-metrics", "task-inc-3-socket"],
        ),
        Task(
            id="task-inc-5-synth",
            run_id=run1_id,
            title="Synthesize Post-Mortem & Remediation Plan",
            description="Formalize root cause and specify architectural safeguards.",
            assigned_role="synthesizer",
            assigned_agent_id="agent-inc-synth-1",
            status="completed",
            priority="high",
            dependencies=["task-inc-4-critic"],
        ),
    ]
    for t in tasks_r1:
        await repo.create_task(t)

    await repo.record_task_handoff("task-inc-1-triage", "task-inc-2-metrics", "coordinator", "researcher")
    await repo.record_task_handoff("task-inc-1-triage", "task-inc-3-socket", "coordinator", "analyst")
    await repo.record_task_handoff("task-inc-2-metrics", "task-inc-4-critic", "researcher", "critic")
    await repo.record_task_handoff("task-inc-3-socket", "task-inc-4-critic", "analyst", "critic")
    await repo.record_task_handoff("task-inc-4-critic", "task-inc-5-synth", "critic", "synthesizer")

    sources_r1 = [
        ("src-prom-metrics", "Prometheus Node Exporter & Redis Gauge Dashboard", "https://monitoring.prod.internal/dashboards/redis-cluster", "metrics"),
        ("src-socket-proc", "Linux /proc/net/tcp and TCP SYN backlog kernel dumps", "https://logs.prod.internal/kernel/tcp-backlog-dump.log", "system_logs"),
        ("src-app-tracing", "OpenTelemetry Distributed Trace Spans during Outage", "https://tracing.prod.internal/spans/redis-timeout-cluster", "traces"),
    ]
    for s_id, title, uri, s_type in sources_r1:
        await repo.save_source(Source(id=s_id, title=title, uri=uri, source_type=s_type))

    claim_normal = Claim(
        id="claim-redis-normal",
        project_id=proj_id,
        run_id=run1_id,
        agent_id="agent-inc-research-1",
        agent_role="researcher",
        text="Prometheus dashboard metrics indicate Redis memory and CPU are within nominal limits (24% CPU, 41% RAM).",
        confidence=0.65,
        status="challenged",
        supporting_source_ids=["src-prom-metrics"],
    )
    await repo.save_claim(claim_normal)

    claim_exhausted = Claim(
        id="claim-redis-exhausted",
        project_id=proj_id,
        run_id=run1_id,
        agent_id="agent-inc-analyst-1",
        agent_role="analyst",
        text="Linux socket queue and TCP SYN backlog show 12,000 unhandled sockets dropping connections due to client-side BlockingConnectionPool exhaustion.",
        confidence=0.96,
        status="verified",
        supporting_source_ids=["src-socket-proc", "src-app-tracing"],
    )
    await repo.save_claim(claim_exhausted)

    claim_timeout = Claim(
        id="claim-timeout-impact",
        project_id=proj_id,
        run_id=run1_id,
        agent_id="agent-inc-analyst-1",
        agent_role="analyst",
        text="Client applications experienced 504 Gateway Timeouts on graph queries when pool threads waited > 5000ms for connection lease.",
        confidence=0.94,
        status="verified",
        supporting_source_ids=["src-app-tracing"],
    )
    await repo.save_claim(claim_timeout)

    await repo.record_contradiction(
        claim_a_id="claim-redis-normal",
        claim_b_id="claim-redis-exhausted",
        notes="Prometheus polling at 15s intervals missed sub-second connection pool starvation, causing false negative telemetry.",
    )

    mem_rule_weak = Memory(
        id="mem-rule-prom-trust",
        project_id=proj_id,
        run_id=run1_id,
        agent_id="agent-inc-critic-1",
        agent_role="critic",
        task_id="task-inc-4-critic",
        content="Assume read replica health metrics from Prometheus dashboard are always accurate",
        instruction="Assume read replica health metrics from Prometheus dashboard are always accurate",
        memory_type="procedural",
        confidence=0.45,
        successes=0,
        failures=1,
        tags=["telemetry", "monitoring", "incident"],
    )
    await repo.save_memory(mem_rule_weak)

    mem_rule_strong = Memory(
        id="mem-rule-socket-verify",
        project_id=proj_id,
        run_id=run1_id,
        agent_id="agent-inc-critic-1",
        agent_role="critic",
        task_id="task-inc-4-critic",
        content="Cross-verify socket queue depth against connection pool saturation before clearing database health",
        instruction="Cross-verify socket queue depth against connection pool saturation before clearing database health",
        memory_type="procedural",
        confidence=0.68,
        successes=1,
        failures=0,
        tags=["database", "connection-pool", "concurrency"],
    )
    await repo.save_memory(mem_rule_strong)

    mem_episode_inc = Memory(
        id="mem-ep-outage-root",
        project_id=proj_id,
        run_id=run1_id,
        agent_id="agent-inc-synth-1",
        agent_role="synthesizer",
        task_id="task-inc-5-synth",
        content="Incident episode: False negative on Redis health due to Prometheus sampling aliasing during 25k req/s connection pool starvation.",
        memory_type="episodic",
        confidence=0.95,
        tags=["episode", "incident", "outage"],
    )
    await repo.save_memory(mem_episode_inc)
    await repo.record_episode(run1_id, "mem-ep-outage-root", "challenged")

    t1 = Turn(
        id="turn-inc-1",
        run_id=run1_id,
        role="user",
        content="Why did our graph queries spike to 4.2s latency when CPU was under 30%?",
        prev_turn_id=None,
        mentioned_claim_ids=[],
    )
    await repo.create_turn(t1)

    t2 = Turn(
        id="turn-inc-2",
        run_id=run1_id,
        role="assistant",
        content="The team cross-examined dashboard metrics with kernel socket logs. While CPU and memory were healthy, client-side connection pools were starved at 32 connections, backing up over 12,000 socket requests in the SYN backlog.",
        prev_turn_id="turn-inc-1",
        mentioned_claim_ids=["claim-redis-exhausted", "claim-timeout-impact"],
    )
    await repo.create_turn(t2)

    t3 = Turn(
        id="turn-inc-3",
        run_id=run1_id,
        role="user",
        content="Did Prometheus catch this bottleneck?",
        prev_turn_id="turn-inc-2",
        mentioned_claim_ids=[],
    )
    await repo.create_turn(t3)

    t4 = Turn(
        id="turn-inc-4",
        run_id=run1_id,
        role="assistant",
        content="No. The 15s Prometheus scrape interval smoothed over the sub-second connection starvation spikes, leading to an explicit telemetry contradiction with kernel socket queues.",
        prev_turn_id="turn-inc-3",
        mentioned_claim_ids=["claim-redis-normal", "claim-redis-exhausted"],
    )
    await repo.create_turn(t4)

    # ------------------ RUN 2: ARCHITECTURE REMEDIATION ------------------
    run2 = Run(
        id=run2_id,
        project_id=proj_id,
        goal="Implement resilient async connection pooling, read-only replica query routing, and kernel backlog tuning to prevent recurring outages.",
        status="completed",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        task_count=4,
        completed_task_count=4,
        findings_count=2,
        conflicts_count=0,
    )
    await repo.create_run(run2)

    agents_r2 = [
        ("agent-inc-coord-2", "coordinator", "Remediation Coordinator"),
        ("agent-inc-planner-2", "planner", "Database Systems Architect"),
        ("agent-inc-analyst-2", "analyst", "Performance Engineer"),
        ("agent-inc-synth-2", "synthesizer", "Architecture Synthesizer"),
    ]
    for a_id, role, name in agents_r2:
        await repo.record_relationship(run2_id, a_id, "INCLUDES_AGENT")

    tasks_r2 = [
        Task(
            id="task-rem-1-recall",
            run_id=run2_id,
            title="Recall Prior Incident Episodes & Query Procedural Rules",
            description="Retrieve high-confidence rules (confidence >= 0.55) and avoid known failure modes from Run 1.",
            assigned_role="coordinator",
            assigned_agent_id="agent-inc-coord-2",
            status="completed",
            priority="high",
            dependencies=[],
        ),
        Task(
            id="task-rem-2-pool",
            run_id=run2_id,
            title="Configure Async BlockingConnectionPool & Concurrency Limits",
            description="Tune pool to max_connections=64 with non-blocking async acquisition.",
            assigned_role="analyst",
            assigned_agent_id="agent-inc-analyst-2",
            status="completed",
            priority="critical",
            dependencies=["task-rem-1-recall"],
        ),
        Task(
            id="task-rem-3-ro",
            run_id=run2_id,
            title="Route Read Traffic via FalkorDB GRAPH.RO_QUERY",
            description="Separate read and write paths to maximize read throughput and avoid blocking master writes.",
            assigned_role="planner",
            assigned_agent_id="agent-inc-planner-2",
            status="completed",
            priority="high",
            dependencies=["task-rem-2-pool"],
        ),
        Task(
            id="task-rem-4-verify",
            run_id=run2_id,
            title="Execute Synthetic 30k req/s Load Test & Verify Latency",
            description="Validate P99 remains below 50ms under peak load.",
            assigned_role="synthesizer",
            assigned_agent_id="agent-inc-synth-2",
            status="completed",
            priority="critical",
            dependencies=["task-rem-3-ro"],
        ),
    ]
    for t in tasks_r2:
        await repo.create_task(t)

    await repo.record_task_handoff("task-rem-1-recall", "task-rem-2-pool", "coordinator", "analyst")
    await repo.record_task_handoff("task-rem-2-pool", "task-rem-3-ro", "analyst", "planner")
    await repo.record_task_handoff("task-rem-3-ro", "task-rem-4-verify", "planner", "synthesizer")

    sources_r2 = [
        ("src-loadtest-results", "Locust 30k req/s Stress Test Run Results", "https://ci.benchmarks.internal/runs/locust-30k-falkordb", "benchmark"),
        ("src-falkor-ro-spec", "FalkorDB Read-Only Query Optimization Spec", "https://docs.falkordb.com/commands/graph.ro_query.html", "documentation"),
    ]
    for s_id, title, uri, s_type in sources_r2:
        await repo.save_source(Source(id=s_id, title=title, uri=uri, source_type=s_type))

    claim_upgrade = Claim(
        id="claim-pool-upgrade",
        project_id=proj_id,
        run_id=run2_id,
        agent_id="agent-inc-analyst-2",
        agent_role="analyst",
        text="Upgrading to async BlockingConnectionPool with max_connections=64 resolved client queue latency, stabilizing P99 under 38ms.",
        confidence=0.97,
        status="verified",
        supporting_source_ids=["src-loadtest-results"],
    )
    await repo.save_claim(claim_upgrade)

    claim_ro = Claim(
        id="claim-ro-throughput",
        project_id=proj_id,
        run_id=run2_id,
        agent_id="agent-inc-planner-2",
        agent_role="planner",
        text="Routing read queries via GRAPH.RO_QUERY offloads 82% of query traffic from primary coordinator node, eliminating contention.",
        confidence=0.95,
        status="verified",
        supporting_source_ids=["src-falkor-ro-spec", "src-loadtest-results"],
    )
    await repo.save_claim(claim_ro)

    mem_standard = Memory(
        id="mem-pool-standard",
        project_id=proj_id,
        run_id=run2_id,
        agent_id="agent-inc-synth-2",
        agent_role="synthesizer",
        task_id="task-rem-4-verify",
        content="Architecture Standard: Use falkordb.asyncio with BlockingConnectionPool and explicit GRAPH.RO_QUERY for high-concurrency read operations.",
        memory_type="semantic",
        confidence=0.98,
        tags=["architecture", "falkordb", "best-practice"],
    )
    await repo.save_memory(mem_standard)

    t5 = Turn(
        id="turn-rem-1",
        run_id=run2_id,
        role="user",
        content="How does the revised architecture handle 30k req/s?",
        prev_turn_id=None,
        mentioned_claim_ids=[],
    )
    await repo.create_turn(t5)

    t6 = Turn(
        id="turn-rem-2",
        run_id=run2_id,
        role="assistant",
        content="Under synthetic 30k req/s testing, async BlockingConnectionPool combined with GRAPH.RO_QUERY reduced P99 latency from 4,200ms to 38ms with zero socket timeouts.",
        prev_turn_id="turn-rem-1",
        mentioned_claim_ids=["claim-pool-upgrade", "claim-ro-throughput"],
    )
    await repo.create_turn(t6)

    return {
        "status": "seeded",
        "project_id": proj_id,
        "runs_count": "2",
        "tasks_count": str(len(tasks_r1) + len(tasks_r2)),
        "claims_count": str(len(sources_r1) + len(sources_r2)),
        "contradictions_count": "1",
        "memories_count": "4",
        "turns_count": "6",
    }


async def seed_all_demo_projects(repo: GraphRepository) -> dict[str, Any]:
    """Seed all demo projects (VentureAudit + Incident Investigation)."""
    audit_res = await seed_demo_project(repo)
    incident_res = await seed_incident_demo_project(repo)
    return {
        "status": "seeded_all",
        "scenarios": {
            "venture_audit": audit_res,
            "incident_investigation": incident_res,
        },
    }


# Backward-compatibility alias
seed_ai_tutoring_demo = seed_demo_project
