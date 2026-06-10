# BranchSlide Roadmap

Phased plan for making the framework bulletproof and media-capable. Revisit this before major feature work or first real classroom use.

**Current state:** Branching engine, teacher control, branch-question sub-slides, back navigation, LAN projection (dual-port), file-based maps, map validation/preview, image and audio assets with teacher-triggered projector sync. Ready for classroom demos and content authoring.

---

## Phase 1 — Bulletproof the classroom core ✅

**Do this before relying on it in a real lesson.**

| Gap | Status |
|-----|--------|
| WebSocket reconnect | Done |
| Session survives server restart | Done (SQLite) |
| Teacher rejoin | Done (bookmark URL) |
| Clear error states | Done |
| Production run mode | Done (`uv run main`) |
| Map reload without DB wipe | Done (loader upserts) |

---

## Phase 2 — Content authoring at scale ✅

**Before building many maps or importing Cicero.**

| Gap | Status |
|-----|--------|
| Authoring validation | Done |
| Map preview mode | Done |
| Asset pipeline | Done (folder layout, size limits, formats) |
| Basic images end-to-end | Done |

---

## Phase 3 — Audio ✅

**When spoken text or pronunciation matters without a timed visual.**

| Item | Status |
|------|--------|
| `type: audio` in manifest | Done |
| Audio renderer (HTML5 `<audio>`) | Done |
| Teacher controls: play / pause / stop | Done |
| Projector sync via WebSocket | Done |
| Optional `autoplay` on slide entry | Done (teacher-triggered by default) |

**Keep audio** for audio-only slides (pronunciation, short clips, ambient tones). Not deprecated.

---

## Phase 4 — Video (synced picture + sound + captions) ✅

**When image and speech must stay in sync, or captions are required.**

Use **embedded video only** — one file per performed slide. No separate audio+image choreography and **no manifest timeline engine**.

| Item | Status |
|------|--------|
| `type: video` in manifest | Done (MP4, WebM, M4V) |
| Video renderer + WebVTT captions | Done |
| Teacher play / pause / stop | Done (shared with audio via `/media`) |
| Files on disk under `maps/…/assets/` | Done (50 MB default limit; not in SQLite) |
| Authoring | Export from any editor; bake diagram + narration into one clip |

**When to use what:**

| Need | Asset type |
|------|------------|
| Static diagram | `image` |
| Heard-only (no timed visual) | `audio` |
| Narration + visuals in sync, or captions | `video` |

**Start when:** A slide is a performed segment (narrated diagram, read-aloud source with visual) and accessibility matters.

---

## Phase 5 — Multi-task / multi-session robustness

**When one server hosts many maps or many classes.**

| Feature | When |
|---------|------|
| Named sessions / session picker | Multiple classes same day |
| Map catalog with metadata | 5+ maps |
| Optional light auth | Beyond firewall-only deployment |
| Session history / analytics | Post-lesson review |

**Start when:** Shared server or multiple teachers — not a single laptop in one room.

---

## Recommended order

```
Done    → Phases 1–4 (classroom core, authoring, audio, video)
Next    → Phase 5 when deployment grows beyond one classroom
```

---

## Already in place (don't rebuild)

- Generic branching engine (`graph_slug` everywhere)
- `assets[].type` + renderer registry (extensible)
- Node slots: `content`, `branch_question`
- Branch slots: `label`, `student_label`
- SQLite + file-based loader
- WebSocket live sync (teacher ↔ projector)
- Teacher back navigation + display phases
- Audio and video assets with teacher media controls

See `README.md` for authoring slot reference and run instructions.