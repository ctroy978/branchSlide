from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import BASE_DIR
from app.database import get_db
from app.services.graph import GraphNotFoundError, list_graphs
from app.services.session import SessionNotFoundError, create_session, get_session_state

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


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
    request: Request, graph_slug: str, db: Session = Depends(get_db)
) -> HTMLResponse:
    try:
        inquiry_session = create_session(db, graph_slug)
        state = get_session_state(db, graph_slug, inquiry_session.id)
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    projector_url = f"/g/{graph_slug}/projector?session={state.session_id}"
    return templates.TemplateResponse(
        request,
        "teacher.html",
        {
            "state": state,
            "projector_url": projector_url,
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
    except (GraphNotFoundError, SessionNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return templates.TemplateResponse(
        request,
        "projector.html",
        {
            "state": state,
            "graph_slug": graph_slug,
            "session_id": session,
        },
    )