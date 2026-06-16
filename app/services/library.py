import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import yaml
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import BASE_DIR, LIBRARY_DIR, LIBRARY_MAX_BYTES, MAPS_DIR
from app.models import Graph
from app.services.graph import list_graphs
from app.services.loader import LoaderError
from app.services.maps import MapRemoveError, publish_map, remove_map
from app.services.validation import ValidationIssue, validate_map

SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


class LibraryError(Exception):
    pass


@dataclass(frozen=True)
class ZipLayout:
    extract_to: Path
    map_dir: Path


def ensure_library_dir() -> Path:
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    return LIBRARY_DIR


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    if not name.lower().endswith(".zip"):
        raise LibraryError("Only .zip files are supported")
    stem = name[:-4]
    stem = SAFE_FILENAME_RE.sub("-", stem).strip("-")
    if not stem:
        raise LibraryError("Invalid filename")
    return f"{stem}.zip"


def resolve_library_zip(filename: str) -> Path:
    safe_name = sanitize_filename(filename)
    zip_path = (LIBRARY_DIR / safe_name).resolve()
    if zip_path.parent != LIBRARY_DIR.resolve():
        raise LibraryError("Invalid library path")
    if not zip_path.is_file():
        raise LibraryError(f"Library archive not found: {safe_name}")
    return zip_path


def _installed_slugs(db: Session) -> set[str]:
    return {graph.slug for graph in list_graphs(db)}


def _peek_manifest_from_bytes(content: bytes) -> tuple[str | None, str | None]:
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return None, None
    if not isinstance(data, dict):
        return None, None
    graph = data.get("graph", {})
    if not isinstance(graph, dict):
        return None, None
    slug = graph.get("slug")
    title = graph.get("title")
    return (
        slug if isinstance(slug, str) and slug else None,
        title if isinstance(title, str) and title else None,
    )


def peek_zip_manifest(zip_path: Path) -> tuple[str | None, str | None]:
    with zipfile.ZipFile(zip_path) as zf:
        for name in _manifest_member_names(zf):
            return _peek_manifest_from_bytes(zf.read(name))
    return None, None


def _manifest_member_names(zf: zipfile.ZipFile) -> list[str]:
    names: list[str] = []
    for name in zf.namelist():
        if name.endswith("/"):
            continue
        parts = PurePosixPath(name).parts
        if len(parts) == 2 and parts[1] == "manifest.yaml":
            names.append(name)
        elif len(parts) == 3 and parts[0] == "maps" and parts[2] == "manifest.yaml":
            names.append(name)
    return names


def _detect_zip_layout(zf: zipfile.ZipFile) -> str:
    manifest_names = _manifest_member_names(zf)
    if not manifest_names:
        raise LibraryError(
            "No manifest.yaml found. Zip must contain {slug}/manifest.yaml "
            "or maps/{slug}/manifest.yaml (see HERMES.md)."
        )

    has_maps_prefix = any(
        PurePosixPath(name).parts[0] == "maps" for name in manifest_names
    )
    has_slug_root = any(
        len(PurePosixPath(name).parts) == 2 for name in manifest_names
    )

    if has_maps_prefix and has_slug_root:
        raise LibraryError(
            "Ambiguous zip layout: archive contains both maps/{slug}/ and {slug}/ paths."
        )
    if has_maps_prefix:
        return "base_dir"
    return "maps_dir"


def _safe_extract_member(zf: zipfile.ZipFile, member: zipfile.ZipInfo, target_dir: Path) -> None:
    member_path = PurePosixPath(member.filename)
    if member_path.is_absolute() or ".." in member_path.parts:
        raise LibraryError(f"Unsafe path in zip archive: {member.filename}")

    dest = (target_dir / member.filename).resolve()
    if not str(dest).startswith(str(target_dir.resolve())):
        raise LibraryError(f"Unsafe path in zip archive: {member.filename}")

    if member.is_dir() or member.filename.endswith("/"):
        dest.mkdir(parents=True, exist_ok=True)
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    with zf.open(member) as src, dest.open("wb") as out:
        shutil.copyfileobj(src, out)


def _layout_for_zip(zip_path: Path, extract_parent: Path) -> ZipLayout:
    with zipfile.ZipFile(zip_path) as zf:
        layout = _detect_zip_layout(zf)
        slug, _ = peek_zip_manifest(zip_path)
        if not slug:
            raise LibraryError("Could not read graph.slug from manifest.yaml")

        if layout == "maps_dir":
            return ZipLayout(extract_to=extract_parent, map_dir=extract_parent / slug)
        return ZipLayout(extract_to=extract_parent, map_dir=extract_parent / "maps" / slug)


def extract_zip(zip_path: Path, extract_parent: Path) -> Path:
    layout = _layout_for_zip(zip_path, extract_parent)
    if layout.map_dir.is_dir():
        shutil.rmtree(layout.map_dir)

    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            _safe_extract_member(zf, member, layout.extract_to)

    if not (layout.map_dir / "manifest.yaml").is_file():
        raise LibraryError(f"Extracted map is missing manifest.yaml at {layout.map_dir}")
    return layout.map_dir


async def save_uploaded_zip(upload: UploadFile) -> str:
    ensure_library_dir()
    if not upload.filename:
        raise LibraryError("No filename provided")

    safe_name = sanitize_filename(upload.filename)
    dest = LIBRARY_DIR / safe_name
    if dest.exists():
        stem = safe_name[:-4]
        counter = 1
        while dest.exists():
            dest = LIBRARY_DIR / f"{stem}-{counter}.zip"
            counter += 1
        safe_name = dest.name

    total = 0
    try:
        with dest.open("wb") as out:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > LIBRARY_MAX_BYTES:
                    raise LibraryError(
                        f"Upload exceeds maximum size of {LIBRARY_MAX_BYTES // (1024 * 1024)} MB"
                    )
                out.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise

    if total == 0:
        dest.unlink(missing_ok=True)
        raise LibraryError("Uploaded file is empty")

    return safe_name


def list_library_entries(db: Session) -> list[dict]:
    ensure_library_dir()
    installed = _installed_slugs(db)
    entries: list[dict] = []

    for zip_path in sorted(LIBRARY_DIR.glob("*.zip")):
        slug, title = peek_zip_manifest(zip_path)
        entries.append(
            {
                "filename": zip_path.name,
                "slug": slug,
                "title": title,
                "file_size": zip_path.stat().st_size,
                "installed": slug in installed if slug else False,
                "installed_slug": slug if slug and slug in installed else None,
            }
        )

    return entries


def validate_library_zip(filename: str) -> list[ValidationIssue]:
    zip_path = resolve_library_zip(filename)
    with tempfile.TemporaryDirectory(prefix="branchslide-validate-", dir=BASE_DIR / "data") as tmp:
        map_dir = extract_zip(zip_path, Path(tmp))
        return validate_map(map_dir)


def install_library_zip(db: Session, filename: str) -> tuple[Graph, list[ValidationIssue]]:
    zip_path = resolve_library_zip(filename)
    slug, _ = peek_zip_manifest(zip_path)
    if not slug:
        raise LibraryError("Could not read graph.slug from manifest.yaml")

    with zipfile.ZipFile(zip_path) as zf:
        layout = _detect_zip_layout(zf)

    extract_parent = MAPS_DIR if layout == "maps_dir" else BASE_DIR
    map_dir = extract_zip(zip_path, extract_parent)

    issues = validate_map(map_dir)
    errors = [issue for issue in issues if issue.severity == "error"]
    if errors:
        raise LibraryError(
            "Validation failed after extract. Fix the archive and try again.\n"
            + "\n".join(f"- {issue.message}" for issue in errors)
        )

    try:
        graph = publish_map(db, map_dir)
    except LoaderError as exc:
        raise LibraryError(str(exc)) from exc

    warnings = [issue for issue in issues if issue.severity == "warning"]
    return graph, warnings


def uninstall_installed_map(
    db: Session,
    graph_slug: str,
    *,
    force: bool = False,
) -> None:
    try:
        remove_map(db, graph_slug, delete_files=True, force=force)
    except MapRemoveError as exc:
        raise LibraryError(str(exc)) from exc


def delete_library_zip(
    db: Session,
    filename: str,
    *,
    force: bool = False,
) -> None:
    zip_path = resolve_library_zip(filename)
    slug, _ = peek_zip_manifest(zip_path)
    if slug and slug in _installed_slugs(db) and not force:
        raise LibraryError(
            f"Map '{slug}' is still installed. Uninstall it first or use force=true."
        )
    zip_path.unlink()