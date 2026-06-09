from sqlalchemy.orm import Session, joinedload

from app.models import Branch, Graph, Session as InquirySession
from app.renderers.registry import render_node
from app.schemas import BranchChoice, NodeState, SessionState
from app.services.graph import GraphNotFoundError, get_graph_by_slug, get_node_with_assets, get_outgoing_branches


class SessionNotFoundError(Exception):
    pass


class BranchNotFoundError(Exception):
    pass


class InvalidBranchError(Exception):
    pass


def _build_session_state(db: Session, inquiry_session: InquirySession) -> SessionState:
    graph = inquiry_session.graph
    node = get_node_with_assets(db, inquiry_session.current_node_id)
    branches = get_outgoing_branches(db, node.id)

    return SessionState(
        session_id=inquiry_session.id,
        graph_slug=graph.slug,
        graph_title=graph.title,
        node=NodeState(
            slug=node.slug,
            title=node.title,
            html_content=render_node(node, graph.slug),
            node_type=node.node_type,
        ),
        branches=[
            BranchChoice(id=b.id, label=b.label, to_slug=b.to_node.slug)
            for b in branches
        ],
    )


def create_session(db: Session, graph_slug: str) -> InquirySession:
    graph = get_graph_by_slug(db, graph_slug)
    if not graph.entry_node_id:
        raise GraphNotFoundError(f"Graph '{graph_slug}' has no entry node")

    inquiry_session = InquirySession(
        graph_id=graph.id,
        current_node_id=graph.entry_node_id,
        status="active",
    )
    db.add(inquiry_session)
    db.commit()
    db.refresh(inquiry_session)
    return inquiry_session


def get_session(db: Session, graph_slug: str, session_id: str) -> InquirySession:
    graph = get_graph_by_slug(db, graph_slug)
    inquiry_session = (
        db.query(InquirySession)
        .options(joinedload(InquirySession.graph), joinedload(InquirySession.current_node))
        .filter(InquirySession.id == session_id, InquirySession.graph_id == graph.id)
        .first()
    )
    if not inquiry_session:
        raise SessionNotFoundError(f"Session '{session_id}' not found")
    return inquiry_session


def get_session_state(db: Session, graph_slug: str, session_id: str) -> SessionState:
    inquiry_session = get_session(db, graph_slug, session_id)
    return _build_session_state(db, inquiry_session)


def select_branch(
    db: Session, graph_slug: str, session_id: str, branch_id: int
) -> SessionState:
    inquiry_session = get_session(db, graph_slug, session_id)
    branch = (
        db.query(Branch)
        .options(joinedload(Branch.to_node))
        .filter(Branch.id == branch_id, Branch.graph_id == inquiry_session.graph_id)
        .first()
    )
    if not branch:
        raise BranchNotFoundError(f"Branch {branch_id} not found")
    if branch.from_node_id != inquiry_session.current_node_id:
        raise InvalidBranchError("Branch is not available from the current node")

    inquiry_session.current_node_id = branch.to_node_id
    db.commit()
    db.refresh(inquiry_session)
    return _build_session_state(db, inquiry_session)


def reset_session(db: Session, graph_slug: str, session_id: str) -> SessionState:
    inquiry_session = get_session(db, graph_slug, session_id)
    graph = inquiry_session.graph
    if not graph.entry_node_id:
        raise GraphNotFoundError(f"Graph '{graph_slug}' has no entry node")

    inquiry_session.current_node_id = graph.entry_node_id
    db.commit()
    db.refresh(inquiry_session)
    return _build_session_state(db, inquiry_session)