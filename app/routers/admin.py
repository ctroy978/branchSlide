from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    GraphSummary,
    InstallResult,
    LibraryEntry,
    LoadMapRequest,
    ValidationIssueOut,
    ValidationReport,
)
from app.services.graph import GraphNotFoundError
from app.services.library import (
    LibraryError,
    delete_library_zip,
    install_library_zip,
    list_library_entries,
    save_uploaded_zip,
    uninstall_installed_map,
    validate_library_zip,
)
from app.services.loader import LoaderError
from app.services.maps import MapRemoveError, publish_map, remove_map
from app.services.validation import MapValidationError, ValidationIssue, validate_map

router = APIRouter(prefix="/api/admin")


def _issues_to_report(issues: list[ValidationIssue]) -> ValidationReport:
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


@router.post("/validate", response_model=ValidationReport)
def admin_validate_map(payload: LoadMapRequest) -> ValidationReport:
    try:
        issues = validate_map(payload.path)
    except MapValidationError as exc:
        issues = exc.issues
    return _issues_to_report(issues)


@router.get("/library", response_model=list[LibraryEntry])
def admin_list_library(db: Session = Depends(get_db)) -> list[LibraryEntry]:
    return [LibraryEntry(**entry) for entry in list_library_entries(db)]


@router.post("/library/upload", response_model=LibraryEntry)
async def admin_upload_library_zip(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> LibraryEntry:
    try:
        filename = await save_uploaded_zip(file)
    except LibraryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    entries = {entry["filename"]: entry for entry in list_library_entries(db)}
    entry = entries.get(filename)
    if not entry:
        raise HTTPException(status_code=500, detail="Upload succeeded but entry not found")
    return LibraryEntry(**entry)


@router.post("/library/{filename}/validate", response_model=ValidationReport)
def admin_validate_library_zip(filename: str) -> ValidationReport:
    try:
        issues = validate_library_zip(filename)
    except LibraryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _issues_to_report(issues)


@router.post("/library/{filename}/install", response_model=InstallResult)
def admin_install_library_zip(filename: str, db: Session = Depends(get_db)) -> InstallResult:
    try:
        graph, warnings = install_library_zip(db, filename)
    except LibraryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return InstallResult(
        graph=GraphSummary(slug=graph.slug, title=graph.title, description=graph.description),
        warnings=[
            ValidationIssueOut(
                severity=issue.severity,
                code=issue.code,
                message=issue.message,
                path=issue.path,
            )
            for issue in warnings
        ],
    )


@router.delete("/library/installed/{graph_slug}")
def admin_uninstall_library_map(
    graph_slug: str,
    force: bool = False,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        uninstall_installed_map(db, graph_slug, force=force)
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LibraryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "uninstalled", "slug": graph_slug}


@router.delete("/library/{filename}")
def admin_delete_library_zip(
    filename: str,
    force: bool = False,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        delete_library_zip(db, filename, force=force)
    except LibraryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "deleted", "filename": filename}


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