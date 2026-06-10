from app.models import Asset
from app.utils.assets import asset_label, parse_asset_metadata


def render_audio(asset: Asset, graph_slug: str) -> str:
    src = f"/map-assets/{graph_slug}/{asset.path}"
    label = asset_label(asset.path, asset.alt_text)
    metadata = parse_asset_metadata(asset.metadata_json)
    autoplay = "true" if metadata.get("autoplay") else "false"
    return (
        f'<figure class="slide-asset slide-asset-audio my-6" data-asset-id="{asset.id}">'
        f'<audio id="asset-{asset.id}" class="slide-audio" '
        f'data-asset-id="{asset.id}" data-autoplay="{autoplay}" '
        f'src="{src}" preload="metadata"></audio>'
        f'<figcaption class="sr-only">{label}</figcaption>'
        f"</figure>"
    )