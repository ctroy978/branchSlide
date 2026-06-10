You are an expert full-stack Python developer building educational tools with FastAPI. I want you to create a proof-of-concept for a **generic, reusable Teacher-Controlled Branching Inquiry System**.

**Goal**
Build the core framework that can host many different branching philosophical/literary inquiry maps. The teacher must stay in complete control at every branch point. The same codebase must work for any map we create in the future.

**Working Directory**
`/home/Work/branchSlide'

**Required Tech Stack**
- FastAPI + Uvicorn
- SQLite
- Jinja2 + HTMX
- PyYAML
- Tailwind via CDN
- WebSocket support for live updates

**Core Requirements (must be generic)**
- Support multiple independent graphs/presentations in one database.
- Tables: graphs, nodes, branches, assets, sessions.
- Content is loaded from files (manifest.yaml + Markdown files + assets folder), not hardcoded.
- All routes and logic must be parameterized by `graph_slug` — nothing should be Cicero-specific or map-specific.
- Two views:
  1. Projector view (clean, large text for students)
  2. Teacher control panel (shows current node + live branch choice buttons)
- When the teacher selects a branch, the projector view updates in real time via WebSocket.
- The system must support loops, crossing between paths, and synthesis/end nodes.

**Proof-of-Concept Scope (keep it focused and fast)**
Create a working end-to-end PoC using a **small built-in example map** (you design a simple 6–8 node graph with at least two branch points, one loop, and a synthesis exit). This example map is only for proving the framework works.

Do **not** try to import the full Cicero document in this phase.

Minimum working PoC must allow:
- Loading the example map into SQLite via a `load_inquiry_map.py` script or admin endpoint
- Opening the teacher dashboard and seeing available branch choices
- Clicking a choice and watching the projector view update live
- Basic navigation (forward, loop back, jump to synthesis)

**Future-Proofing (design in now)**
- Make the `assets` system extensible (`type` field: image, audio, video, code, etc.)
- Keep node rendering modular so new content types can be added later without changing core logic
- Support Markdown (including code blocks) from day one

**Deliverables — Strict Order**

1. First, output a clear written plan including:
   - Recommended folder structure
   - Database schema
   - Proposed `manifest.yaml` format (with a small example)
   - API design
   - How real-time updates will work
   - Scope boundaries for this PoC

2. After the plan, implement the PoC:
   - Set up the project with all folders and files
   - Install required packages
   - Create the loader and a small example map
   - Build functional (even if basic) projector and teacher HTML views
   - Implement branch selection with live update
   - Make the whole thing runnable with `uvicorn`

3. End with clear run instructions.

**Important**
Prioritize making the core branching engine, loader pattern, and teacher-control flow clean and generic. Beauty and rich media integration come later. Do not over-scope this proof of concept.