import asyncio
import re
import signal
import socket
import subprocess
import sys

import uvicorn

from app.config import PROJECTOR_PORT, TEACHER_PORT
from app.database import init_db
from app.shutdown import register_shutdown


class PortInUseError(Exception):
    def __init__(self, ports: list[int]) -> None:
        self.ports = ports
        port_list = ", ".join(str(port) for port in ports)
        super().__init__(
            f"Port(s) already in use: {port_list}. "
            "Another BranchSlide instance may still be running — try: uv run stop"
        )


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", port))
        except OSError:
            return True
    return False


def _check_ports() -> None:
    busy = [port for port in (TEACHER_PORT, PROJECTOR_PORT) if _port_in_use(port)]
    if busy:
        raise PortInUseError(busy)


def _find_listener_pids(port: int) -> list[int]:
    try:
        output = subprocess.check_output(
            ["ss", "-tlnp"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    pids: list[int] = []
    for line in output.splitlines():
        if f":{port}" not in line:
            continue
        pids.extend(int(match.group(1)) for match in re.finditer(r"pid=(\d+)", line))
    return pids


def stop_servers() -> None:
    """Stop any process listening on the teacher and projector ports."""
    pids = {
        pid
        for port in (TEACHER_PORT, PROJECTOR_PORT)
        for pid in _find_listener_pids(port)
    }
    if not pids:
        print("BranchSlide is not running.")
        return

    for pid in pids:
        try:
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            signal.signal(signal.SIGINT, signal.SIG_DFL)
        except ValueError:
            pass
        try:
            import os

            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue

    print(f"Stopped BranchSlide ({len(pids)} process(es)).")
    print(f"  Teacher port {TEACHER_PORT}, projector port {PROJECTOR_PORT}")


async def run_servers(*, reload: bool = False) -> None:
    _check_ports()
    init_db()

    teacher = uvicorn.Server(
        uvicorn.Config(
            "app.main:app",
            host="0.0.0.0",
            port=TEACHER_PORT,
            reload=reload,
        )
    )
    projector = uvicorn.Server(
        uvicorn.Config(
            "app.projector_main:projector_app",
            host="0.0.0.0",
            port=PROJECTOR_PORT,
            reload=False,
        )
    )

    loop = asyncio.get_running_loop()

    def request_shutdown() -> None:
        teacher.should_exit = True
        projector.should_exit = True

    register_shutdown(request_shutdown)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, request_shutdown)
        except NotImplementedError:
            pass

    await asyncio.gather(teacher.serve(), projector.serve())


def main_entry(*, reload: bool = False) -> None:
    try:
        asyncio.run(run_servers(reload=reload))
    except PortInUseError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass