# BranchSlide

A generic, teacher-controlled branching inquiry system. Teachers navigate ethical, literary, or philosophical inquiry maps while students follow along on a live projector view.

## Tech Stack

- FastAPI + Uvicorn
- SQLite + SQLAlchemy
- Jinja2 + HTMX
- PyYAML
- Tailwind CSS (CDN)
- WebSocket live sync

## Quick Start

```bash
# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Load the example map
python scripts/load_inquiry_map.py maps/example-inquiry

# Start the server
uvicorn app.main:app --reload
```

Open **http://localhost:8000** to see available maps.

## Classroom Flow

1. Open the **Teacher Panel** for a map (auto-creates a session)
2. Copy the **Projector URL** shown on the teacher page
3. Open the projector URL on a second screen or projector
4. Click branch choices on the teacher panel — the projector updates live via WebSocket

## Loading Maps

### CLI

```bash
python scripts/load_inquiry_map.py maps/example-inquiry
```

### Admin API

```bash
curl -X POST http://localhost:8000/api/admin/load \
  -H "Content-Type: application/json" \
  -d '{"path": "maps/example-inquiry"}'
```

## Creating a New Map

Create a folder under `maps/` with this structure:

```
maps/my-inquiry/
├── manifest.yaml
├── nodes/
│   └── *.md
└── assets/          # optional images, audio, etc.
```

See `maps/example-inquiry/manifest.yaml` for the format.

## API Overview

| Endpoint | Purpose |
|----------|---------|
| `GET /` | List loaded graphs |
| `GET /g/{slug}/teacher` | Teacher control panel |
| `GET /g/{slug}/projector?session={id}` | Projector view |
| `POST /api/g/{slug}/sessions` | Create session |
| `POST /api/g/{slug}/sessions/{id}/branch` | Select branch |
| `POST /api/g/{slug}/sessions/{id}/reset` | Return to start |
| `POST /api/admin/load` | Load map from disk |
| `WS /ws/g/{slug}/sessions/{id}` | Live updates |