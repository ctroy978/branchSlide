# Hermes — build a BranchSlide presentation

You are authoring a **branching classroom presentation** for BranchSlide. Your deliverable is a **folder of files** under `maps/{slug}/` — not a slide deck file, not database content, not HTML.

**Start here:** copy `maps/_template/` to `maps/{your-slug}/`, then replace every placeholder.

**Reference example:** `maps/example-inquiry/` (working map with text, image, audio, and a video-only node).

**Human docs:** `README.md` (full slot reference).

---

## Headless agent setup

If you are **not** already inside the BranchSlide repository (e.g. you run on a remote server), do this first:

1. **Clone the repo**
   ```bash
   git clone https://github.com/ctroy978/branchSlide.git
   cd branchSlide
   ```
2. **Read this file** (`HERMES.md`) and skim `maps/example-inquiry/` for a working manifest.
3. **Copy the template** (do not ask the teacher to send it):
   ```bash
   cp -r maps/_template maps/{your-slug}/
   ```
4. **Install tooling** (for validate/publish on the build server):
   ```bash
   uv sync
   ```

The teacher does **not** need to attach template files or paste YAML by hand. Your inputs are the lesson brief (topic, branches, text vs media) and this document.

---

## How BranchSlide works (read this first)

BranchSlide is a **directed graph** of slides (**nodes**) connected by **branches** (teacher choices).

| Role | What happens |
|------|----------------|
| **Teacher** | Private control panel on port 8000. Clicks branches, triggers media, shows discussion sub-slides. |
| **Projector** | Public display on port 8001. Students watch; they never click branches. |
| **You (author)** | Write the graph as files. Media stays on disk in `assets/`. |

### One node = one classroom beat

Each node can show up to **two screens**:

1. **Main slide** — Markdown body + optional assets (image, audio, video).
2. **Branch-question sub-slide** (optional) — discussion prompt before the teacher picks a path. You write the question; the app lists branch options automatically.

Then the teacher selects a **branch** → projector jumps to the next node's main slide.

Typical rhythm at a branch point:

```
Main slide → class discusses → branch-question sub-slide → class discusses options → teacher picks branch → next node
```

### Media strategy (important)

| Need | What to build |
|------|----------------|
| Text the class reads | `layout: default` node + `nodes/{slug}.md` |
| Static diagram | `type: image` asset on that node |
| Short sound only | `type: audio` asset (teacher hits Play) |
| Synced narration + visuals + captions | **Separate node** with `layout: video` + one `type: video` asset + `.vtt` captions |

**Do not** put video on the same slide as long markdown — use a **video-only node** so formatting stays clean.

**Do not** build timeline/sync engines in YAML. One MP4 per performed segment.

---

## Your deliverable: folder layout

```
maps/{graph.slug}/
├── manifest.yaml          # graph + nodes + branches + assets (single source of truth)
├── nodes/
│   ├── {slug}.md          # main slide text
│   ├── {slug}-question.md # optional branch-question (only at branch points)
│   └── ...
└── assets/
    ├── diagram.svg
    ├── clip.mp4           # video files live here (not in DB)
    └── clip.vtt           # WebVTT captions for hearing accessibility
```

---

## Step-by-step workflow

### Step 1 — Plan the graph (before writing files)

1. List every **beat** (one node each).
2. Mark **branch points** (2+ outgoing branches).
3. Sketch links: `from → to` with meaningful labels.
4. Mark which beats are **text** vs **video-only**.
5. Choose `graph.slug` (lowercase, hyphens, never renamed after publish).

### Step 2 — Write `manifest.yaml`

Four sections in order: `graph`, `nodes`, `branches`, `assets`.

#### `graph`

```yaml
graph:
  slug: my-lesson
  title: "Title teachers see in the catalog"
  description: "One-sentence summary"
  entry_node: opening
```

#### `nodes`

| Field | Required | Purpose |
|-------|----------|---------|
| `slug` | yes | Stable id; referenced by `branches` |
| `title` | yes | Projector heading (hidden on `layout: video`) |
| `type` | yes | `content` (most nodes) or `synthesis` (closing) |
| `layout` | no | `default` or `video` |
| `content` | yes* | Path to main-slide `.md` (*omit path only if `layout: video` and no stub file) |
| `branch_question` | no | Path to discussion sub-slide `.md` |

**Text slide:**

```yaml
  - slug: opening
    title: "The Question"
    type: content
    layout: default
    content: nodes/opening.md
    branch_question: nodes/opening-question.md
```

**Video-only slide** (projector shows only the video):

```yaml
  - slug: opening-clip
    title: "Opening segment"
    type: content
    layout: video
    content: nodes/opening-clip.md
```

Pair with **one** `type: video` asset on this node. No images or audio on `layout: video` nodes.

#### `branches`

```yaml
branches:
  - from: opening
    to: path-a
    label: "Explore the first argument"
    student_label: "Optional longer text on the branch-question sub-slide"
```

- `from` and `to` must match node `slug` values.
- Manifest order = button order on the teacher panel.
- Loops and converging paths are allowed.

#### `assets`

```yaml
assets:
  - node: opening
    type: image
    path: assets/diagram.svg
    alt: "Accessible description"
  - node: opening-clip
    type: video
    path: assets/opening.mp4
    captions: assets/opening-clip.vtt
    alt: "Opening narration with captions"
  - node: opening
    type: audio
    path: assets/chime.wav
    alt: "Transition tone"
```

| `type` | Formats | Notes |
|--------|---------|-------|
| `image` | `.png`, `.jpg`, `.svg`, `.webp`, … | Inline below markdown |
| `audio` | `.mp3`, `.wav`, `.ogg`, … | Teacher play / pause / stop |
| `video` | `.mp4`, `.webm`, `.m4v` | Use with `layout: video` for full-screen |

- **50 MB** max per file (default).
- Optional `autoplay: true` on audio/video (teacher-triggered by default).
- Optional `sort_order: 0` to control asset order on text slides.

### Step 3 — Write Markdown files

**Main slide** (`nodes/{slug}.md`):

- Short projector text; one beat per file.
- Manifest `title` is already the big heading — avoid repeating unless intentional.
- Use `>` for block quotations.

**Branch-question** (`nodes/{slug}-question.md`):

- Open question only. **Never list branch options** — the app adds them.
- Required when the node has 2+ outgoing branches and the class should deliberate.

**Video stub** (`nodes/{slug}.md` on a video node):

```markdown
<!-- video-only -->
```

### Step 4 — Add media files

Place binaries in `assets/`. Every `path` and `captions` in the manifest must exist on disk before publish.

### Step 5 — Validate

```bash
uv run validate maps/my-lesson
```

Fix every **error** before delivery. Warnings should be reviewed.

**Publish** (`uv run publish maps/my-lesson`) is usually run on the **classroom machine** after the map folder is copied there — see [Deliverable packaging](#deliverable-packaging) below.

### Step 6 — Package for the classroom machine

The teacher copies the finished map to the laptop that runs BranchSlide in class. **Create a zip** after validation passes.

**Use this zip layout** (top level is the slug folder — **not** `maps/`):

```bash
mkdir -p deliverables
(cd maps && zip -r ../deliverables/my-lesson.zip my-lesson/)
```

Check with `unzip -l deliverables/my-lesson.zip` — paths must look like `my-lesson/manifest.yaml`, **not** `maps/my-lesson/manifest.yaml`.

Deliver **`deliverables/my-lesson.zip`** (or the whole `maps/my-lesson/` folder).

**On the classroom machine** (from the BranchSlide repo root):

```bash
unzip ~/Downloads/my-lesson.zip -d maps/
uv run validate maps/my-lesson
uv run publish maps/my-lesson
uv run main
```

**If the zip already contains a `maps/` prefix** (Hermes ran `zip -r … maps/my-lesson/` from the repo root), unzip to the repo root instead — **not** into `maps/`:

```bash
unzip ~/Downloads/my-lesson.zip -d .    # yields maps/my-lesson/ correctly
```

Wrong: `unzip … -d maps/` when the archive paths start with `maps/` → creates `maps/maps/my-lesson/` and publish fails.

| Delivery method | Best for |
|-----------------|----------|
| **Zip** (`deliverables/{slug}.zip`) | Default — works for text and media; no git required on the classroom laptop |
| **Git push / PR** | Text-only maps when both machines use the same repo |
| **rsync / scp** | Large video files you do not want in git |

Do not assume `publish` on the build server makes the map visible in class — publishing updates the database on **that** machine only.

### Step 7 — Remove (when replacing a map)

```bash
uv run remove my-lesson                  # database only
uv run remove my-lesson --delete-files   # database + maps/my-lesson/ folder
uv run remove my-lesson --force          # allow removal during active class
```

---

## Pre-publish checklist

- [ ] `graph.slug`, `title`, `entry_node` set
- [ ] Every branch `from` / `to` references an existing node `slug`
- [ ] Every `content` and `branch_question` file exists
- [ ] Every asset file (and `.vtt` if declared) exists
- [ ] Branch points with 2+ exits have a `branch_question` file
- [ ] Each `layout: video` node has exactly one video asset
- [ ] Video nodes are separate from heavy text nodes
- [ ] Slugs are lowercase with hyphens

---

## Example graph

```
opening (text) ──→ opening-clip (video) ──→ path-a (text) ──┐
     │                                                      ├──→ synthesis
     └──────────────────────────→ path-b (text) ──────────┘
```

See `maps/example-inquiry/manifest.yaml` for a real manifest.

---

## Do not

- Put images, audio, or video bytes inside YAML
- Sync separate audio + image with timers — use **video**
- Let students click branches — teacher only
- Rename slugs after a map is published
- Commit huge video files to git without intent (files belong in `maps/…/assets/` on the server)

---

## Quick commands

| Task | Command |
|------|---------|
| Clone repo | `git clone https://github.com/ctroy978/branchSlide.git` |
| Validate | `uv run validate maps/{slug}` |
| Zip for classroom | `(cd maps && zip -r ../deliverables/{slug}.zip {slug}/)` — top level `{slug}/`, not `maps/{slug}/` |
| Publish (classroom) | `uv run publish maps/{slug}` |
| Run class | `uv run main` |
| Teacher URL | `http://localhost:8000/g/{slug}/teacher` |
| Template | `maps/_template/` |