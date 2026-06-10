#!/usr/bin/env python3
"""Validate and load (publish) an inquiry map into BranchSlide."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal, init_db  # noqa: E402
from app.services.loader import LoaderError  # noqa: E402
from app.services.maps import publish_map  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <map-directory>")
        print(f"Example: {sys.argv[0]} maps/my-lesson")
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


if __name__ == "__main__":
    main()