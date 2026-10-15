import json
from pathlib import Path
from datetime import datetime
from app.graph.base import GraphRepository
from app.schemas.project import Project
from app.schemas.run import Run
from app.schemas.agent import Agent
from app.schemas.task import Task
from app.schemas.claim import Claim, Source
from app.schemas.memory import Memory


async def seed_demo_project(repo: GraphRepository) -> dict[str, str]:
    """Seed the complete Signature Demo evaluation project into the active graph repository.

    Scenario: Fictional startup evaluating an AI Tutoring product launch.
    Contains: Project, Run, 6 Agents, 6 Tasks with dependencies, Sources, Claims,
              an explicit CONTRADICTS dispute, and shared Memories.
    """
    proj_id = "proj-ai-tutoring"
    run_id = "run-ai-tutoring-eval"

    # 1. Project
    project = Project(
        id=proj_id,
        name="AI Tutoring Product Feasibility & Launch Strategy",
        description="Comprehensive evaluation of market TAM, inference economics, pedagogical efficacy, and launch risks for Socratic AI tutor.",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await repo.create_project(project)

    # 2. Run
    run = Run(
        id=run_id,
        project_id=proj_id,
        goal="Evaluate whether our startup should launch an AI tutoring product. Assess market TAM, inference costs, pedagogical efficacy, contradictions in market estimates, and provide a launch recommendation.",
        status="completed",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        task_count=6,
        completed_task_count=6,
        findings_count=5,
        conflicts_count=1,
    )
    await repo.create_run(run)

    # 3. Agents
    agents_spec = [
        ("agent-coord", "coordinator", "Coordinator Agent"),
        ("agent-research", "researcher", "Researcher Agent"),
        ("agent-analyst", "analyst", "Analyst Agent"),
        ("agent-critic", "critic", "Critic Agent"),
        ("agent-planner", "planner", "Planner Agent"),
        ("agent-synth", "synthesizer", "Synthesizer Agent"),
    ]
    for a_id, role, name in agents_spec:
        agent = Agent(id=a_id, role=role, name=name, status="completed")
        await repo.record_relationship(run_id, a_id, "INCLUDES_AGENT")

    # 4. Tasks with dependencies
    tasks = [
        Task(
            id="task-1-coord",
            run_id=run_id,
            title="Decompose Investigation Goals & Schedule Team",
            description="Establish research boundaries, metrics, and assign specialized agent roles.",
            assigned_role="coordinator",
            assigned_agent_id="agent-coord",
            status="completed",
            priority="high",
            dependencies=[],
        ),
        Task(
            id="task-2-market",
            run_id=run_id,
            title="Gather Market Intelligence & TAM Estimates",
            description="Collect global EdTech market sizes and public school district procurement data.",
            assigned_role="researcher",
            assigned_agent_id="agent-research",
            status="completed",
            priority="high",
            dependencies=["task-1-coord"],
        ),
        Task(
            id="task-3-tech",
            run_id=run_id,
            title="Analyze Inference Costs & Latency Feasibility",
            description="Calculate token economics, audio latency, and gross margins at $15/month B2C tier.",
            assigned_role="analyst",
            assigned_agent_id="agent-analyst",
            status="completed",
            priority="medium",
            dependencies=["task-1-coord"],
        ),
        Task(
            id="task-4-critic",
            run_id=run_id,
            title="Cross-Examine Claims & Detect Market Size Contradiction",
            description="Validate evidence sources and flag conflicting claims between B2C TAM and K-12 institutional caps.",
            assigned_role="critic",
            assigned_agent_id="agent-critic",
            status="completed",
            priority="high",
            dependencies=["task-2-market", "task-3-tech"],
        ),
        Task(
            id="task-5-plan",
            run_id=run_id,
            title="Formulate Go-To-Market Roadmap & Guardrails",
            description="Prioritize direct-to-consumer launch to bypass K-12 14-month procurement cycle.",
            assigned_role="planner",
            assigned_agent_id="agent-planner",
            status="completed",
            priority="high",
            dependencies=["task-4-critic"],
        ),
        Task(
            id="task-6-synth",
            run_id=run_id,
            title="Synthesize Final Executive Report with Evidence Provenance",
            description="Compile final findings, recommendations, and auditable graph citations.",
            assigned_role="synthesizer",
            assigned_agent_id="agent-synth",
            status="completed",
            priority="critical",
            dependencies=["task-5-plan"],
        ),
    ]

    for t in tasks:
        await repo.create_task(t)

    # 5. Sources
    sources_data = [
        ("src-edtech-tam-2026", "Global EdTech & AI Tutoring Market Intelligence Report 2026", "https://research.edtech-analytics.internal/reports/2026-market-size", "industry_report"),
        ("src-k12-saturation-survey", "K-12 Public School District Procurement & Budget Survey 2026", "https://gov.ed-procurement.internal/surveys/2026-district-budgets", "survey"),
        ("src-inference-cost-benchmark", "Real-Time Socratic LLM Voice & Text Inference Economics", "https://ai-infra.benchmarks.internal/cost-per-student-hour", "technical_benchmark"),
        ("src-pedagogical-efficacy-study", "Cognitive Scaffolding Meta-Analysis on 1-on-1 AI Tutoring", "https://cognition.edu.internal/papers/2025-ai-scaffolding-results", "academic_study"),
        ("src-hallucination-risk-brief", "Educational AI Compliance & Hallucination Guardrails Brief", "https://ed-safety.standards.internal/guidelines/hallucination-risks", "safety_brief"),
    ]
    for s_id, title, uri, s_type in sources_data:
        src = Source(id=s_id, title=title, uri=uri, source_type=s_type)
        await repo.save_source(src)

    # 6. Claims & Explicit Contradiction
    claim_bull = Claim(
        id="claim-tam-bull",
        project_id=proj_id,
        run_id=run_id,
        agent_id="agent-research",
        agent_role="researcher",
        text="Global AI Tutoring TAM is estimated at $5.2B with a 38.4% CAGR through 2030, driven by direct-to-consumer adoption.",
        confidence=0.88,
        status="proposed",
        supporting_source_ids=["src-edtech-tam-2026"],
    )
    await repo.save_claim(claim_bull)

    claim_bear = Claim(
        id="claim-tam-bear",
        project_id=proj_id,
        run_id=run_id,
        agent_id="agent-critic",
        agent_role="critic",
        text="Institutional K-12 market ceiling is restricted to $800M due to 14-month district procurement cycles and state certification barriers.",
        confidence=0.84,
        status="proposed",
        supporting_source_ids=["src-k12-saturation-survey"],
    )
    await repo.save_claim(claim_bear)

    claim_cost = Claim(
        id="claim-inference-feasible",
        project_id=proj_id,
        run_id=run_id,
        agent_id="agent-analyst",
        agent_role="analyst",
        text="Real-time Socratic voice inference costs $0.042/student-hour, enabling viable 72% gross margins on a $15/month B2C tier.",
        confidence=0.92,
        status="supported",
        supporting_source_ids=["src-inference-cost-benchmark"],
    )
    await repo.save_claim(claim_cost)

    claim_efficacy = Claim(
        id="claim-efficacy-gain",
        project_id=proj_id,
        run_id=run_id,
        agent_id="agent-analyst",
        agent_role="analyst",
        text="Socratic active-recall scaffolding produces +0.62 sigma gains in student mastery compared to standard LLM direct answers.",
        confidence=0.89,
        status="verified",
        supporting_source_ids=["src-pedagogical-efficacy-study"],
    )
    await repo.save_claim(claim_efficacy)

    # Record the key CONTRADICTION between TAM estimates
    await repo.record_contradiction(
        claim_a_id="claim-tam-bull",
        claim_b_id="claim-tam-bear",
        notes="Conflict identified by Critic: Direct-to-consumer market ($5.2B TAM) vs Institutional district procurement ($800M ceiling). Resolution: Launch direct-to-consumer first.",
    )

    # 7. Persistent Memories
    memories = [
        Memory(
            id="mem-tam-resolution",
            project_id=proj_id,
            run_id=run_id,
            agent_id="agent-planner",
            agent_role="planner",
            task_id="task-5-plan",
            content="Strategic Decision: Target direct-to-consumer parents ($5.2B TAM) instead of school districts ($800M ceiling) to avoid 14-month procurement delays.",
            memory_type="rule",
            confidence=0.90,
            tags=["gtm", "strategy", "tam"],
        ),
        Memory(
            id="mem-latency-requirement",
            project_id=proj_id,
            run_id=run_id,
            agent_id="agent-analyst",
            agent_role="analyst",
            task_id="task-3-tech",
            content="Technical Constraint: Voice response latency must remain below 400ms to preserve Socratic conversational immersion.",
            memory_type="fact",
            confidence=0.95,
            tags=["technical", "latency", "voice"],
        ),
        Memory(
            id="mem-hallucination-guardrail",
            project_id=proj_id,
            run_id=run_id,
            agent_id="agent-critic",
            agent_role="critic",
            task_id="task-4-critic",
            content="Safety Guardrail: Deterministic math solver verifier required before outputting step-by-step arithmetic solutions.",
            memory_type="rule",
            confidence=0.96,
            tags=["safety", "compliance"],
        ),
    ]

    for m in memories:
        await repo.save_memory(m)

    return {
        "status": "seeded",
        "project_id": proj_id,
        "run_id": run_id,
        "tasks_count": str(len(tasks)),
        "claims_count": "4",
        "contradictions_count": "1",
        "memories_count": str(len(memories)),
    }
