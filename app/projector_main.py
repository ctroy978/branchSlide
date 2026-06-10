from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, CORS_ORIGINS, MAPS_DIR
from app.database import init_db
from app.routers import projector_api, projector_pages, websocket

projector_app = FastAPI(title="BranchSlide Projector", description="Student projector display")

cors_origins = ["*"] if CORS_ORIGINS == "*" else [
    origin.strip() for origin in CORS_ORIGINS.split(",") if origin.strip()
]
projector_app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

projector_app.include_router(projector_pages.router)
projector_app.include_router(projector_api.router)
projector_app.include_router(websocket.router)

static_path = BASE_DIR / "app" / "static"
static_path.mkdir(parents=True, exist_ok=True)
projector_app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

maps_path = Path(MAPS_DIR)
maps_path.mkdir(parents=True, exist_ok=True)
projector_app.mount("/map-assets", StaticFiles(directory=str(maps_path)), name="map-assets")


@projector_app.on_event("startup")
def on_startup() -> None:
    init_db()