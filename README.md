# BranchSlide

> **Start the server (remember this):**
> ```bash
> uv run main
> ```
> To stop: click **End service** on the teacher or projector page, or run `uv run stop` (if restart fails with "port already in use", run `uv run stop` first)
> - **Laptop (teacher):** http://localhost:8000 → open the teacher panel (do not use `http://0.0.0.0:8000` — that breaks the projector share URL)
> - **TV computer (projector):** copy the full projector URL from the teacher panel (e.g. `http://192.168.x.x:8001/ABCD`)
>
> First time only: `uv sync` then `uv run publish maps/example-inquiry`
>
> **Future work:** see [ROADMAP.md](ROADMAP.md) — Phase 5 (multi-session scale). Video and audio are implemented.

A generic, teacher-controlled branching inquiry framework. Teachers navigate inquiry maps in real time; students follow on a live projector view. All content is authored in files — nothing is hardcoded per map.

**Building a presentation with Hermes?** Read **[`HERMES.md`](HERMES.md)** first.

This README is the **authoring reference**. Every slot has a name and a defined purpose so humans and AI can create compatible content without reading the application source code.

---

## How the framework works

An **inquiry map** is a directed graph of **nodes** connected by **branches**. During a classroom session:

1. The class sees one **projector view** (large text, clean layout).
2. The teacher uses a private **control panel** with branch buttons.
3. When the teacher selects a branch, the projector updates live via WebSocket.

The teacher stays in control at every step. Students do not click branches.

A single node can expose more than one projector view. The teacher advances through **display phases** within a node before choosing a branch. See [Display phases](#display-phases-within-a-node) below.

---

## Map folder structure

Each inquiry map lives in its own directory under `maps/`:

```
maps/my-inquiry/
├── manifest.yaml       # Graph definition: nodes, branches, assets
├── nodes/              # Markdown files for node content slots
│   ├── opening.md
│   └── opening-question.md
└── assets/             # Optional media files
    └── diagram.png
```

### AI authoring (Hermes)

**Agent prompt:** [`HERMES.md`](HERMES.md) — start here  
**Starter skeleton:** copy `maps/_template/` to `maps/{your-slug}/`

### Publish, validate, remove

```bash
uv run validate maps/my-inquiry    # check manifest + files (no DB write)
uv run publish maps/my-inquiry     # validate + load into database
uv run remove my-inquiry           # remove from database
uv run remove my-inquiry --delete-files   # also delete maps/my-inquiry/
```

Or via the admin API:

```bash
curl -X POST http://localhost:8000/api/admin/validate -H 'Content-Type: application/json' -d '{"path":"maps/my-inquiry"}'
curl -X POST http://localhost:8000/api/admin/load -H 'Content-Type: application/json' -d '{"path":"maps/my-inquiry"}'
curl -X DELETE 'http://localhost:8000/api/admin/maps/my-inquiry?delete_files=true'
```

Media files stay on disk under `assets/` — they are not stored in SQLite.

---

## manifest.yaml — complete slot reference

The manifest is the single source of truth for a map. All slots are listed here.

### Section: `graph`

Identifies the map and sets session entry point.

| Slot | Required | Purpose |
|------|----------|---------|
| `slug` | yes | Unique URL identifier for this map. Used in all routes: `/g/{slug}/teacher`. Lowercase, hyphen-separated. Example: `cicero-balance`. |
| `title` | yes | Human-readable map name. Shown on the index page and projector header. |
| `description` | no | Short summary for the map catalog (index page). Helps teachers choose a map. |
| `entry_node` | yes | `slug` of the node where new sessions begin. |

```yaml
graph:
  slug: example-inquiry
  title: "The Trolley and the Gardener"
  description: "A short ethical branching inquiry for classroom demonstration."
  entry_node: start
```

---

### Section: `nodes`

Each item is one vertex in the inquiry graph.

| Slot | Required | Purpose |
|------|----------|---------|
| `slug` | yes | Unique node identifier within this map. Referenced by branches (`from`, `to`) and `entry_node`. Stable — do not rename after publishing. |
| `title` | yes | Projector heading for this node. Short, display-sized. Shown on both the main slide and the branch-question sub-slide. |
| `type` | yes | Node role in the inquiry arc. Controls styling and teacher expectations. See [Node types](#node-types). |
| `layout` | no | `default` (text + assets below) or `video` (projector shows only the video asset — use for performed clips). |
| `content` | yes* | Path to the **main slide** Markdown file (*optional when `layout: video`). |
| `branch_question` | no | Path to the **branch-question sub-slide** Markdown file. See [Display phases](#display-phases-within-a-node). If omitted, the node has only a main slide. |

```yaml
nodes:
  - slug: start
    title: "The Dilemma"
    type: content
    content: nodes/start.md
    branch_question: nodes/start-question.md   # planned — see status below
```

#### Node types

| Value | Purpose |
|-------|---------|
| `content` | Standard inquiry node. Present material, discuss, branch onward. Most nodes use this. |
| `synthesis` | Closing node. Summarises what the class explored. Typically has few or no outgoing branches. Projector may show a distinct synthesis marker. |

More types may be added later (e.g. `intro`, `checkpoint`). Use only the values listed above unless the README is updated.

---

### Section: `branches`

Each item is a directed edge — one choice the teacher can make at a branch point.

| Slot | Required | Purpose |
|------|----------|---------|
| `from` | yes | `slug` of the node this branch departs from. Must match a node `slug`. |
| `to` | yes | `slug` of the node this branch arrives at. Must match a node `slug`. |
| `label` | yes | Short name for this path. Used on the **teacher control panel** button and, when a `branch_question` sub-slide is shown, listed as a student-visible option. Write it as an explorable path: *"Explore virtue ethics"*, not *"Click here"*. |
| `student_label` | no | Optional alternate text for the **branch-question sub-slide** only. Use when the teacher button needs to be terse but the student listing should be fuller. Falls back to `label` if omitted. *Planned — not yet implemented.* |

```yaml
branches:
  - from: start
    to: virtue-path
    label: "Explore virtue ethics"
  - from: start
    to: consequence-path
    label: "Explore consequentialism"
    student_label: "Follow the consequentialist argument"   # planned
```

Branch list order in the manifest is display order on both the teacher panel and the branch-question sub-slide.

---

### Section: `assets`

Optional media attached to a node. Rendered below the main slide content.

| Slot | Required | Purpose |
|------|----------|---------|
| `node` | yes | `slug` of the node this asset belongs to. |
| `type` | yes | Asset kind. Determines renderer. See [Asset types](#asset-types). |
| `path` | yes | Path relative to map folder. Example: `assets/diagram.png`. |
| `alt` | no | Accessibility text. Recommended for `type: image`; used as the audio label in teacher controls. |
| `autoplay` | no | `audio` / `video`. If `true`, the projector plays when the main slide appears. Default: teacher triggers playback. |
| `captions` | no | `video` only. Path to a WebVTT file (`.vtt`) for closed captions on the projector. |

```yaml
assets:
  - node: start
    type: image
    path: assets/trolley-diagram.png
    alt: "Diagram of the trolley problem with a side track"
  - node: start
    type: audio
    path: assets/opening-tone.wav
    alt: "Opening tone"
  - node: start
    type: video
    path: assets/opening-segment.mp4
    captions: assets/opening-segment.vtt
    alt: "Opening narration with diagram"
```

---

## Display phases within a node

A node is not always a single projector screen. The teacher moves through **phases** before selecting a branch.

| Phase | Slot | Audience | Purpose |
|-------|------|----------|---------|
| **Main slide** | `content` | Students (projector) | Present context, narrative, source text, or argument. Read and discuss. |
| **Branch-question sub-slide** | `branch_question` | Students (projector) | Teacher pushes when ready to open decision to the class. Shows a discussion question and lists the outgoing branch options so students can see what paths are available before the teacher commits. |
| **Branch selection** | `branches` | Teacher only (control panel) | Teacher clicks one outgoing branch. Projector advances to the next node's main slide. |

The teacher can press **Back** at any time to undo a mis-click or revisit a previous slide. On a branch-question sub-slide, Back returns to the main slide on the same node. Otherwise, Back restores the previous node and display phase.

### Typical classroom rhythm at a branch point

```
[Main slide]  →  teacher discusses  →  [Branch-question sub-slide]  →  class discusses options  →  teacher selects branch  →  [Next node main slide]
```

The teacher triggers the sub-slide with a **"Show question"** control (planned). Students never see branch buttons; they see the option names listed on the sub-slide.

### Authoring a `branch_question` file

The `branch_question` Markdown file contains only the **question prompt** — not the branch list. The application appends the outgoing branch labels automatically from the manifest.

**Write the question to invite exploration of the listed paths:**

```markdown
# Which direction should we take?

We have set up the dilemma. Before I choose our path, consider:

- What does each framework offer that the others do not?
- Which approach feels most natural to you right now?

Be ready to defend your preference.
```

**Do not** duplicate the branch labels in this file — the system lists them. **Do** write a question that only makes sense when those branches exist.

Nodes with a single outgoing branch (e.g. a linear "Continue") may omit `branch_question` — there is nothing meaningful to deliberate.

Nodes with no outgoing branches (e.g. `synthesis`) should not have `branch_question`.

---

## Content slots summary

Quick reference for content authors and AI.

| Slot | Location | Purpose |
|------|----------|---------|
| `graph.slug` | manifest | Map URL identifier |
| `graph.title` | manifest | Map display name |
| `graph.description` | manifest | Map catalog blurb |
| `graph.entry_node` | manifest | Session start node |
| `nodes[].slug` | manifest | Node identifier |
| `nodes[].title` | manifest | Node projector heading |
| `nodes[].type` | manifest | Node role (`content`, `synthesis`) |
| `nodes[].content` | manifest → Markdown file | Main slide body |
| `nodes[].branch_question` | manifest → Markdown file | Branch-question sub-slide prompt |
| `branches[].from` | manifest | Departure node |
| `branches[].to` | manifest | Arrival node |
| `branches[].label` | manifest | Teacher button + default student option text |
| `branches[].student_label` | manifest | Optional fuller student option text *(planned)* |
| `assets[].node` | manifest | Owning node |
| `assets[].type` | manifest | Renderer selection |
| `assets[].path` | manifest | File location |
| `assets[].alt` | manifest | Image accessibility text |

---

## Asset types

| Type | Status | Purpose |
|------|--------|---------|
| `image` | implemented | Displayed inline below node content. |
| `audio` | implemented | Audio-only clips. Teacher play / pause / stop; optional `autoplay`. |
| `video` | implemented | **Synced picture + sound** in one MP4; optional WebVTT captions. Teacher play / pause / stop. Files live in `maps/{slug}/assets/` (not in the database). |
| `code` | planned | Syntax-highlighted excerpts. |

**Media strategy:** Use `image` for static visuals, `audio` when sound alone is enough, and `video` when narration must stay in sync with visuals or captions are required. Audio and video are teacher-controlled by default; the projector plays via live sync.

---

## Markdown conventions

Content files (`content` and `branch_question`) are standard Markdown.

- Use `#` for the slide title only if you want a title distinct from `nodes[].title` — the manifest `title` is always shown as the primary projector heading.
- Use `>` for block quotations from source texts.
- Use fenced code blocks for excerpts:

````markdown
```text
Virtue → Character → Habit → Flourishing
```
````

- Keep main slides concise — they are projector text, not essays.
- Keep branch-question prompts short and open-ended.

---

## Authoring guidelines for AI content generation

When generating a new inquiry map, follow this order:

1. **Design the graph** — sketch nodes and branches on paper first. Identify branch points (nodes with 2+ outgoing branches).
2. **Write `graph`** — slug, title, description, entry_node.
3. **Write `nodes`** — one entry per vertex. Every node needs `slug`, `title`, `type`, `content`.
4. **Add `branch_question`** at every node where the class should deliberate between multiple paths. Skip linear nodes and synthesis.
5. **Write `branches`** — every edge. Labels must read as meaningful inquiry paths.
6. **Write Markdown files** — one per `content` slot; one per `branch_question` slot.
7. **Add `assets`** last, only where visual aid helps.

### Rules

- **Slugs are stable identifiers.** Use lowercase and hyphens. Never use map-specific logic in slugs (no `cicero-special-case`).
- **Branch labels are student-facing.** Even though students do not click them, they appear on branch-question sub-slides.
- **Loops are allowed.** A branch may return to an earlier node (e.g. `revisit → start`).
- **Paths may converge.** Multiple branches may target the same `to` node.
- **Synthesis nodes** use `type: synthesis` and typically end the arc.
- **Do not hardcode** map names, author names, or institution details in slugs.

### Minimal branch-point node (template)

```yaml
  - slug: my-branch-point
    title: "A decision"
    type: content
    content: nodes/my-branch-point.md
    branch_question: nodes/my-branch-point-question.md
```

```yaml
branches:
  - from: my-branch-point
    to: path-a
    label: "Explore the first argument"
  - from: my-branch-point
    to: path-b
    label: "Explore the second argument"
```

---

## Implementation status

| Feature | Status |
|---------|--------|
| `graph`, `nodes`, `branches`, `assets` slots | implemented |
| `content` main slide | implemented |
| `branch_question` sub-slide | implemented |
| `branches[].student_label` | implemented |
| Teacher "Show question" / "Back to main slide" controls | implemented |
| Asset type `audio` (teacher controls, optional autoplay) | implemented |
| Asset type `video` (MP4 + optional VTT captions, teacher controls) | implemented |
| Asset type `code` | **planned** |

The example map (`maps/example-inquiry`) includes `branch_question` files at `start` and `crossroads`.

---

## Laptop + TV on separate computers

Yes — this works with what we have. Both machines connect to the **same BranchSlide server** over your local network.

1. Start the server so it accepts LAN connections:
   ```bash
   uv run main
   ```
2. On your **laptop**, open the teacher panel.
3. Copy the **Projector URL** from the teacher page.
4. On the **TV computer**, paste that URL into the browser.

The teacher page auto-replaces `localhost` with your **network IP** so the TV computer can reach your laptop. The projector runs on a separate port with a short 4-character class code. Both computers must be on the same network (or otherwise able to reach the server).

Optional environment variables:

| Variable | Purpose |
|----------|---------|
| `BRANCHSLIDE_PUBLIC_URL` | Force the teacher share URL (e.g. `http://192.168.1.50:8000`) |
| `BRANCHSLIDE_PROJECTOR_PUBLIC_URL` | Force the projector base URL (e.g. `http://192.168.1.50:8001`) |
| `BRANCHSLIDE_PROJECTOR_PORT` | Projector port (default `8001`) |
| `BRANCHSLIDE_CORS_ORIGINS` | CORS allowed origins (default `*` for classroom/LAN use) |

CORS is enabled so API calls work from flexible classroom setups. When both pages are loaded from the same server address, same-origin rules already apply; CORS adds support for cross-origin tooling if needed.

---

## Running the application

Requires [uv](https://docs.astral.sh/uv/). Install it once, then:

```bash
uv sync
uv run python scripts/load_inquiry_map.py maps/example-inquiry
uv run main
```

For local development with auto-reload: `uv run dev`

| URL | Purpose |
|-----|---------|
| `http://localhost:8000/` | Map catalog (teacher machine) |
| `http://localhost:8000/g/{slug}/teacher` | Teacher control panel (auto-creates session) |
| `http://<server-ip>:8001/{code}` | Projector view (TV computer — 4-character class code) |

## API reference

| Method | Route | Purpose |
|--------|-------|---------|
| `GET` | `/` | List loaded graphs |
| `GET` | `/g/{slug}/teacher` | Teacher control panel |
| `GET` | `/g/{slug}/projector?session={id}` | Projector view |
| `POST` | `/api/g/{slug}/sessions` | Create session |
| `GET` | `/api/g/{slug}/sessions/{id}` | Current state |
| `POST` | `/api/g/{slug}/sessions/{id}/branch` | Select branch |
| `POST` | `/api/g/{slug}/sessions/{id}/show-question` | Push branch-question sub-slide to projector |
| `POST` | `/api/g/{slug}/sessions/{id}/show-content` | Return projector to main slide |
| `POST` | `/api/g/{slug}/sessions/{id}/back` | Back to main slide or previous node |
| `POST` | `/api/g/{slug}/sessions/{id}/reset` | Return to entry node |
| `POST` | `/api/admin/load` | Load map from disk |
| `WS` | `/ws/g/{slug}/sessions/{id}` | Live projector sync |

---

## Tech stack

- FastAPI + Uvicorn
- SQLite + SQLAlchemy
- Jinja2 + HTMX
- PyYAML
- Tailwind CSS (CDN)
- WebSocket live sync