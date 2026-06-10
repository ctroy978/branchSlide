#!/usr/bin/env python3
"""Remove an inquiry map from the database (and optionally delete its files)."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal, init_db  # noqa: E402
from app.services.graph import GraphNotFoundError  # noqa: E402
from app.services.maps import MapRemoveError, remove_map  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove a map from BranchSlide")
    parser.add_argument("slug", help="Map slug (graph.slug from manifest.yaml)")
    parser.add_argument(
        "--delete-files",
        action="store_true",
        help="Also delete the map folder under maps/ (only if it lives there)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove even when active classroom sessions exist",
    )
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        remove_map(
            db,
            args.slug,
            delete_files=args.delete_files,
            force=args.force,
        )
        print(f"Removed map '{args.slug}' from the database.")
        if args.delete_files:
            print("  Map folder deleted when it was under maps/.")
    except GraphNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except MapRemoveError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()