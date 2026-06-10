from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SessionState
from app.services.session import SessionNotFoundError, get_session_state_by_join_code

router = APIRouter(prefix="/api")


@router.get("/{join_code}", response_model=SessionState)
def api_get_session_by_code(
    join_code: str,
    db: Session = Depends(get_db),
) -> SessionState:
    try:
        return get_session_state_by_join_code(db, join_code)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc