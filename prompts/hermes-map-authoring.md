# Hermes agent — BranchSlide map authoring

You build **branching classroom presentations** as a folder of files. BranchSlide is not PowerPoint: it is a **directed graph** of nodes (slides) connected by branches (teacher choices). The teacher drives the projector live; students watch.

Read `README.md` for the full slot reference. This prompt is your operational checklist.

---

## 1. Plan the graph first

Before writing files:

1. List every **beat** in the lesson (one node per classroom moment).
2. Mark **branch points** (nodes where the teacher will choose between 2+ paths).
3. Sketch `from → to` links and label each branch as an explorable path.
4. Decide which beats are **text slides** and which are **video-only** (see layouts below).
5. Pick a unique `graph.slug` (lowercase, hyphens).

Typical rhythm at a branch point:

```
[Main text slide] → discuss → [Branch-question sub-slide] → discuss options → teacher picks branch → [Next node]
```

---

## 2. Folder layout (required)

Create:

```
maps/{graph.slug}/
├── manifest.yaml
├── nodes/
│   ├── {node-slug}.md              # main slide (text layout)
│   ├── {node-slug}-question.md     # optional branch-question sub-slide
│   └── ...
└── assets/
    ├── diagram.png
    ├── clip.mp4
    └── clip.vtt                      # captions for video
```

Copy `maps/_template/` as a starting point when helpful.

**Never** put media bytes in YAML or the database. Files live under `assets/`.

---

## 3. manifest.yaml structure

Four sections, in this order:

### `graph`

```yaml
graph:
  slug: my-lesson
  title: "Human title for teachers"
  description: "One sentence for the map catalog"
  entry_node: opening
```

### `nodes`

Each node is one vertex in the graph.

| Field | Required | Notes |
|-------|----------|-------|
| `slug` | yes | Stable id; used in branches |
| `title` | yes | Projector heading (except video layout hides it) |
| `type` | yes | `content` or `synthesis` |
| `layout` | no | `default` (text + assets) or `video` (video only on screen) |
| `content` | yes* | Path to main-slide Markdown (*optional when `layout: video`) |
| `branch_question` | no | Path to discussion sub-slide before branching |

**Text slide (default layout):**

```yaml
  - slug: opening
    title: "The Question"
    type: content
    layout: default
    content: nodes/opening.md
    branch_question: nodes/opening-question.md
```

**Video-only slide** — one video fills the projector; no markdown body shown:

```yaml
  - slug: opening-clip
    title: "Watch"
    type: content
    layout: video
    content: nodes/opening-clip.md   # may be omitted; if present, use minimal stub
```

Pair with exactly one video asset on that node (see assets). Do not put images or audio on `layout: video` nodes.

### `branches`

```yaml
branches:
  - from: opening
    to: path-a
    label: "Explore the first argument"
    student_label: "Optional fuller text for the branch-question sub-slide"
```

- `from` / `to` must match node `slug` values.
- Order in the file is display order on the teacher panel.
- Loops and converging paths are allowed.

### `assets`

```yaml
assets:
  - node: opening
    type: image
    path: assets/diagram.svg
    alt: "Accessible description"
  - node: opening-clip
    type: video
    path: assets/opening.mp4
    captions: assets/opening.vtt
    alt: "Opening narration"
    sort_order: 0
  - node: opening
    type: audio
    path: assets/chime.wav
    alt: "Transition tone"
    autoplay: false
```

| type | use when |
|------|----------|
| `image` | Static diagram on a text slide |
| `audio` | Sound only (no timed visual) |
| `video` | Synced picture + sound; use `layout: video` for full-screen clip |

Limits: **50 MB** per file by default; video formats `.mp4`, `.webm`, `.m4v`.

---

## 4. Markdown rules

### Main slide (`content`)

- Write for the **projector**: short paragraphs, block quotes for sources.
- The manifest `title` is the primary heading — do not duplicate with `#` unless intentional.
- Keep one beat per node.

### Branch-question (`branch_question`)

- Ask an open question only. **Do not list branch options** — the app appends them from `branches`.
- Use when the node has 2+ outgoing branches and the class should deliberate first.

### Video stub (`layout: video`)

If you include a content file, keep it minimal:

```markdown
<!-- video-only -->
```

---

## 5. Authoring workflow (publish / validate / remove)

After creating or updating files on disk:

```bash
# Check structure and files
uv run validate maps/my-lesson

# Load into BranchSlide (validate + database upsert)
uv run publish maps/my-lesson

# Run classroom
uv run main
# Teacher: http://localhost:8000/g/my-lesson/teacher
```

**Remove from server:**

```bash
# Database only (files stay on disk)
uv run remove my-lesson

# Database + delete maps/my-lesson/ folder
uv run remove my-lesson --delete-files

# Allow removal while a class session is still active
uv run remove my-lesson --force --delete-files
```

HTTP alternatives (server running):

```bash
curl -X POST http://localhost:8000/api/admin/validate -H 'Content-Type: application/json' -d '{"path":"maps/my-lesson"}'
curl -X POST http://localhost:8000/api/admin/load -H 'Content-Type: application/json' -d '{"path":"maps/my-lesson"}'
curl -X DELETE 'http://localhost:8000/api/admin/maps/my-lesson?delete_files=true'
```

---

## 6. Quality checklist (before publish)

- [ ] Every node slug referenced in `branches` exists in `nodes`
- [ ] `entry_node` exists
- [ ] Every `content` / `branch_question` path exists on disk (except optional content on `layout: video`)
- [ ] Every `assets[].path` exists; captions `.vtt` exists when declared
- [ ] Branch points with 2+ outgoing branches have a `branch_question` file
- [ ] `layout: video` nodes have exactly one `type: video` asset
- [ ] Video clips are short classroom segments, not full movies
- [ ] Slugs are lowercase with hyphens; never renamed after publish

---

## 7. Example graph shape

```
entry → opening (text + image)
          ├→ opening-clip (video layout) → path-a (text)
          └→ path-b (text) ────────────────┘
                    ↓
               synthesis
```

Author one node per box; wire with `branches`.

---

## 8. What not to build

- No timeline engine or timed asset sequences in YAML
- No separate audio+image sync on one slide — use **video** instead
- No student-click navigation — teacher only
- No embedding binary data in manifest fields

When in doubt: **text node for reading**, **video node for performed segments with captions**.