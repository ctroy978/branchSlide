from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.websocket import broadcast_media_control, broadcast_session_state
from app.schemas import BranchSelectRequest, MediaControlRequest, SessionState
from app.services.graph import GraphNotFoundError
from app.services.session import (
    AudioAssetNotFoundError,
    BranchNotFoundError,
    InvalidAudioActionError,
    InvalidBranchError,
    InvalidPhaseError,
    SessionNotFoundError,
    control_playback,
    create_session,
    get_session_state,
    get_session_state_by_join_code,
    go_back,
    reset_session,
    select_branch,
    show_branch_question,
    show_content,
)

router = APIRouter(prefix="/api")


@router.post("/g/{graph_slug}/sessions", response_model=SessionState)
def api_create_session(graph_slug: str, db: Session = Depends(get_db)) -> SessionState:
    try:
        inquiry_session = create_session(db, graph_slug)
        return get_session_state(db, graph_slug, inquiry_session.id)
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/join/{join_code}", response_model=SessionState)
def api_get_session_by_join_code(
    join_code: str, db: Session = Depends(get_db)
) -> SessionState:
    try:
        return get_session_state_by_join_code(db, join_code)
    except SessionNotFoundError as exc:
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


@router.post("/g/{graph_slug}/sessions/{session_id}/show-question", response_model=SessionState)
async def api_show_question(
    graph_slug: str, session_id: str, db: Session = Depends(get_db)
) -> SessionState:
    try:
        state = show_branch_question(db, graph_slug, session_id)
        await broadcast_session_state(session_id, state.model_dump())
        return state
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidPhaseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/g/{graph_slug}/sessions/{session_id}/show-content", response_model=SessionState)
async def api_show_content(
    graph_slug: str, session_id: str, db: Session = Depends(get_db)
) -> SessionState:
    try:
        state = show_content(db, graph_slug, session_id)
        await broadcast_session_state(session_id, state.model_dump())
        return state
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


async def _api_control_media(
    graph_slug: str,
    session_id: str,
    payload: MediaControlRequest,
    db: Session,
) -> SessionState:
    state, asset_id, action = control_playback(
        db, graph_slug, session_id, payload.asset_id, payload.action
    )
    await broadcast_media_control(session_id, asset_id, action)
    return state


@router.post("/g/{graph_slug}/sessions/{session_id}/media", response_model=SessionState)
async def api_control_media(
    graph_slug: str,
    session_id: str,
    payload: MediaControlRequest,
    db: Session = Depends(get_db),
) -> SessionState:
    try:
        return await _api_control_media(graph_slug, session_id, payload, db)
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except MediaAssetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidPhaseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvalidMediaActionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/g/{graph_slug}/sessions/{session_id}/audio", response_model=SessionState)
async def api_control_audio(
    graph_slug: str,
    session_id: str,
    payload: MediaControlRequest,
    db: Session = Depends(get_db),
) -> SessionState:
    """Backward-compatible alias for /media."""
    return await api_control_media(graph_slug, session_id, payload, db)


@router.post("/g/{graph_slug}/sessions/{session_id}/back", response_model=SessionState)
async def api_go_back(
    graph_slug: str, session_id: str, db: Session = Depends(get_db)
) -> SessionState:
    try:
        state = go_back(db, graph_slug, session_id)
        await broadcast_session_state(session_id, state.model_dump())
        return state
    except GraphNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidPhaseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc