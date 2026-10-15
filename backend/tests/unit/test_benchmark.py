import asyncio
from app.graph.local_adapter import LocalGraphAdapter
from app.demo.seed_data import seed_demo_project
from app.evaluation.benchmark import EvaluationBenchmark


def async_test(coro):
    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))
    return wrapper


@async_test
async def test_evaluation_benchmark_suite():
    repo = LocalGraphAdapter()
    await repo.initialize()
    await seed_demo_project(repo)

    benchmark = EvaluationBenchmark(repo)
    report = await benchmark.evaluate_project("proj-ai-tutoring")

    assert report is not None
    assert report.total_claims >= 4
    assert report.citation_grounding_rate >= 0.75
    assert report.detected_contradictions >= 1
    assert report.contradiction_recall == 1.0
    assert report.passed_all_gates is True
