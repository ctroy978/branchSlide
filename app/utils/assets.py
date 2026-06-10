import json
from pathlib import Path


def parse_asset_metadata(metadata_json: str) -> dict:
    try:
        data = json.loads(metadata_json or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def asset_label(path: str, alt_text: str) -> str:
    if alt_text.strip():
        return alt_text.strip()
    return Path(path).stem.replace("-", " ").replace("_", " ")


def build_asset_metadata(asset_data: dict) -> str:
    metadata: dict = {}
    if "autoplay" in asset_data:
        metadata["autoplay"] = bool(asset_data["autoplay"])
    return json.dumps(metadata)