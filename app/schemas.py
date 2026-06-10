from pydantic import BaseModel


class BranchChoice(BaseModel):
    id: int
    label: str
    student_label: str
    to_slug: str


class NodeState(BaseModel):
    slug: str
    title: str
    html_content: str
    node_type: str
    layout: str = "default"


class PlaybackAssetState(BaseModel):
    id: int
    label: str
    kind: str  # audio | video
    autoplay: bool = False


class MediaControlRequest(BaseModel):
    asset_id: int
    action: str  # play | pause | stop


# Backward-compatible aliases
AudioAssetState = PlaybackAssetState
AudioControlRequest = MediaControlRequest


class SessionState(BaseModel):
    session_id: str
    join_code: str
    graph_slug: str
    graph_title: str
    display_phase: str
    has_branch_question: bool
    can_show_question: bool
    can_go_back: bool
    node: NodeState
    branches: list[BranchChoice]
    playback_assets: list[PlaybackAssetState] = []


class BranchSelectRequest(BaseModel):
    branch_id: int


class LoadMapRequest(BaseModel):
    path: str


class GraphSummary(BaseModel):
    slug: str
    title: str
    description: str


class ValidationIssueOut(BaseModel):
    severity: str
    code: str
    message: str
    path: str = ""


class ValidationReport(BaseModel):
    valid: bool
    errors: list[ValidationIssueOut]
    warnings: list[ValidationIssueOut]


class PreviewState(BaseModel):
    graph_slug: str
    graph_title: str
    node_slug: str
    display_phase: str
    has_branch_question: bool
    can_show_question: bool
    can_go_back: bool
    history: str
    node: NodeState
    branches: list[BranchChoice]