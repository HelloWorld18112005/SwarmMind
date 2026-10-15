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
        system_text = next((m.content.lower() for m in messages if m.role == "system"), "")
        prompt_text = " ".join(m.content for m in messages).lower()
        target = system_text if system_text else prompt_text

        role = None
        for r in ["coordinator", "synthesizer", "planner", "critic", "analyst", "researcher"]:
            if f"you are the {r} agent" in target or f"{r} agent" in target:
                role = r
                break

        if not role:
            if "coordinator" in target or "decompose" in target:
                role = "coordinator"
            elif "synthesizer" in target or "unresolved_disputes" in target:
                role = "synthesizer"
            elif "planner" in target or "roadmap" in target:
                role = "planner"
            elif "critic" in target or "contradiction" in target:
                role = "critic"
            elif "analyst" in target:
                role = "analyst"
            elif "researcher" in target:
                role = "researcher"
            else:
                role = "synthesizer"

        # 1. Synthesizer
        if role == "synthesizer":
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

        # 2. Coordinator: goal decomposition into task graph
        elif role == "coordinator":
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

        # 3. Researcher: claims with source citations
        elif role == "researcher":
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

        # 4. Analyst: inferences & economics
        elif role == "analyst":
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

        # 5. Critic: contradiction detection & verification
        elif role == "critic":
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
        elif role == "planner":
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

        # Default fallback: Synthesizer
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
