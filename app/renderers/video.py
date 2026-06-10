from app.models import Asset
from app.utils.assets import asset_captions_path, asset_label, parse_asset_metadata


def render_video(asset: Asset, graph_slug: str) -> str:
    src = f"/map-assets/{graph_slug}/{asset.path}"
    label = asset_label(asset.path, asset.alt_text)
    metadata = parse_asset_metadata(asset.metadata_json)
    autoplay = "true" if metadata.get("autoplay") else "false"
    captions_path = asset_captions_path(metadata)
    track_html = ""
    if captions_path:
        track_src = f"/map-assets/{graph_slug}/{captions_path}"
        track_html = (
            f'<track kind="captions" src="{track_src}" srclang="en" '
            f'label="Captions" default>'
        )
    return (
        f'<figure class="slide-asset slide-asset-video my-6" data-asset-id="{asset.id}">'
        f'<video id="asset-{asset.id}" class="slide-video mx-auto max-w-full rounded-lg shadow-md" '
        f'data-asset-id="{asset.id}" data-autoplay="{autoplay}" '
        f'playsinline preload="metadata">'
        f'<source src="{src}">'
        f"{track_html}"
        f"</video>"
        f'<figcaption class="sr-only">{label}</figcaption>'
        f"</figure>"
    )