import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MAPS_DIR = BASE_DIR / "maps"
DATABASE_URL = f"sqlite:///{DATA_DIR / 'branchslide.db'}"

TEACHER_PORT = int(os.getenv("PORT", os.getenv("BRANCHSLIDE_TEACHER_PORT", "8000")))
PROJECTOR_PORT = int(os.getenv("BRANCHSLIDE_PROJECTOR_PORT", "8001"))

# Optional override for share links (e.g. http://192.168.1.50:8000)
PUBLIC_BASE_URL = os.getenv("BRANCHSLIDE_PUBLIC_URL", "").rstrip("/")
PROJECTOR_PUBLIC_URL = os.getenv("BRANCHSLIDE_PROJECTOR_PUBLIC_URL", "").rstrip("/")

# Comma-separated origins, or "*" to allow any (classroom / LAN use)
CORS_ORIGINS = os.getenv("BRANCHSLIDE_CORS_ORIGINS", "*")

# Asset pipeline — folder layout: maps/{slug}/assets/
ASSET_FOLDER_PREFIX = "assets/"
ASSET_MAX_BYTES = int(os.getenv("BRANCHSLIDE_ASSET_MAX_BYTES", str(5 * 1024 * 1024)))

ALLOWED_NODE_TYPES = frozenset({"content", "synthesis"})
SUPPORTED_ASSET_TYPES: dict[str, frozenset[str]] = {
    "image": frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}),
    "audio": frozenset({".mp3", ".wav", ".ogg", ".m4a", ".aac"}),
}
