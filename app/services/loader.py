from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from app.config import BASE_DIR
from app.models import Asset, Branch, Graph, Node


class LoaderError(Exception):
    pass


def _resolve_map_dir(map_path: str | Path) -> Path:
    path = Path(map_path)
    if not path.is_absolute():
        path = BASE_DIR / path
    path = path.resolve()
    if not path.is_dir():
        raise LoaderError(f"Map directory not found: {path}")
    manifest = path / "manifest.yaml"
    if not manifest.is_file():
        raise LoaderError(f"manifest.yaml not found in {path}")
    return path


def _read_markdown(map_dir: Path, relative_path: str) -> str:
    content_path = map_dir / relative_path
    if not content_path.is_file():
        raise LoaderError(f"Content file not found: {content_path}")
    return content_path.read_text(encoding="utf-8")


def load_inquiry_map(db: Session, map_path: str | Path) -> Graph:
    map_dir = _resolve_map_dir(map_path)
    manifest = yaml.safe_load((map_dir / "manifest.yaml").read_text(encoding="utf-8"))

    graph_data = manifest.get("graph", {})
    slug = graph_data.get("slug")
    if not slug:
        raise LoaderError("manifest.graph.slug is required")

    graph = db.query(Graph).filter(Graph.slug == slug).first()
    if not graph:
        graph = Graph(
            slug=slug,
            title=graph_data.get("title", slug),
            description=graph_data.get("description", ""),
            source_path=str(map_dir),
        )
        db.add(graph)
        db.flush()
    else:
        graph.title = graph_data.get("title", slug)
        graph.description = graph_data.get("description", "")
        graph.source_path = str(map_dir)
        db.flush()

    node_slug_to_id: dict[str, int] = {}
    nodes_data = manifest.get("nodes", [])
    for index, node_data in enumerate(nodes_data):
        node_slug = node_data.get("slug")
        if not node_slug:
            raise LoaderError("Each node requires a slug")

        content_file = node_data.get("content")
        content_md = _read_markdown(map_dir, content_file) if content_file else ""

        node = (
            db.query(Node)
            .filter(Node.graph_id == graph.id, Node.slug == node_slug)
            .first()
        )
        if not node:
            node = Node(graph_id=graph.id, slug=node_slug)
            db.add(node)

        node.title = node_data.get("title", node_slug)
        node.content_md = content_md
        node.node_type = node_data.get("type", "content")
        node.sort_order = index
        db.flush()
        node_slug_to_id[node_slug] = node.id

    entry_slug = graph_data.get("entry_node")
    if entry_slug not in node_slug_to_id:
        raise LoaderError(f"entry_node '{entry_slug}' not found in nodes")
    graph.entry_node_id = node_slug_to_id[entry_slug]

    existing_branches = {
        (b.from_node_id, b.to_node_id, b.label)
        for b in db.query(Branch).filter(Branch.graph_id == graph.id).all()
    }
    seen_branches: set[tuple[int, int, str]] = set()

    for index, branch_data in enumerate(manifest.get("branches", [])):
        from_slug = branch_data.get("from")
        to_slug = branch_data.get("to")
        label = branch_data.get("label")
        if from_slug not in node_slug_to_id or to_slug not in node_slug_to_id:
            raise LoaderError(f"Branch references unknown node: {from_slug} -> {to_slug}")
        if not label:
            raise LoaderError(f"Branch {from_slug} -> {to_slug} requires a label")

        from_id = node_slug_to_id[from_slug]
        to_id = node_slug_to_id[to_slug]
        key = (from_id, to_id, label)
        seen_branches.add(key)

        branch = (
            db.query(Branch)
            .filter(
                Branch.graph_id == graph.id,
                Branch.from_node_id == from_id,
                Branch.to_node_id == to_id,
                Branch.label == label,
            )
            .first()
        )
        if not branch:
            branch = Branch(
                graph_id=graph.id,
                from_node_id=from_id,
                to_node_id=to_id,
                label=label,
            )
            db.add(branch)
        branch.sort_order = index
        db.flush()

    for from_id, to_id, label in existing_branches - seen_branches:
        db.query(Branch).filter(
            Branch.graph_id == graph.id,
            Branch.from_node_id == from_id,
            Branch.to_node_id == to_id,
            Branch.label == label,
        ).delete()

    node_ids = set(node_slug_to_id.values())
    db.query(Asset).filter(Asset.node_id.in_(node_ids)).delete(synchronize_session=False)

    for asset_data in manifest.get("assets", []):
        node_slug = asset_data.get("node")
        if node_slug not in node_slug_to_id:
            raise LoaderError(f"Asset references unknown node: {node_slug}")

        asset = Asset(
            node_id=node_slug_to_id[node_slug],
            asset_type=asset_data.get("type", "image"),
            path=asset_data.get("path", ""),
            alt_text=asset_data.get("alt", ""),
            metadata_json="{}",
        )
        db.add(asset)

    db.commit()
    db.refresh(graph)
    return graph