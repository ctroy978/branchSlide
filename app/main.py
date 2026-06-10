from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, CORS_ORIGINS, MAPS_DIR
from app.database import init_db
from app.routers import admin, api, pages, shutdown, websocket

app = FastAPI(title="BranchSlide", description="Teacher-controlled branching inquiry system")

cors_origins = ["*"] if CORS_ORIGINS == "*" else [
    origin.strip() for origin in CORS_ORIGINS.split(",") if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pages.router)
app.include_router(api.router)
app.include_router(admin.router)
app.include_router(shutdown.router)
app.include_router(websocket.router)

static_path = BASE_DIR / "app" / "static"
static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

maps_path = Path(MAPS_DIR)
maps_path.mkdir(parents=True, exist_ok=True)
app.mount("/map-assets", StaticFiles(directory=str(maps_path)), name="map-assets")


@app.on_event("startup")
def on_startup() -> None:
    init_db()