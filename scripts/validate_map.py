#!/usr/bin/env python3
"""Validate an inquiry map manifest without loading it into the database."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.validation import MapValidationError, format_validation_report, validate_map  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <map-directory>")
        print(f"Example: {sys.argv[0]} maps/example-inquiry")
        sys.exit(1)

    map_path = sys.argv[1]
    try:
        issues = validate_map(map_path)
    except MapValidationError as exc:
        print(format_validation_report(exc.issues), file=sys.stderr)
        sys.exit(1)

    if not issues:
        print(f"OK: {map_path}")
        sys.exit(0)

    print(format_validation_report(issues))
    has_errors = any(issue.severity == "error" for issue in issues)
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()