from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import GraphSummary, LoadMapRequest, ValidationIssueOut, ValidationReport
from app.services.graph import GraphNotFoundError
from app.services.loader import LoaderError
from app.services.maps import MapRemoveError, publish_map, remove_map
from app.services.validation import MapValidationError, validate_map

router = APIRouter(prefix="/api/admin")


@router.post("/validate", response_model=ValidationReport)
def admin_validate_map(payload: LoadMapRequest) -> ValidationReport:
    try:
        issues = validate_map(payload.path)
    except MapValidationError as exc:
        issues = exc.issues

    errors = [
        ValidationIssueOut(
            severity=issue.severity,
            code=issue.code,
            message=issue.message,
            path=issue.path,
        )
        for issue in issues
        if issue.severity == "error"
    ]
    warnings = [
        ValidationIssueOut(
            severity=issue.severity,
            code=issue.code,
            message=issue.message,
            path=issue.path,
        )
        for issue in issues
        if issue.severity == "warning"
    ]
    return ValidationReport(valid=len(errors) == 0, errors=errors, warnings=warnings)


@router.post("/load", response_model=GraphSummary)
def admin_publish_map(payload: LoadMapRequest, db: Session = Depends(get_db)) -> GraphSummary:
    """Validate and publish a map folder into the database."""
    try:
        graph = publish_map(db, payload.path)
        return GraphSummary(slug=graph.slug, title=graph.title, description=graph.description)
    except LoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/maps/{graph_slug}")
def admin_remove_map(
    graph_slug: str,
    delete_files: bool = False,
    force: bool = False,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        remove_map(db, graph_slug, delete_files=delete_files, force=force)
        return {"status": "removed", "slug": graph_slug}
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except MapRemoveError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc