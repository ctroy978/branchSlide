# Map template

Copy this folder to `maps/{your-slug}/` and replace placeholders.

1. Set `graph.slug`, titles, and `entry_node` in `manifest.yaml`
2. Write `nodes/*.md` content
3. Add `assets/opening-clip.mp4` (and real `.vtt` captions)
4. Run `uv run validate maps/{your-slug}` then `uv run publish maps/{your-slug}`

Authoring guide for Hermes: `HERMES.md` (repository root)