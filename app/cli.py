from app.launcher import main_entry, stop_servers


def main() -> None:
    """Start teacher + projector servers for classroom use."""
    main_entry(reload=False)


def dev() -> None:
    """Start teacher + projector servers (no reload — keeps live sync stable)."""
    main_entry(reload=False)


def stop() -> None:
    """Stop teacher + projector servers."""
    stop_servers()