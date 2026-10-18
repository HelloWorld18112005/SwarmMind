import json
from app.llm.base import ChatMessage, LLMProvider, LLMResponse


class MockProvider(LLMProvider):
    """Deterministic mock LLM provider simulating authentic multi-agent outputs for offline testing."""

    def __init__(self, model_name: str = "mock-model") -> None:
        self.model_name = model_name

    async def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 2000,
        response_json: bool = True,
    ) -> LLMResponse:
        prompt_text = " ".join(m.content for m in messages).lower()
        is_ma = any(k in prompt_text for k in ("apexai", "due diligence", "m&a", "venture", "escrow", "gpl", "founder", "sbom"))

        # 1. Coordinator: goal decomposition into task graph
        if "coordinator" in prompt_text or "decompose" in prompt_text:
            if is_ma:
                payload = {
                    "summary": "Decomposed ApexAI M&A due diligence into 5 specialized audit tasks.",
                    "tasks": [
                        {
                            "task_id": "task-ip",
                            "title": "Audit Founder Claims against Git SBOM",
                            "assigned_role": "researcher",
                            "priority": "critical",
                            "dependencies": [],
                        },
                        {
                            "task_id": "task-infra",
                            "title": "Analyze Cloud Availability & Single-Region Risks",
                            "assigned_role": "analyst",
                            "priority": "high",
                            "dependencies": [],
                        },
                        {
                            "task_id": "task-critic",
                            "title": "Cross-Examine Founder Claims & Flag Contradictions",
                            "assigned_role": "critic",
                            "priority": "critical",
                            "dependencies": ["task-ip", "task-infra"],
                        },
                        {
                            "task_id": "task-plan",
                            "title": "Formulate $45M Escrow Withholding Risk Matrix",
                            "assigned_role": "planner",
                            "priority": "high",
                            "dependencies": ["task-critic"],
                        },
                        {
                            "task_id": "task-synth",
                            "title": "Synthesize M&A Due Diligence Executive Report",
                            "assigned_role": "synthesizer",
                            "priority": "critical",
                            "dependencies": ["task-plan"],
                        },
                    ],
                }
            else:
                payload = {
                    "summary": "Decomposed investigation into 5 specialized dependent subtasks.",
                    "tasks": [
                        {
                            "task_id": "task-market",
                            "title": "Investigate Market Size & TAM",
                            "assigned_role": "researcher",
                            "priority": "high",
                            "dependencies": [],
                        },
                        {
                            "task_id": "task-tech",
                            "title": "Analyze Voice Latency & Inference Economics",
                            "assigned_role": "analyst",
                            "priority": "medium",
                            "dependencies": [],
                        },
                        {
                            "task_id": "task-critic",
                            "title": "Validate Claims & Check Market Contradictions",
                            "assigned_role": "critic",
                            "priority": "high",
                            "dependencies": ["task-market", "task-tech"],
                        },
                        {
                            "task_id": "task-plan",
                            "title": "Formulate Phased Go-To-Market Roadmap",
                            "assigned_role": "planner",
                            "priority": "high",
                            "dependencies": ["task-critic"],
                        },
                        {
                            "task_id": "task-synth",
                            "title": "Synthesize Executive Report with Citations",
                            "assigned_role": "synthesizer",
                            "priority": "critical",
                            "dependencies": ["task-plan"],
                        },
                    ],
                }
            return LLMResponse(content=json.dumps(payload), prompt_tokens=150, completion_tokens=220)

        # 2. Researcher: claims with source citations
        if "researcher" in prompt_text:
            if is_ma:
                payload = {
                    "findings": [
                        {
                            "claim_text": "Engineering SBOM reveals core/routing_engine dynamically links ffmpeg & libx264 under GPLv3, triggering viral copyleft contamination of commercial engine.",
                            "confidence": 0.98,
                            "source_title": "Engineering SBOM & Git Repository Deep Audit",
                            "source_uri": "https://audit.ventureaudit.internal/reports/apexai-sbom-git-audit.json",
                            "source_type": "code_audit",
                        },
                        {
                            "claim_text": "Delaware Chancery Court docket reveals an undisclosed preliminary injunction over proprietary model weights trained on scraped competitor data.",
                            "confidence": 0.95,
                            "source_title": "Delaware Chancery Court Docket (Case #2026-0842-JTL)",
                            "source_uri": "https://courts.delaware.gov/chancery/dockets/2026-0842-jtl",
                            "source_type": "court_docket",
                        },
                    ],
                    "summary": "Retrieved 2 verified forensic audit claims from SBOM and court records.",
                }
            else:
                payload = {
                    "findings": [
                        {
                            "claim_text": "Global AI Tutoring TAM is projected to reach $5.2B by 2030 with a 38.4% CAGR.",
                            "confidence": 0.88,
                            "source_title": "Global EdTech Market Intelligence Report 2026",
                            "source_uri": "https://research.edtech-analytics.internal/reports/2026-market-size",
                            "source_type": "industry_report",
                        },
                        {
                            "claim_text": "Public school district budgets cap institutional adoption at $800M due to procurement friction.",
                            "confidence": 0.84,
                            "source_title": "K-12 Procurement Survey 2026",
                            "source_uri": "https://gov.ed-procurement.internal/surveys/2026-district-budgets",
                            "source_type": "survey",
                        },
                    ],
                    "summary": "Retrieved 2 primary market claims with source citations.",
                }
            return LLMResponse(content=json.dumps(payload), prompt_tokens=180, completion_tokens=210)

        # 3. Analyst: inferences & economics
        if "analyst" in prompt_text:
            if is_ma:
                payload = {
                    "inferences": [
                        {
                            "text": "Terraform configs confirm single-region us-east-1 deployment with zero read replicas, invalidating founder 99.99% multi-region uptime representation.",
                            "confidence": 0.96,
                            "memory_type": "fact",
                            "tags": ["infrastructure", "cloud", "uptime"],
                        },
                        {
                            "text": "GPLv3 viral copyleft in routing engine creates significant commercial licensing exposure; requires cleanroom refactoring covenant.",
                            "confidence": 0.94,
                            "memory_type": "rule",
                            "tags": ["ip", "licensing", "covenant"],
                        },
                    ],
                    "summary": "Analyzed cloud infrastructure resilience and copyleft contamination blast radius.",
                }
            else:
                payload = {
                    "inferences": [
                        {
                            "text": "Unit inference cost is $0.042/hour, delivering 72% gross margins on a $15/student/month subscription.",
                            "confidence": 0.92,
                            "memory_type": "fact",
                            "tags": ["unit-economics", "inference", "margins"],
                        },
                        {
                            "text": "Voice round-trip latency must remain under 400ms to preserve Socratic pedagogical engagement.",
                            "confidence": 0.95,
                            "memory_type": "rule",
                            "tags": ["latency", "voice", "pedagogy"],
                        },
                    ],
                    "summary": "Modeled inference cost economics and latency constraints.",
                }
            return LLMResponse(content=json.dumps(payload), prompt_tokens=170, completion_tokens=190)

        # 4. Synthesizer: final executive report
        if "synthesizer" in prompt_text or "executive report" in prompt_text:
            if is_ma:
                payload = {
                    "title": "M&A Due Diligence Executive Report: ApexAI Acquisition ($45M Deal Escrow)",
                    "executive_summary": "Conditional approval recommended. Mandate $12M escrow withholding due to verified GPLv3 copyleft contamination in core engine and single-region infrastructure fragility.",
                    "key_findings": [
                        "Founder proprietary IP claim is contradicted by Git SBOM showing GPLv3 dynamic linking in core routing engine.",
                        "Founder 99.99% multi-region uptime claim is contradicted by AWS Terraform single-region configuration.",
                        "Delaware Chancery Court docket discloses an active preliminary injunction regarding scraped training data.",
                    ],
                    "unresolved_disputes": [
                        "Founder representations on proprietary code ownership directly contradict forensic SBOM audit."
                    ],
                    "confidence_assessment": "High confidence (0.96) anchored by code audit provenance and court docket evidence.",
                }
            else:
                payload = {
                    "title": "Strategic Feasibility Evaluation: Socratic AI Tutoring Platform",
                    "executive_summary": "Strong greenlight recommendation to launch direct-to-consumer AI tutoring, resolving market divergence through B2C positioning.",
                    "key_findings": [
                        "B2C TAM is $5.2B with 38% CAGR, far exceeding the $800M institutional school district ceiling.",
                        "Real-time voice inference costs $0.042/hour, supporting sustainable 72% gross margins.",
                        "Socratic active-recall scaffolding produces +0.62 sigma gains in student learning mastery.",
                    ],
                    "unresolved_disputes": [
                        "School district adoption timeline remains disputed (14-month procurement delay confirmed)."
                    ],
                    "confidence_assessment": "High confidence (0.89) backed by industry benchmark citations and unit economics analysis.",
                }
            return LLMResponse(content=json.dumps(payload), prompt_tokens=250, completion_tokens=300)

        # 5. Critic: contradiction detection & verification
        if "critic" in prompt_text or "contradiction" in prompt_text:
            if is_ma:
                payload = {
                    "verified_claims": [
                        "Terraform infrastructure dump confirms single-region us-east-1 deployment with zero read replicas.",
                    ],
                    "contradictions": [
                        {
                            "claim_a": "Founder Pitch Deck asserts ApexAI Core Engine is 100% proprietary with zero external copyleft dependencies.",
                            "claim_b": "Engineering SBOM reveals core/routing_engine dynamically links ffmpeg & libx264 under GPLv3, triggering viral copyleft contamination.",
                            "dispute_reason": "Founder representation of proprietary IP directly contradicted by forensic SBOM GPLv3 finding.",
                            "recommendation": "Preserve dispute and structure $12M deal escrow withholding for IP remediation before closing.",
                        }
                    ],
                    "summary": "Identified 1 critical IP contradiction between founder representations and Git SBOM.",
                }
            else:
                payload = {
                    "verified_claims": [
                        "Voice latency below 400ms is supported by cognitive latency benchmarks.",
                    ],
                    "contradictions": [
                        {
                            "claim_a": "Global AI Tutoring TAM is projected to reach $5.2B by 2030",
                            "claim_b": "Public school district budgets cap institutional adoption at $800M",
                            "dispute_reason": "Divergence between Direct-to-Consumer TAM ($5.2B) and K-12 Institutional Procurement ($800M ceiling).",
                            "recommendation": "Preserve dispute and recommend B2C parent-subscription GTM to avoid 14-month district procurement delays.",
                        }
                    ],
                    "summary": "Identified 1 critical market TAM contradiction between B2C and institutional estimates.",
                }
            return LLMResponse(content=json.dumps(payload), prompt_tokens=210, completion_tokens=240)

        # 6. Planner: actionable recommendations
        if "planner" in prompt_text:
            if is_ma:
                payload = {
                    "recommendations": [
                        {
                            "title": "Withhold $12M in Deal Escrow for IP Remediation",
                            "description": "Establish $12M indemnity escrow to cover cleanroom refactoring of GPLv3 dynamic link and Delaware litigation resolution.",
                            "priority": "critical",
                            "risks": ["Seller resistance to 26% holdback", "3-month refactor timeline"],
                        },
                        {
                            "title": "Mandate Multi-Region AWS Infrastructure Covenant",
                            "description": "Require seller to deploy multi-region read replicas in us-west-2 before final closing tranche.",
                            "priority": "high",
                            "risks": ["Minor infrastructure cost increase"],
                        },
                    ],
                    "summary": "Formulated 2 deal structuring recommendations with escrow holdback terms.",
                }
            else:
                payload = {
                    "recommendations": [
                        {
                            "title": "Launch Direct-to-Consumer Parent Tier First",
                            "description": "Bypass school district 14-month procurement cycles by marketing directly to parents seeking Socratic math tutoring.",
                            "priority": "high",
                            "risks": ["Parent CAC acquisition costs", "Churn outside of school semesters"],
                        },
                        {
                            "title": "Implement Dual-Pass Math Solver Guardrails",
                            "description": "Integrate a deterministic symbolic solver to prevent arithmetic hallucinations.",
                            "priority": "critical",
                            "risks": ["Extra 60ms latency overhead"],
                        },
                    ],
                    "summary": "Produced 2 prioritized recommendations with risk mitigations.",
                }
            return LLMResponse(content=json.dumps(payload), prompt_tokens=190, completion_tokens=230)

        # Fallback default
        payload = {
            "title": "Investigation Report",
            "executive_summary": "Completed analysis.",
            "key_findings": ["Completed successfully."],
            "unresolved_disputes": [],
            "confidence_assessment": "High confidence (0.85)",
        }
        return LLMResponse(content=json.dumps(payload), prompt_tokens=100, completion_tokens=100)
