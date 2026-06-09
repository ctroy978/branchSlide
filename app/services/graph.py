from sqlalchemy.orm import Session, joinedload

from app.models import Branch, Graph, Node


class GraphNotFoundError(Exception):
    pass


class NodeNotFoundError(Exception):
    pass


def get_graph_by_slug(db: Session, graph_slug: str) -> Graph:
    graph = db.query(Graph).filter(Graph.slug == graph_slug).first()
    if not graph:
        raise GraphNotFoundError(f"Graph '{graph_slug}' not found")
    return graph


def list_graphs(db: Session) -> list[Graph]:
    return db.query(Graph).order_by(Graph.title).all()


def get_node_by_slug(db: Session, graph_id: int, node_slug: str) -> Node:
    node = (
        db.query(Node)
        .options(joinedload(Node.assets))
        .filter(Node.graph_id == graph_id, Node.slug == node_slug)
        .first()
    )
    if not node:
        raise NodeNotFoundError(f"Node '{node_slug}' not found")
    return node


def get_node_with_assets(db: Session, node_id: int) -> Node:
    node = (
        db.query(Node)
        .options(joinedload(Node.assets))
        .filter(Node.id == node_id)
        .first()
    )
    if not node:
        raise NodeNotFoundError(f"Node id {node_id} not found")
    return node


def get_outgoing_branches(db: Session, node_id: int) -> list[Branch]:
    return (
        db.query(Branch)
        .options(joinedload(Branch.to_node))
        .filter(Branch.from_node_id == node_id)
        .order_by(Branch.sort_order, Branch.id)
        .all()
    )