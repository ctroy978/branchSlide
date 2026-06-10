import socket
from urllib.parse import urlparse, urlunparse

from fastapi import Request

from app.config import PROJECTOR_PORT, PROJECTOR_PUBLIC_URL, PUBLIC_BASE_URL


def get_lan_ip() -> str | None:
    """Best-effort local network IP for sharing URLs across machines."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


def _with_port(base_url: str, port: int) -> str:
    parsed = urlparse(base_url)
    host = parsed.hostname or "localhost"
    return urlunparse(parsed._replace(netloc=f"{host}:{port}"))


def build_public_base_url(request: Request) -> tuple[str, bool]:
    """Return (base_url, used_lan_fallback) for the teacher app."""
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL, False

    host = request.url.hostname or "localhost"
    port = request.url.port
    scheme = request.url.scheme
    port_suffix = f":{port}" if port else ""

    if host in {"localhost", "127.0.0.1"}:
        lan_ip = get_lan_ip()
        if lan_ip:
            return f"{scheme}://{lan_ip}{port_suffix}", True

    return f"{scheme}://{host}{port_suffix}", False


def build_projector_base_url(request: Request) -> tuple[str, bool]:
    """Return (base_url, used_lan_fallback) for the projector app."""
    if PROJECTOR_PUBLIC_URL:
        return PROJECTOR_PUBLIC_URL, False

    teacher_base, used_fallback = build_public_base_url(request)
    return _with_port(teacher_base, PROJECTOR_PORT), used_fallback


def build_projector_url(request: Request, join_code: str) -> tuple[str, bool]:
    base, used_fallback = build_projector_base_url(request)
    return f"{base}/{join_code}", used_fallback