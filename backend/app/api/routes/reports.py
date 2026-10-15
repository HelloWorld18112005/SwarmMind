from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import PlainTextResponse
from app.dependencies import GraphRepoDep
from app.schemas.report import Report
from app.services.report_service import ReportService

router = APIRouter(prefix="/runs/{run_id}", tags=["Executive Reports"])


@router.get("/report", response_model=Report, summary="Get synthesized executive report")
async def get_report(run_id: str, repo: GraphRepoDep) -> Report:
    service = ReportService(repo)
    try:
        return await service.generate_report(run_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/export", response_class=PlainTextResponse, summary="Export report as downloadable Markdown")
async def export_report(run_id: str, repo: GraphRepoDep) -> Response:
    service = ReportService(repo)
    try:
        md = await service.export_markdown(run_id)
        filename = f"swarmmind_report_{run_id}.md"
        return PlainTextResponse(
            content=md,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
