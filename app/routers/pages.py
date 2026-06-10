from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import BASE_DIR
from app.database import get_db
from app.utils.network import build_projector_url, build_public_base_url
from app.services.graph import GraphNotFoundError, NodeNotFoundError, list_graphs
from app.services.preview import (
    build_preview_state,
    parse_history,
    preview_back_path,
    preview_branch_path,
    preview_show_question_path,
)
from app.services.session import (
    SessionNotFoundError,
    activate_session,
    create_session,
    get_session_state,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


def _error_response(
    request: Request,
    *,
    title: str,
    message: str,
    action_url: str | None = None,
    action_label: str | None = None,
    secondary_url: str | None = None,
    secondary_label: str | None = None,
    status_code: int = 404,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "title": title,
            "message": message,
            "action_url": action_url,
            "action_label": action_label,
            "secondary_url": secondary_url,
            "secondary_label": secondary_label,
        },
        status_code=status_code,
    )


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    graphs = list_graphs(db)
    return templates.TemplateResponse(
        request,
        "index.html",
        {"graphs": graphs},
    )


@router.get("/g/{graph_slug}/teacher", response_class=HTMLResponse)
def teacher_panel(
    request: Request,
    graph_slug: str,
    session: str | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    try:
        if session:
            activate_session(db, graph_slug, session)
            state = get_session_state(db, graph_slug, session)
        else:
            inquiry_session = create_session(db, graph_slug)
            return RedirectResponse(
                url=f"/g/{graph_slug}/teacher?session={inquiry_session.id}",
                status_code=303,
            )
    except GraphNotFoundError:
        return _error_response(
            request,
            title="Map not found",
            message="This inquiry map is not loaded. Check the URL or load the map from the home page.",
            action_url="/",
            action_label="View available maps",
        )
    except SessionNotFoundError:
        return _error_response(
            request,
            title="Session not found",
            message="This classroom session no longer exists. It may have been cleared, or the link is outdated.",
            action_url=f"/g/{graph_slug}/teacher",
            action_label="Start a new session",
            secondary_url="/",
            secondary_label="← All maps",
        )

    teacher_path = f"/g/{graph_slug}/teacher?session={state.session_id}"
    public_base, used_lan_fallback = build_public_base_url(request)
    projector_full_url, projector_lan_fallback = build_projector_url(request, state.join_code)
    teacher_full_url = f"{public_base}{teacher_path}"
    return templates.TemplateResponse(
        request,
        "teacher.html",
        {
            "state": state,
            "projector_full_url": projector_full_url,
            "teacher_url": teacher_path,
            "teacher_full_url": teacher_full_url,
            "used_lan_fallback": used_lan_fallback or projector_lan_fallback,
            "graph_slug": graph_slug,
        },
    )


@router.get("/g/{graph_slug}/projector", response_class=HTMLResponse)
def projector_view(
    request: Request,
    graph_slug: str,
    session: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    try:
        state = get_session_state(db, graph_slug, session)
    except GraphNotFoundError:
        return _error_response(
            request,
            title="Map not found",
            message="This inquiry map is not loaded. Ask the teacher to confirm the server is running and the map has been loaded.",
            action_url="/",
            action_label="View available maps",
        )
    except SessionNotFoundError:
        return _error_response(
            request,
            title="Session not found",
            message="This classroom session does not exist. Ask the teacher for an updated projector link.",
            action_url=f"/g/{graph_slug}/teacher",
            action_label="Open teacher panel",
            secondary_url="/",
            secondary_label="← All maps",
        )

    return templates.TemplateResponse(
        request,
        "projector.html",
        {
            "state": state,
            "graph_slug": graph_slug,
            "session_id": session,
        },
    )


@router.get("/g/{graph_slug}/preview", response_class=HTMLResponse)
def preview_map(
    request: Request,
    graph_slug: str,
    node: str | None = None,
    phase: str = "content",
    h: str | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    history = parse_history(h)
    try:
        state = build_preview_state(
            db,
            graph_slug,
            node_slug=node,
            display_phase=phase,
            history=history,
        )
    except GraphNotFoundError:
        return _error_response(
            request,
            title="Map not found",
            message="This inquiry map is not loaded. Load it first, then return to preview.",
            action_url="/",
            action_label="View available maps",
        )
    except NodeNotFoundError:
        return _error_response(
            request,
            title="Node not found",
            message="That node does not exist in this map. Return to the preview entry point.",
            action_url=f"/g/{graph_slug}/preview",
            action_label="Restart preview",
            secondary_url="/",
            secondary_label="← All maps",
        )

    branch_links = {
        branch.id: preview_branch_path(
            graph_slug,
            state.node_slug,
            state.display_phase,
            branch.to_slug,
            history,
        )
        for branch in state.branches
    }
    show_question_url = (
        preview_show_question_path(graph_slug, state.node_slug, history)
        if state.can_show_question and state.display_phase == "content"
        else None
    )
    back_url = (
        preview_back_path(graph_slug, state.node_slug, state.display_phase, history)
        if state.can_go_back
        else None
    )

    return templates.TemplateResponse(
        request,
        "preview.html",
        {
            "state": state,
            "graph_slug": graph_slug,
            "branch_links": branch_links,
            "show_question_url": show_question_url,
            "back_url": back_url,
        },
    )