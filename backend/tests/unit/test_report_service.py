import asyncio
from functools import wraps
import pytest
from app.graph.local_adapter import LocalGraphAdapter
from app.schemas.project import Project
from app.schemas.run import Run
from app.schemas.claim import Claim
from app.services.report_service import ReportService


def async_test(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


@async_test
async def test_report_service_generation_and_export():
    repo = LocalGraphAdapter()
    await repo.initialize()

    # Create project and run
    await repo.create_project(Project(id="p-rep", name="Report Project"))
    await repo.create_run(Run(id="r-rep", project_id="p-rep", goal="Evaluate AI tutoring feasibility"))

    # Add claims & contradiction
    c1 = Claim(id="c1", project_id="p-rep", run_id="r-rep", text="TAM is $5.2B in B2C")
    c2 = Claim(id="c2", project_id="p-rep", run_id="r-rep", text="TAM is $800M in K-12")
    await repo.save_claim(c1)
    await repo.save_claim(c2)
    await repo.record_contradiction("c1", "c2", "TAM divergence note")

    service = ReportService(repo)
    report = await service.generate_report("r-rep")

    assert report.run_id == "r-rep"
    assert len(report.findings) >= 2
    assert len(report.unresolved_conflicts) == 1
    assert "c1" in report.unresolved_conflicts[0].claim_a_id

    # Test markdown export
    md = await service.export_markdown("r-rep")
    assert "# Strategic Investigation Report" in md
    assert "Executive Summary" in md
    assert "Contradictions & Unresolved Disputes" in md
    assert "Prioritized Recommendations" in md

    await repo.close()
