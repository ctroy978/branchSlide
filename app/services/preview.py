from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.renderers.branch_question import render_branch_question
from app.renderers.registry import render_node
from app.schemas import BranchChoice, NodeState, PreviewState
from app.services.graph import (
    GraphNotFoundError,
    get_graph_by_slug,
    get_node_by_slug,
    get_node_with_assets,
    get_outgoing_branches,
)


def parse_history(history_param: str | None) -> list[tuple[str, str]]:
    if not history_param:
        return []
    entries: list[tuple[str, str]] = []
    for part in history_param.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            continue
        node_slug, phase = part.split(":", 1)
        if node_slug and phase in {"content", "branch_question"}:
            entries.append((node_slug, phase))
    return entries


def encode_history(history: list[tuple[str, str]]) -> str:
    return ",".join(f"{slug}:{phase}" for slug, phase in history)


def _branch_choices(branches) -> list[BranchChoice]:
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


def _can_show_question(node, branches) -> bool:
    return _has_branch_question(node) and len(branches) >= 2


def _render_display_content(node, branches, graph_slug: str, display_phase: str) -> str:
    if display_phase == "branch_question":
        return render_branch_question(node, branches)
    return render_node(node, graph_slug)


def build_preview_state(
    db: Session,
    graph_slug: str,
    node_slug: str | None = None,
    display_phase: str = "content",
    history: list[tuple[str, str]] | None = None,
) -> PreviewState:
    graph = get_graph_by_slug(db, graph_slug)
    history = list(history or [])

    if node_slug:
        node = get_node_by_slug(db, graph.id, node_slug)
    else:
        if not graph.entry_node_id:
            raise GraphNotFoundError(f"Graph '{graph_slug}' has no entry node")
        node = get_node_with_assets(db, graph.entry_node_id)

    if display_phase not in {"content", "branch_question"}:
        display_phase = "content"

    branches = get_outgoing_branches(db, node.id)
    if display_phase == "branch_question" and not _can_show_question(node, branches):
        display_phase = "content"

    can_go_back = display_phase == "branch_question" or len(history) > 0

    return PreviewState(
        graph_slug=graph.slug,
        graph_title=graph.title,
        node_slug=node.slug,
        display_phase=display_phase,
        has_branch_question=_has_branch_question(node),
        can_show_question=_can_show_question(node, branches),
        can_go_back=can_go_back,
        history=encode_history(history),
        node=NodeState(
            slug=node.slug,
            title=node.title,
            html_content=_render_display_content(node, branches, graph.slug, display_phase),
            node_type=node.node_type,
            layout=node.layout,
        ),
        branches=_branch_choices(branches),
    )


def preview_path(
    graph_slug: str,
    node_slug: str,
    display_phase: str = "content",
    history: list[tuple[str, str]] | None = None,
) -> str:
    params: dict[str, str] = {"node": node_slug, "phase": display_phase}
    encoded = encode_history(history or [])
    if encoded:
        params["h"] = encoded
    return f"/g/{graph_slug}/preview?{urlencode(params)}"


def preview_branch_path(
    graph_slug: str,
    current_node_slug: str,
    current_phase: str,
    to_node_slug: str,
    history: list[tuple[str, str]] | None = None,
) -> str:
    history = list(history or [])
    history.append((current_node_slug, current_phase))
    return preview_path(graph_slug, to_node_slug, "content", history)


def preview_show_question_path(
    graph_slug: str,
    node_slug: str,
    history: list[tuple[str, str]] | None = None,
) -> str:
    return preview_path(graph_slug, node_slug, "branch_question", history)


def preview_show_content_path(
    graph_slug: str,
    node_slug: str,
    history: list[tuple[str, str]] | None = None,
) -> str:
    return preview_path(graph_slug, node_slug, "content", history)


def preview_back_path(
    graph_slug: str,
    node_slug: str,
    display_phase: str,
    history: list[tuple[str, str]] | None = None,
) -> str | None:
    history = list(history or [])
    if display_phase == "branch_question":
        return preview_path(graph_slug, node_slug, "content", history)
    if not history:
        return None
    previous_node_slug, previous_phase = history.pop()
    return preview_path(graph_slug, previous_node_slug, previous_phase, history)