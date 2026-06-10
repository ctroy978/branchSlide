from collections import deque
from dataclasses import dataclass
from pathlib import Path

import yaml

from app.config import (
    ALLOWED_NODE_LAYOUTS,
    ALLOWED_NODE_TYPES,
    ASSET_FOLDER_PREFIX,
    ASSET_MAX_BYTES,
    BASE_DIR,
    SUPPORTED_ASSET_TYPES,
)


@dataclass(frozen=True)
class ValidationIssue:
    severity: str  # "error" | "warning"
    code: str
    message: str
    path: str = ""


class MapValidationError(Exception):
    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        errors = [issue for issue in issues if issue.severity == "error"]
        messages = "\n".join(f"- {issue.message}" for issue in errors)
        super().__init__(messages or "Map validation failed")


def resolve_map_dir(map_path: str | Path) -> Path:
    path = Path(map_path)
    if not path.is_absolute():
        path = BASE_DIR / path
    path = path.resolve()
    if not path.is_dir():
        raise MapValidationError(
            [ValidationIssue("error", "map_not_found", f"Map directory not found: {path}")]
        )
    return path


def _load_manifest(map_dir: Path) -> tuple[dict, list[ValidationIssue]]:
    manifest_path = map_dir / "manifest.yaml"
    if not manifest_path.is_file():
        return {}, [
            ValidationIssue("error", "manifest_missing", "manifest.yaml not found", "manifest.yaml")
        ]

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return {}, [
            ValidationIssue(
                "error",
                "manifest_invalid_yaml",
                f"manifest.yaml is not valid YAML: {exc}",
                "manifest.yaml",
            )
        ]

    if not isinstance(manifest, dict):
        return {}, [
            ValidationIssue(
                "error",
                "manifest_invalid_root",
                "manifest.yaml must be a mapping at the top level",
                "manifest.yaml",
            )
        ]

    return manifest, []


def _check_file_exists(map_dir: Path, relative_path: str, field_path: str) -> list[ValidationIssue]:
    if not relative_path:
        return [
            ValidationIssue("error", "file_missing", f"{field_path} is required", field_path)
        ]
    file_path = map_dir / relative_path
    if not file_path.is_file():
        return [
            ValidationIssue(
                "error",
                "file_missing",
                f"File not found: {relative_path}",
                field_path,
            )
        ]
    return []


def _validate_asset_file(
    map_dir: Path, asset_type: str, relative_path: str, field_path: str
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not relative_path:
        issues.append(
            ValidationIssue("error", "asset_path_missing", "Asset path is required", field_path)
        )
        return issues

    if not relative_path.startswith(ASSET_FOLDER_PREFIX):
        issues.append(
            ValidationIssue(
                "warning",
                "asset_path_layout",
                f"Asset path should live under '{ASSET_FOLDER_PREFIX}' (got '{relative_path}')",
                field_path,
            )
        )

    file_path = map_dir / relative_path
    if not file_path.is_file():
        issues.append(
            ValidationIssue(
                "error",
                "asset_file_missing",
                f"Asset file not found: {relative_path}",
                field_path,
            )
        )
        return issues

    allowed_extensions = SUPPORTED_ASSET_TYPES.get(asset_type)
    if allowed_extensions is None:
        issues.append(
            ValidationIssue(
                "warning",
                "asset_type_unsupported",
                f"Asset type '{asset_type}' has no renderer yet — it will be stored but not displayed",
                field_path,
            )
        )
    else:
        suffix = file_path.suffix.lower()
        if suffix not in allowed_extensions:
            issues.append(
                ValidationIssue(
                    "error",
                    "asset_format_unsupported",
                    f"Asset type '{asset_type}' does not support '{suffix}' "
                    f"(allowed: {', '.join(sorted(allowed_extensions))})",
                    field_path,
                )
            )

    size = file_path.stat().st_size
    if size > ASSET_MAX_BYTES:
        issues.append(
            ValidationIssue(
                "error",
                "asset_too_large",
                f"Asset exceeds size limit ({size} > {ASSET_MAX_BYTES} bytes): {relative_path}",
                field_path,
            )
        )

    return issues


def _reachable_node_slugs(entry_slug: str, branches: list[dict], node_slugs: set[str]) -> set[str]:
    adjacency: dict[str, list[str]] = {slug: [] for slug in node_slugs}
    for branch in branches:
        from_slug = branch.get("from")
        to_slug = branch.get("to")
        if from_slug in adjacency and to_slug in node_slugs:
            adjacency[from_slug].append(to_slug)

    visited: set[str] = set()
    queue: deque[str] = deque([entry_slug])
    while queue:
        slug = queue.popleft()
        if slug in visited:
            continue
        visited.add(slug)
        for target in adjacency.get(slug, []):
            if target not in visited:
                queue.append(target)
    return visited


def validate_map(map_path: str | Path) -> list[ValidationIssue]:
    map_dir = resolve_map_dir(map_path)
    manifest, issues = _load_manifest(map_dir)
    if any(issue.severity == "error" for issue in issues):
        return issues

    graph_data = manifest.get("graph")
    if not isinstance(graph_data, dict):
        issues.append(
            ValidationIssue("error", "graph_missing", "graph section is required", "graph")
        )
        return issues

    slug = graph_data.get("slug")
    if not slug or not isinstance(slug, str):
        issues.append(
            ValidationIssue("error", "graph_slug_missing", "graph.slug is required", "graph.slug")
        )
    elif not slug.replace("-", "").isalnum() or slug != slug.lower():
        issues.append(
            ValidationIssue(
                "warning",
                "graph_slug_format",
                f"graph.slug '{slug}' should be lowercase with hyphens only",
                "graph.slug",
            )
        )

    if not graph_data.get("title"):
        issues.append(
            ValidationIssue("error", "graph_title_missing", "graph.title is required", "graph.title")
        )

    entry_slug = graph_data.get("entry_node")
    if not entry_slug:
        issues.append(
            ValidationIssue(
                "error",
                "graph_entry_missing",
                "graph.entry_node is required",
                "graph.entry_node",
            )
        )

    nodes_data = manifest.get("nodes")
    if not isinstance(nodes_data, list) or not nodes_data:
        issues.append(
            ValidationIssue("error", "nodes_missing", "nodes must be a non-empty list", "nodes")
        )
        return issues

    node_slugs: set[str] = set()
    seen_slugs: set[str] = set()
    for index, node_data in enumerate(nodes_data):
        prefix = f"nodes[{index}]"
        if not isinstance(node_data, dict):
            issues.append(
                ValidationIssue("error", "node_invalid", "Each node must be a mapping", prefix)
            )
            continue

        node_slug = node_data.get("slug")
        if not node_slug:
            issues.append(
                ValidationIssue("error", "node_slug_missing", "Node slug is required", f"{prefix}.slug")
            )
            continue

        if node_slug in seen_slugs:
            issues.append(
                ValidationIssue(
                    "error",
                    "node_slug_duplicate",
                    f"Duplicate node slug '{node_slug}'",
                    f"{prefix}.slug",
                )
            )
        seen_slugs.add(node_slug)
        node_slugs.add(node_slug)

        if not node_data.get("title"):
            issues.append(
                ValidationIssue(
                    "error", "node_title_missing", "Node title is required", f"{prefix}.title"
                )
            )

        node_type = node_data.get("type")
        if not node_type:
            issues.append(
                ValidationIssue("error", "node_type_missing", "Node type is required", f"{prefix}.type")
            )
        elif node_type not in ALLOWED_NODE_TYPES:
            issues.append(
                ValidationIssue(
                    "error",
                    "node_type_invalid",
                    f"Unknown node type '{node_type}' (allowed: {', '.join(sorted(ALLOWED_NODE_TYPES))})",
                    f"{prefix}.type",
                )
            )

        layout = node_data.get("layout", "default")
        if layout not in ALLOWED_NODE_LAYOUTS:
            issues.append(
                ValidationIssue(
                    "error",
                    "node_layout_invalid",
                    f"Unknown node layout '{layout}' (allowed: {', '.join(sorted(ALLOWED_NODE_LAYOUTS))})",
                    f"{prefix}.layout",
                )
            )

        content_file = node_data.get("content")
        if layout == "video":
            if content_file:
                issues.extend(_check_file_exists(map_dir, content_file, f"{prefix}.content"))
        else:
            issues.extend(_check_file_exists(map_dir, content_file, f"{prefix}.content"))

        branch_question_file = node_data.get("branch_question")
        if branch_question_file:
            issues.extend(
                _check_file_exists(map_dir, branch_question_file, f"{prefix}.branch_question")
            )

    if entry_slug and entry_slug not in node_slugs:
        issues.append(
            ValidationIssue(
                "error",
                "entry_node_missing",
                f"entry_node '{entry_slug}' not found in nodes",
                "graph.entry_node",
            )
        )

    branches_data = manifest.get("branches", [])
    if not isinstance(branches_data, list):
        issues.append(
            ValidationIssue("error", "branches_invalid", "branches must be a list", "branches")
        )
        branches_data = []

    for index, branch_data in enumerate(branches_data):
        prefix = f"branches[{index}]"
        if not isinstance(branch_data, dict):
            issues.append(
                ValidationIssue("error", "branch_invalid", "Each branch must be a mapping", prefix)
            )
            continue

        from_slug = branch_data.get("from")
        to_slug = branch_data.get("to")
        label = branch_data.get("label")

        if not from_slug:
            issues.append(
                ValidationIssue("error", "branch_from_missing", "Branch from is required", f"{prefix}.from")
            )
        elif from_slug not in node_slugs:
            issues.append(
                ValidationIssue(
                    "error",
                    "branch_from_orphan",
                    f"Branch departs from unknown node '{from_slug}'",
                    f"{prefix}.from",
                )
            )

        if not to_slug:
            issues.append(
                ValidationIssue("error", "branch_to_missing", "Branch to is required", f"{prefix}.to")
            )
        elif to_slug not in node_slugs:
            issues.append(
                ValidationIssue(
                    "error",
                    "branch_to_orphan",
                    f"Branch arrives at unknown node '{to_slug}'",
                    f"{prefix}.to",
                )
            )

        if not label:
            issues.append(
                ValidationIssue(
                    "error", "branch_label_missing", "Branch label is required", f"{prefix}.label"
                )
            )

    if entry_slug and entry_slug in node_slugs and not any(
        issue.code == "branch_from_orphan" for issue in issues
    ):
        reachable = _reachable_node_slugs(entry_slug, branches_data, node_slugs)
        unreachable = node_slugs - reachable
        for node_slug in sorted(unreachable):
            issues.append(
                ValidationIssue(
                    "warning",
                    "node_unreachable",
                    f"Node '{node_slug}' is not reachable from entry_node '{entry_slug}'",
                    f"nodes.{node_slug}",
                )
            )

    assets_data = manifest.get("assets", [])
    if not isinstance(assets_data, list):
        issues.append(
            ValidationIssue("error", "assets_invalid", "assets must be a list", "assets")
        )
        assets_data = []

    nodes_with_video_asset: set[str] = set()

    for index, asset_data in enumerate(assets_data):
        prefix = f"assets[{index}]"
        if not isinstance(asset_data, dict):
            issues.append(
                ValidationIssue("error", "asset_invalid", "Each asset must be a mapping", prefix)
            )
            continue

        node_slug = asset_data.get("node")
        if not node_slug:
            issues.append(
                ValidationIssue("error", "asset_node_missing", "Asset node is required", f"{prefix}.node")
            )
        elif node_slug not in node_slugs:
            issues.append(
                ValidationIssue(
                    "error",
                    "asset_node_orphan",
                    f"Asset references unknown node '{node_slug}'",
                    f"{prefix}.node",
                )
            )

        asset_type = asset_data.get("type", "image")
        asset_path = asset_data.get("path", "")
        issues.extend(_validate_asset_file(map_dir, asset_type, asset_path, f"{prefix}.path"))

        if asset_type == "video" and node_slug in node_slugs:
            nodes_with_video_asset.add(node_slug)

        if asset_type == "video":
            captions_path = asset_data.get("captions", "")
            if captions_path:
                captions_file = map_dir / captions_path
                if not captions_file.is_file():
                    issues.append(
                        ValidationIssue(
                            "error",
                            "captions_file_missing",
                            f"Captions file not found: {captions_path}",
                            f"{prefix}.captions",
                        )
                    )
                elif captions_file.suffix.lower() != ".vtt":
                    issues.append(
                        ValidationIssue(
                            "error",
                            "captions_format_unsupported",
                            "Captions must be a WebVTT file (.vtt)",
                            f"{prefix}.captions",
                        )
                    )

    for node_data in nodes_data:
        if not isinstance(node_data, dict):
            continue
        if node_data.get("layout") != "video":
            continue
        node_slug = node_data.get("slug")
        if node_slug and node_slug not in nodes_with_video_asset:
            issues.append(
                ValidationIssue(
                    "error",
                    "video_layout_missing_asset",
                    f"Node '{node_slug}' uses layout 'video' but has no video asset",
                    f"nodes.{node_slug}.layout",
                )
            )

    return issues


def assert_map_valid(map_path: str | Path) -> None:
    issues = validate_map(map_path)
    errors = [issue for issue in issues if issue.severity == "error"]
    if errors:
        raise MapValidationError(issues)


def format_validation_report(issues: list[ValidationIssue]) -> str:
    lines: list[str] = []
    for issue in issues:
        prefix = "ERROR" if issue.severity == "error" else "WARN"
        location = f" ({issue.path})" if issue.path else ""
        lines.append(f"{prefix}{location}: {issue.message}")
    return "\n".join(lines)