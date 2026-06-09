#!/usr/bin/env python3
"""Load an inquiry map from a manifest directory into SQLite."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal, init_db  # noqa: E402
from app.services.loader import LoaderError, load_inquiry_map  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <map-directory>")
        print(f"Example: {sys.argv[0]} maps/example-inquiry")
        sys.exit(1)

    map_path = sys.argv[1]
    init_db()
    db = SessionLocal()
    try:
        graph = load_inquiry_map(db, map_path)
        print(f"Loaded '{graph.slug}' — {graph.title}")
        print(f"  Entry node id: {graph.entry_node_id}")
        print(f"  Source: {graph.source_path}")
    except LoaderError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()