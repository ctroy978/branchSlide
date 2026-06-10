from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import BASE_DIR
from app.database import get_db
from app.services.join_code import is_valid_join_code, normalize_join_code
from app.services.session import SessionNotFoundError, get_session_state_by_join_code
from app.utils.network import build_teacher_base_url

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


def _error_response(
    request: Request,
    *,
    title: str,
    message: str,
    status_code: int = 404,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "title": title,
            "message": message,
            "action_url": "/",
            "action_label": "Enter a different code",
        },
        status_code=status_code,
    )


@router.get("/", response_class=HTMLResponse)
def projector_join(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "projector_join.html", {})


@router.get("/{join_code}", response_class=HTMLResponse)
def projector_by_code(
    request: Request,
    join_code: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    code = normalize_join_code(join_code)
    if not is_valid_join_code(code):
        return _error_response(
            request,
            title="Invalid code",
            message="Enter the 4-character code shown on the teacher panel.",
        )

    try:
        state = get_session_state_by_join_code(db, code)
    except SessionNotFoundError:
        return _error_response(
            request,
            title="Code not found",
            message="No active class matches that code. Check the code on the teacher panel and try again.",
        )

    teacher_sync_url, _ = build_teacher_base_url(request)

    return templates.TemplateResponse(
        request,
        "projector.html",
        {
            "state": state,
            "join_code": code,
            "use_join_code": True,
            "teacher_sync_url": teacher_sync_url,
        },
    )