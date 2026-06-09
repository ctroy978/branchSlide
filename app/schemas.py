from pydantic import BaseModel


class BranchChoice(BaseModel):
    id: int
    label: str
    to_slug: str


class NodeState(BaseModel):
    slug: str
    title: str
    html_content: str
    node_type: str


class SessionState(BaseModel):
    session_id: str
    graph_slug: str
    graph_title: str
    node: NodeState
    branches: list[BranchChoice]


class BranchSelectRequest(BaseModel):
    branch_id: int


class LoadMapRequest(BaseModel):
    path: str


class GraphSummary(BaseModel):
    slug: str
    title: str
    description: str