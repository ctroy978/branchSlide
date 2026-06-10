from collections.abc import Callable

from app.models import Asset, Node
from app.renderers.audio import render_audio
from app.renderers.video import render_video
from app.renderers.markdown import render_markdown

ASSET_RENDERERS: dict[str, Callable] = {}


def register_asset_renderer(asset_type: str, renderer: Callable) -> None:
    ASSET_RENDERERS[asset_type] = renderer


def render_image(asset: Asset, graph_slug: str) -> str:
    src = f"/map-assets/{graph_slug}/{asset.path}"
    alt = asset.alt_text or ""
    return (
        f'<figure class="slide-asset slide-asset-image my-8">'
        f'<img src="{src}" alt="{alt}" '
        f'class="slide-image mx-auto max-w-full rounded-lg shadow-md">'
        f"</figure>"
    )


register_asset_renderer("image", render_image)
register_asset_renderer("audio", render_audio)
register_asset_renderer("video", render_video)


def _sorted_assets(node: Node) -> list[Asset]:
    return sorted(node.assets, key=lambda asset: (asset.sort_order, asset.id))


def render_node(node: Node, graph_slug: str) -> str:
    assets = _sorted_assets(node)

    if node.layout == "video":
        parts = [
            renderer(asset, graph_slug)
            for asset in assets
            if asset.asset_type == "video"
            for renderer in [ASSET_RENDERERS.get(asset.asset_type)]
            if renderer
        ]
        return "\n".join(parts)

    parts = []
    if node.content_md.strip():
        parts.append(render_markdown(node.content_md))
    for asset in assets:
        renderer = ASSET_RENDERERS.get(asset.asset_type)
        if renderer:
            parts.append(renderer(asset, graph_slug))
    return "\n".join(parts)