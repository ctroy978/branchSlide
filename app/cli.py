import sys

from app.database import SessionLocal, init_db
from app.launcher import main_entry, stop_servers
from app.services.graph import GraphNotFoundError, list_graphs
from app.services.loader import LoaderError
from app.services.maps import MapRemoveError, publish_map, remove_map
from app.services.validation import MapValidationError, format_validation_report, validate_map

HELP_TEXT = """\
BranchSlide — command reference

  Run class
    uv run main              Start teacher (8000) + projector (8001) servers
    uv run stop              Stop both servers
    uv run dev               Same as main (alias)

  Install a lesson (from repo root)
    unzip lesson.zip -d maps/     If zip paths start with my-lesson/...
    unzip lesson.zip -d .         If zip paths start with maps/my-lesson/...
    uv run validate maps/<slug>   Check manifest and files (no DB write)
    uv run publish maps/<slug>    Validate + load into database

  Manage loaded lessons
    uv run list                Show published slugs and titles
    uv run remove <slug>       Remove from database (keeps maps/<slug>/ folder)
    uv run remove <slug> --delete-files
                               Also delete maps/<slug>/ when under maps/
    uv run remove <slug> --force
                               Remove even if a class session is active

  Other
    uv run help                Show this menu
    uv sync                    Install/update Python deps (first time setup)

  In class
    Teacher:   http://localhost:8000  (not http://0.0.0.0:8000)
    Projector: copy full URL from teacher panel (e.g. http://192.168.x.x:8001/ABCD)

  Typical workflow
    uv run list
    unzip ~/Downloads/my-lesson.zip -d maps/
    uv run validate maps/my-lesson
    uv run publish maps/my-lesson
    uv run main
"""


def help_cmd() -> None:
    """Print BranchSlide CLI command reference."""
    print(HELP_TEXT)


def main() -> None:
    """Start teacher + projector servers for classroom use."""
    main_entry(reload=False)


def dev() -> None:
    """Start teacher + projector servers (no reload — keeps live sync stable)."""
    main_entry(reload=False)


def stop() -> None:
    """Stop teacher + projector servers."""
    stop_servers()


def publish() -> None:
    """Validate and publish a map folder into the database."""
    if len(sys.argv) < 2:
        print("Usage: uv run publish maps/my-lesson")
        print("  See: uv run help")
        sys.exit(1)

    init_db()
    db = SessionLocal()
    try:
        graph = publish_map(db, sys.argv[1])
        print(f"Published '{graph.slug}' — {graph.title}")
        print(f"  Teacher: /g/{graph.slug}/teacher")
        print(f"  Preview: /g/{graph.slug}/preview")
    except LoaderError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


def list_maps() -> None:
    """List inquiry maps loaded in the database."""
    init_db()
    db = SessionLocal()
    try:
        graphs = list_graphs(db)
    finally:
        db.close()

    if not graphs:
        print("No inquiry maps loaded.")
        print("  Publish one: uv run publish maps/my-lesson")
        sys.exit(0)

    slug_width = max(len(graph.slug) for graph in graphs)
    slug_width = max(slug_width, len("slug"))

    print(f"{'slug'.ljust(slug_width)}  title")
    for graph in graphs:
        print(f"{graph.slug.ljust(slug_width)}  {graph.title}")
    print(f"\n{len(graphs)} map(s) loaded.")
    print("  Remove: uv run remove <slug> [--delete-files]")


def remove() -> None:
    """Remove a map from the database."""
    delete_files = "--delete-files" in sys.argv
    force = "--force" in sys.argv
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    if len(args) != 1:
        print("Usage: uv run remove <slug> [--delete-files] [--force]")
        print("  See: uv run help")
        sys.exit(1)

    init_db()
    db = SessionLocal()
    try:
        remove_map(db, args[0], delete_files=delete_files, force=force)
        print(f"Removed map '{args[0]}' from the database.")
        if delete_files:
            print("  Map folder deleted when it was under maps/.")
    except GraphNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except MapRemoveError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


def validate() -> None:
    """Validate a map folder without loading it."""
    if len(sys.argv) < 2:
        print("Usage: uv run validate maps/my-lesson")
        print("  See: uv run help")
        sys.exit(1)

    try:
        issues = validate_map(sys.argv[1])
    except MapValidationError as exc:
        print(format_validation_report(exc.issues), file=sys.stderr)
        sys.exit(1)

    if not issues:
        print(f"OK: {sys.argv[1]}")
        sys.exit(0)

    print(format_validation_report(issues))
    has_errors = any(issue.severity == "error" for issue in issues)
    sys.exit(1 if has_errors else 0)