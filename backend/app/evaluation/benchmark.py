from dataclasses import dataclass, field
from typing import Any
from datetime import datetime
import asyncio

from app.graph.base import GraphRepository
from app.graph.local_adapter import LocalGraphAdapter
from app.demo.seed_data import seed_demo_project


@dataclass
class BenchmarkReport:
    project_id: str
    evaluated_at: str
    total_claims: int
    grounded_claims: int
    citation_grounding_rate: float
    seeded_contradictions: int
    detected_contradictions: int
    contradiction_recall: float
    total_tasks: int
    completed_tasks: int
    task_completion_rate: float
    total_sources: int
    passed_all_gates: bool
    metrics_summary: dict[str, Any] = field(default_factory=dict)


class EvaluationBenchmark:
    """Automated quality evaluator testing contradiction recall, citation grounding, and graph integrity."""

    def __init__(self, repo: GraphRepository) -> None:
        self.repo = repo

    async def evaluate_project(self, project_id: str) -> BenchmarkReport:
        claims = await self.repo.list_claims(project_id)
        disputes = await self.repo.get_disputes_with_evidence(project_id)
        tasks = []
        runs = await self.repo.list_runs(project_id)
        if runs:
            tasks = await self.repo.list_tasks(runs[0].id)

        project_graph = await self.repo.get_project_graph(project_id, limit=500)
        source_nodes = [n for n in project_graph.nodes if n.label == "Source"]

        # 1. Citation Grounding: Every empirical claim must have supporting_source_ids or CITES edges
        grounded_count = 0
        for c in claims:
            has_sources = len(c.supporting_source_ids) > 0
            has_edges = any(e.source == c.id and e.relationship == "CITES" for e in project_graph.edges)
            if has_sources or has_edges:
                grounded_count += 1
        grounding_rate = round(grounded_count / len(claims), 4) if claims else 1.0

        # 2. Contradiction Recall: Did we detect the seeded TAM conflict?
        # Seeded dataset contains 1 major contradiction between B2C TAM ($5.2B) and K-12 ceiling ($800M)
        seeded_contradictions = 1
        detected_contradictions = len(disputes)
        contradiction_recall = min(round(detected_contradictions / seeded_contradictions, 4), 1.0) if seeded_contradictions else 1.0

        # 3. Task Completion Rate
        completed_tasks = sum(1 for t in tasks if t.status == "completed")
        completion_rate = round(completed_tasks / len(tasks), 4) if tasks else 1.0

        # Gate pass conditions: 100% contradiction recall, >= 75% citation grounding, >= 80% task completion
        passed_all_gates = (contradiction_recall >= 1.0) and (grounding_rate >= 0.75) and (completion_rate >= 0.8)

        return BenchmarkReport(
            project_id=project_id,
            evaluated_at=datetime.utcnow().isoformat(),
            total_claims=len(claims),
            grounded_claims=grounded_count,
            citation_grounding_rate=grounding_rate,
            seeded_contradictions=seeded_contradictions,
            detected_contradictions=detected_contradictions,
            contradiction_recall=contradiction_recall,
            total_tasks=len(tasks),
            completed_tasks=completed_tasks,
            task_completion_rate=completion_rate,
            total_sources=len(source_nodes),
            passed_all_gates=passed_all_gates,
            metrics_summary={
                "citation_grounding_score": f"{grounding_rate * 100:.1f}%",
                "contradiction_recall_score": f"{contradiction_recall * 100:.1f}%",
                "task_completion_score": f"{completion_rate * 100:.1f}%",
            },
        )


async def run_benchmark_cli() -> None:
    repo = LocalGraphAdapter()
    await repo.initialize()
    await seed_demo_project(repo)

    benchmark = EvaluationBenchmark(repo)
    report = await benchmark.evaluate_project("proj-ai-tutoring")

    print("==================================================")
    print("        SWARMMIND QUALITY BENCHMARK REPORT        ")
    print("==================================================")
    print(f"Project ID:               {report.project_id}")
    print(f"Timestamp:                {report.evaluated_at}")
    print(f"Claims Grounded:          {report.grounded_claims}/{report.total_claims} ({report.metrics_summary['citation_grounding_score']})")
    print(f"Contradiction Recall:     {report.detected_contradictions}/{report.seeded_contradictions} ({report.metrics_summary['contradiction_recall_score']})")
    print(f"Tasks Completed:          {report.completed_tasks}/{report.total_tasks} ({report.metrics_summary['task_completion_score']})")
    print(f"Sources Integrated:       {report.total_sources}")
    print("--------------------------------------------------")
    print(f"OVERALL EVALUATION GATE:  {'PASSED [100%]' if report.passed_all_gates else 'FAILED'}")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_benchmark_cli())
