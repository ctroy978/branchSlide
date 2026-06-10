import json
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.graph import GraphNotFoundError
from app.services.session import SessionNotFoundError, get_session_state, get_session_state_by_join_code

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[session_id].append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        connections = self._connections.get(session_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections and session_id in self._connections:
            del self._connections[session_id]

    async def broadcast(self, session_id: str, message: dict) -> None:
        payload = json.dumps(message)
        dead: list[WebSocket] = []
        for websocket in self._connections.get(session_id, []):
            try:
                await websocket.send_text(payload)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(session_id, websocket)


manager = ConnectionManager()


@router.websocket("/ws/g/{graph_slug}/sessions/{session_id}")
async def session_ws(graph_slug: str, session_id: str, websocket: WebSocket) -> None:
    db: Session = SessionLocal()
    try:
        state = get_session_state(db, graph_slug, session_id)
    except (GraphNotFoundError, SessionNotFoundError):
        await websocket.close(code=4404)
        return
    finally:
        db.close()

    await manager.connect(session_id, websocket)
    try:
        await websocket.send_text(
            json.dumps({"type": "node_changed", "state": state.model_dump()})
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)


@router.websocket("/ws/{join_code}")
async def join_code_ws(join_code: str, websocket: WebSocket) -> None:
    db: Session = SessionLocal()
    try:
        state = get_session_state_by_join_code(db, join_code)
    except SessionNotFoundError:
        await websocket.close(code=4404)
        return
    finally:
        db.close()

    session_id = state.session_id
    await manager.connect(session_id, websocket)
    try:
        await websocket.send_text(
            json.dumps({"type": "node_changed", "state": state.model_dump()})
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)


async def broadcast_session_state(session_id: str, state: dict) -> None:
    await manager.broadcast(
        session_id,
        {"type": "node_changed", "state": state},
    )