from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.websocket import broadcast_session_state
from app.schemas import BranchSelectRequest, SessionState
from app.services.graph import GraphNotFoundError
from app.services.session import (
    BranchNotFoundError,
    InvalidBranchError,
    SessionNotFoundError,
    create_session,
    get_session_state,
    reset_session,
    select_branch,
)

router = APIRouter(prefix="/api")


@router.post("/g/{graph_slug}/sessions", response_model=SessionState)
def api_create_session(graph_slug: str, db: Session = Depends(get_db)) -> SessionState:
    try:
        inquiry_session = create_session(db, graph_slug)
        return get_session_state(db, graph_slug, inquiry_session.id)
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/g/{graph_slug}/sessions/{session_id}", response_model=SessionState)
def api_get_session(
    graph_slug: str, session_id: str, db: Session = Depends(get_db)
) -> SessionState:
    try:
        return get_session_state(db, graph_slug, session_id)
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/g/{graph_slug}/sessions/{session_id}/branch", response_model=SessionState)
async def api_select_branch(
    graph_slug: str,
    session_id: str,
    payload: BranchSelectRequest,
    db: Session = Depends(get_db),
) -> SessionState:
    try:
        state = select_branch(db, graph_slug, session_id, payload.branch_id)
        await broadcast_session_state(session_id, state.model_dump())
        return state
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BranchNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidBranchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/g/{graph_slug}/sessions/{session_id}/reset", response_model=SessionState)
async def api_reset_session(
    graph_slug: str, session_id: str, db: Session = Depends(get_db)
) -> SessionState:
    try:
        state = reset_session(db, graph_slug, session_id)
        await broadcast_session_state(session_id, state.model_dump())
        return state
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc