# BranchSlide Roadmap

Phased plan for making the framework bulletproof and media-capable. Revisit this before major feature work or first real classroom use.

**Current state (PoC):** Branching engine, teacher control, branch-question sub-slides, back navigation, LAN projection, file-based maps. Ready for demos and testing one map.

---

## Phase 1 — Bulletproof the classroom core

**Do this before relying on it in a real lesson.**

| Gap | Why it matters |
|-----|----------------|
| WebSocket reconnect | Projector tab refresh or Wi‑Fi blip shouldn't leave the display stuck |
| Session survives server restart | Laptop sleep/restart mid-class shouldn't kill the session |
| Teacher rejoin | Same session URL if the teacher panel is accidentally closed |
| Clear error states | "Server unreachable", "Session not found" — not a blank screen |
| Production run mode | Drop `--reload`; run with `--host 0.0.0.0` behind firewall |
| Map reload without DB wipe | Loader upserts, but schema/content edge cases need a smooth workflow |

**Start when:** "I'm using this in front of a class next week."

---

## Phase 2 — Content authoring at scale

**Before building many maps or importing Cicero.**

| Gap | Why it matters |
|-----|----------------|
| Authoring validation | Catch broken manifests, orphan branches, missing files at load time |
| Map preview mode | Walk the graph without a live session |
| Asset pipeline | Consistent folder layout, file size limits, supported formats documented |
| Basic images end-to-end | Registry stub exists; needs tested rendering on projector |

**Start when:** Authoring the second or third real map, or starting Cicero import.

---

## Phase 3 — Audio

**When spoken text or pronunciation matters.**

The `assets` table and renderer registry already support this. Work items:

1. `type: audio` in manifest
2. Audio renderer (HTML5 `<audio>` or similar)
3. Teacher controls: play / pause / optional "push audio to projector"
4. Decide: ambient (teacher triggers) vs autoplay on slide entry

**Start when:** A map node needs heard Latin, narration, or a primary source read aloud.

**Skip for now if:** The teacher reads slides live.

---

## Phase 4 — Audio + image sync

**Only when timing between media matters.**

This is a new content model, not just a new asset type.

| Approach | Complexity | Best for |
|----------|------------|----------|
| Embedded video (MP4 with image + audio baked in) | Low | Simple, one-file slides |
| Manifest timeline (`sequence: [{at: 0s, show: img}, {at: 3s, play: audio}]`) | High | Precise classroom choreography |
| Pre-built HTML slide as asset (`type: code` / `iframe`) | Medium | One-off bespoke slides |

**Start when:** "The image must appear *while* the audio says X" — not merely both on the same slide.

**Note:** Don't build a timeline engine until 2–3 concrete slides need it. Video or pre-authored HTML often covers 80% of cases.

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
Now     → demos and first map testing (current PoC)
Next    → Phase 1 (reconnect, errors, production startup)
Then    → Phase 2 when authoring more maps
Audio   → Phase 3 when content demands it
Sync    → Phase 4 only with specific slides that need it
Scale   → Phase 5 when deployment grows beyond one classroom
```

**Highest-value next step:** WebSocket reconnect + session recovery — saves you mid-lesson more than audio would.

---

## Already in place (don't rebuild)

- Generic branching engine (`graph_slug` everywhere)
- `assets[].type` + renderer registry (extensible)
- Node slots: `content`, `branch_question`
- Branch slots: `label`, `student_label`
- SQLite + file-based loader
- WebSocket live sync
- Teacher back navigation + display phases

See `README.md` for authoring slot reference and run instructions.