from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import GraphSummary, LoadMapRequest, ValidationIssueOut, ValidationReport
from app.services.loader import LoaderError, load_inquiry_map
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
def admin_load_map(payload: LoadMapRequest, db: Session = Depends(get_db)) -> GraphSummary:
    try:
        graph = load_inquiry_map(db, payload.path)
        return GraphSummary(slug=graph.slug, title=graph.title, description=graph.description)
    except LoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc