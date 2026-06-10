import socket
import subprocess
from urllib.parse import urlparse, urlunparse

from fastapi import Request

from app.config import PROJECTOR_PORT, PROJECTOR_PUBLIC_URL, PUBLIC_BASE_URL, TEACHER_PORT

# Bind/wildcard hosts — not usable on another machine's browser.
_NON_ROUTABLE_HOSTS = frozenset(
    {"localhost", "127.0.0.1", "0.0.0.0", "::", "[::]", "::1", "[::1]"}
)


def get_lan_ip() -> str | None:
    """Best-effort local network IP for sharing URLs across machines."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        pass

    try:
        output = subprocess.check_output(
            ["ip", "-4", "route", "get", "1.1.1.1"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        parts = output.split()
        if "src" in parts:
            return parts[parts.index("src") + 1]
    except (OSError, subprocess.CalledProcessError, IndexError, ValueError):
        pass

    return None


def _needs_lan_fallback(host: str) -> bool:
    return host in _NON_ROUTABLE_HOSTS


def resolve_share_host(request: Request) -> tuple[str, bool]:
    """Return (hostname for share URLs, used_lan_fallback)."""
    if PUBLIC_BASE_URL:
        parsed = urlparse(PUBLIC_BASE_URL)
        return parsed.hostname or "localhost", False

    host = request.url.hostname or "localhost"
    if _needs_lan_fallback(host):
        lan_ip = get_lan_ip()
        if lan_ip:
            return lan_ip, True
        if host == "0.0.0.0":
            return "localhost", False

    return host, False


def _with_port(base_url: str, port: int) -> str:
    parsed = urlparse(base_url)
    host = parsed.hostname or "localhost"
    return urlunparse(parsed._replace(netloc=f"{host}:{port}"))


def build_public_base_url(request: Request) -> tuple[str, bool]:
    """Return (base_url, used_lan_fallback) for the teacher app."""
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL, False

    host, used_fallback = resolve_share_host(request)
    port = request.url.port
    scheme = request.url.scheme
    port_suffix = f":{port}" if port else ""
    return f"{scheme}://{host}{port_suffix}", used_fallback


def build_teacher_base_url(request: Request) -> tuple[str, bool]:
    """Return the teacher app URL for live sync from the projector app (port 8001 → 8000)."""
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL, False

    host, used_fallback = resolve_share_host(request)
    scheme = request.url.scheme
    return f"{scheme}://{host}:{TEACHER_PORT}", used_fallback


def build_projector_base_url(request: Request) -> tuple[str, bool]:
    """Return (base_url, used_lan_fallback) for the projector app."""
    if PROJECTOR_PUBLIC_URL:
        return PROJECTOR_PUBLIC_URL, False

    teacher_base, used_fallback = build_public_base_url(request)
    return _with_port(teacher_base, PROJECTOR_PORT), used_fallback


def build_projector_url(request: Request, join_code: str) -> tuple[str, bool]:
    base, used_fallback = build_projector_base_url(request)
    return f"{base}/{join_code}", used_fallback