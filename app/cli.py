import sys

from app.database import SessionLocal, init_db
from app.launcher import main_entry, stop_servers
from app.services.graph import GraphNotFoundError
from app.services.loader import LoaderError
from app.services.maps import MapRemoveError, publish_map, remove_map
from app.services.validation import MapValidationError, format_validation_report, validate_map


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


def remove() -> None:
    """Remove a map from the database."""
    delete_files = "--delete-files" in sys.argv
    force = "--force" in sys.argv
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    if len(args) != 1:
        print("Usage: uv run remove <slug> [--delete-files] [--force]")
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