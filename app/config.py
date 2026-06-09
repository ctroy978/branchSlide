from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MAPS_DIR = BASE_DIR / "maps"
DATABASE_URL = f"sqlite:///{DATA_DIR / 'branchslide.db'}"
