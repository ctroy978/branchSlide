from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import GraphSummary, LoadMapRequest
from app.services.loader import LoaderError, load_inquiry_map

router = APIRouter(prefix="/api/admin")


@router.post("/load", response_model=GraphSummary)
def admin_load_map(payload: LoadMapRequest, db: Session = Depends(get_db)) -> GraphSummary:
    try:
        graph = load_inquiry_map(db, payload.path)
        return GraphSummary(slug=graph.slug, title=graph.title, description=graph.description)
    except LoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc