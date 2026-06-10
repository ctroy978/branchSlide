from collections.abc import Callable

from app.models import Asset, Node
from app.renderers.audio import render_audio
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


def render_node(node: Node, graph_slug: str) -> str:
    parts = [render_markdown(node.content_md)]
    for asset in sorted(node.assets, key=lambda a: a.id):
        renderer = ASSET_RENDERERS.get(asset.asset_type)
        if renderer:
            parts.append(renderer(asset, graph_slug))
    return "\n".join(parts)