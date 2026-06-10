import json

from sqlalchemy.orm import Session, joinedload

from app.models import Branch, Graph, Session as InquirySession
from app.renderers.branch_question import render_branch_question
from app.renderers.registry import render_node
from app.config import PLAYABLE_ASSET_TYPES
from app.schemas import BranchChoice, NodeState, PlaybackAssetState, SessionState
from app.utils.assets import asset_label, parse_asset_metadata
from app.services.graph import GraphNotFoundError, get_graph_by_slug, get_node_with_assets, get_outgoing_branches
from app.services.join_code import generate_join_code, is_valid_join_code, normalize_join_code


class SessionNotFoundError(Exception):
    pass


class BranchNotFoundError(Exception):
    pass


class InvalidBranchError(Exception):
    pass


class InvalidPhaseError(Exception):
    pass


class MediaAssetNotFoundError(Exception):
    pass


class InvalidMediaActionError(Exception):
    pass


AudioAssetNotFoundError = MediaAssetNotFoundError
InvalidAudioActionError = InvalidMediaActionError


def _load_history(inquiry_session: InquirySession) -> list[dict]:
    try:
        history = json.loads(inquiry_session.navigation_history_json or "[]")
    except json.JSONDecodeError:
        return []
    return history if isinstance(history, list) else []


def _save_history(inquiry_session: InquirySession, history: list[dict]) -> None:
    inquiry_session.navigation_history_json = json.dumps(history)


def _push_history(inquiry_session: InquirySession) -> None:
    history = _load_history(inquiry_session)
    history.append(
        {
            "node_id": inquiry_session.current_node_id,
            "display_phase": inquiry_session.display_phase,
        }
    )
    _save_history(inquiry_session, history)


def _can_go_back(inquiry_session: InquirySession) -> bool:
    if inquiry_session.display_phase == "branch_question":
        return True
    return len(_load_history(inquiry_session)) > 0


def _branch_choices(branches: list[Branch]) -> list[BranchChoice]:
    return [
        BranchChoice(
            id=b.id,
            label=b.label,
            student_label=b.student_label.strip() or b.label,
            to_slug=b.to_node.slug,
        )
        for b in branches
    ]


def _has_branch_question(node) -> bool:
    return bool(node.branch_question_md.strip())


def _can_show_question(node, branches: list[Branch]) -> bool:
    return _has_branch_question(node) and len(branches) >= 2


def _playback_assets(node, display_phase: str) -> list[PlaybackAssetState]:
    if display_phase != "content":
        return []
    assets: list[PlaybackAssetState] = []
    for asset in sorted(node.assets, key=lambda item: item.id):
        if asset.asset_type not in PLAYABLE_ASSET_TYPES:
            continue
        metadata = parse_asset_metadata(asset.metadata_json)
        assets.append(
            PlaybackAssetState(
                id=asset.id,
                label=asset_label(asset.path, asset.alt_text),
                kind=asset.asset_type,
                autoplay=bool(metadata.get("autoplay")),
            )
        )
    return assets


def _render_display_content(
    node, branches: list[Branch], graph_slug: str, display_phase: str
) -> str:
    if display_phase == "branch_question":
        return render_branch_question(node, branches)
    return render_node(node, graph_slug)


def _build_session_state(db: Session, inquiry_session: InquirySession) -> SessionState:
    graph = inquiry_session.graph
    node = get_node_with_assets(db, inquiry_session.current_node_id)
    branches = get_outgoing_branches(db, node.id)
    display_phase = inquiry_session.display_phase

    if display_phase == "branch_question" and not _can_show_question(node, branches):
        display_phase = "content"

    return SessionState(
        session_id=inquiry_session.id,
        join_code=inquiry_session.join_code,
        graph_slug=graph.slug,
        graph_title=graph.title,
        display_phase=display_phase,
        has_branch_question=_has_branch_question(node),
        can_show_question=_can_show_question(node, branches),
        can_go_back=_can_go_back(inquiry_session),
        node=NodeState(
            slug=node.slug,
            title=node.title,
            html_content=_render_display_content(node, branches, graph.slug, display_phase),
            node_type=node.node_type,
        ),
        branches=_branch_choices(branches),
        playback_assets=_playback_assets(node, display_phase),
    )


def control_playback(
    db: Session, graph_slug: str, session_id: str, asset_id: int, action: str
) -> tuple[SessionState, int, str]:
    action = action.strip().lower()
    if action not in {"play", "pause", "stop"}:
        raise InvalidMediaActionError(f"Unknown media action '{action}'")

    inquiry_session = get_session(db, graph_slug, session_id)
    node = get_node_with_assets(db, inquiry_session.current_node_id)
    if inquiry_session.display_phase != "content":
        raise InvalidPhaseError("Media playback is only available on the main slide")

    asset = next((item for item in node.assets if item.id == asset_id), None)
    if not asset or asset.asset_type not in PLAYABLE_ASSET_TYPES:
        raise MediaAssetNotFoundError(f"Media asset {asset_id} not found on this slide")

    return _build_session_state(db, inquiry_session), asset_id, action


control_audio = control_playback


def create_session(db: Session, graph_slug: str) -> InquirySession:
    graph = get_graph_by_slug(db, graph_slug)
    if not graph.entry_node_id:
        raise GraphNotFoundError(f"Graph '{graph_slug}' has no entry node")

    db.query(InquirySession).filter(
        InquirySession.graph_id == graph.id,
        InquirySession.status == "active",
    ).update({"status": "archived"}, synchronize_session=False)

    inquiry_session = InquirySession(
        graph_id=graph.id,
        current_node_id=graph.entry_node_id,
        display_phase="content",
        navigation_history_json="[]",
        join_code=generate_join_code(db),
        status="active",
    )
    db.add(inquiry_session)
    db.commit()
    db.refresh(inquiry_session)
    return inquiry_session


def get_session_by_join_code(db: Session, join_code: str) -> InquirySession:
    code = normalize_join_code(join_code)
    if not is_valid_join_code(code):
        raise SessionNotFoundError(f"Session code '{join_code}' not found")

    inquiry_session = (
        db.query(InquirySession)
        .options(joinedload(InquirySession.graph), joinedload(InquirySession.current_node))
        .filter(InquirySession.join_code == code, InquirySession.status == "active")
        .first()
    )
    if not inquiry_session:
        raise SessionNotFoundError(f"Session code '{code}' not found")
    return inquiry_session


def get_session_state_by_join_code(db: Session, join_code: str) -> SessionState:
    inquiry_session = get_session_by_join_code(db, join_code)
    return _build_session_state(db, inquiry_session)


def activate_session(db: Session, graph_slug: str, session_id: str) -> InquirySession:
    inquiry_session = get_session(db, graph_slug, session_id)
    db.query(InquirySession).filter(
        InquirySession.graph_id == inquiry_session.graph_id,
        InquirySession.id != inquiry_session.id,
        InquirySession.status == "active",
    ).update({"status": "archived"}, synchronize_session=False)
    inquiry_session.status = "active"
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


def show_branch_question(db: Session, graph_slug: str, session_id: str) -> SessionState:
    inquiry_session = get_session(db, graph_slug, session_id)
    node = get_node_with_assets(db, inquiry_session.current_node_id)
    branches = get_outgoing_branches(db, node.id)

    if not _can_show_question(node, branches):
        raise InvalidPhaseError("This node has no branch question to show")

    inquiry_session.display_phase = "branch_question"
    db.commit()
    db.refresh(inquiry_session)
    return _build_session_state(db, inquiry_session)


def show_content(db: Session, graph_slug: str, session_id: str) -> SessionState:
    inquiry_session = get_session(db, graph_slug, session_id)
    inquiry_session.display_phase = "content"
    db.commit()
    db.refresh(inquiry_session)
    return _build_session_state(db, inquiry_session)


def go_back(db: Session, graph_slug: str, session_id: str) -> SessionState:
    inquiry_session = get_session(db, graph_slug, session_id)

    if inquiry_session.display_phase == "branch_question":
        inquiry_session.display_phase = "content"
    else:
        history = _load_history(inquiry_session)
        if not history:
            raise InvalidPhaseError("Nothing to go back to")
        previous = history.pop()
        _save_history(inquiry_session, history)
        inquiry_session.current_node_id = previous["node_id"]
        inquiry_session.display_phase = previous.get("display_phase", "content")

    db.commit()
    db.refresh(inquiry_session)
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

    _push_history(inquiry_session)
    inquiry_session.current_node_id = branch.to_node_id
    inquiry_session.display_phase = "content"
    db.commit()
    db.refresh(inquiry_session)
    return _build_session_state(db, inquiry_session)


def reset_session(db: Session, graph_slug: str, session_id: str) -> SessionState:
    inquiry_session = get_session(db, graph_slug, session_id)
    graph = inquiry_session.graph
    if not graph.entry_node_id:
        raise GraphNotFoundError(f"Graph '{graph_slug}' has no entry node")

    inquiry_session.current_node_id = graph.entry_node_id
    inquiry_session.display_phase = "content"
    _save_history(inquiry_session, [])
    db.commit()
    db.refresh(inquiry_session)
    return _build_session_state(db, inquiry_session)