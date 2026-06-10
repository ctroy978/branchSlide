import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import BASE_DIR, MAPS_DIR
from app.models import Asset, Branch, Graph, Node, Session as InquirySession
from app.services.graph import GraphNotFoundError, get_graph_by_slug
from app.services.loader import LoaderError, load_inquiry_map
from app.services.validation import MapValidationError, assert_map_valid


class MapRemoveError(Exception):
    pass


def resolve_map_dir(map_path: str | Path) -> Path:
    path = Path(map_path)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


def publish_map(db: Session, map_path: str | Path) -> Graph:
    """Validate a map folder and load it into the database."""
    map_dir = resolve_map_dir(map_path)
    try:
        assert_map_valid(map_dir)
    except MapValidationError as exc:
        raise LoaderError(str(exc)) from exc
    return load_inquiry_map(db, map_path)


def remove_map(
    db: Session,
    graph_slug: str,
    *,
    delete_files: bool = False,
    force: bool = False,
) -> None:
    """Remove a map from the database and optionally delete its folder on disk."""
    graph = get_graph_by_slug(db, graph_slug)
    source_path = graph.source_path
    active_sessions = (
        db.query(InquirySession)
        .filter(InquirySession.graph_id == graph.id, InquirySession.status == "active")
        .count()
    )
    if active_sessions and not force:
        raise MapRemoveError(
            f"Map '{graph_slug}' has {active_sessions} active session(s). "
            "Use force=True to remove anyway."
        )

    node_ids = [node.id for node in db.query(Node).filter(Node.graph_id == graph.id).all()]
    if node_ids:
        db.query(Asset).filter(Asset.node_id.in_(node_ids)).delete(synchronize_session=False)
    db.query(Branch).filter(Branch.graph_id == graph.id).delete(synchronize_session=False)
    db.query(InquirySession).filter(InquirySession.graph_id == graph.id).delete(
        synchronize_session=False
    )
    db.query(Node).filter(Node.graph_id == graph.id).delete(synchronize_session=False)
    db.delete(graph)
    db.commit()

    if delete_files and source_path:
        map_dir = Path(source_path)
        if map_dir.is_dir() and map_dir.resolve().parent == Path(MAPS_DIR).resolve():
            shutil.rmtree(map_dir)