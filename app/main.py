from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, MAPS_DIR
from app.database import init_db
from app.routers import admin, api, pages, websocket

app = FastAPI(title="BranchSlide", description="Teacher-controlled branching inquiry system")

app.include_router(pages.router)
app.include_router(api.router)
app.include_router(admin.router)
app.include_router(websocket.router)

maps_path = Path(MAPS_DIR)
maps_path.mkdir(parents=True, exist_ok=True)
app.mount("/map-assets", StaticFiles(directory=str(maps_path)), name="map-assets")


@app.on_event("startup")
def on_startup() -> None:
    init_db()