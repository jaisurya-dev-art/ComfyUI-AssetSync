from pathlib import Path
import re
from typing import Any, Dict

from ..core.asset_descriptor import AssetDescriptor
from ..core.protocol import ImportOptions, validate_request
from ..core.validation import validate_asset


def parse_import_request(message: Dict[str, Any], expected_dcc: str):
    validate_request(message)
    if message.get("action") != "import_asset":
        raise ValueError("Expected import_asset action")
    dcc = str((message.get("destination") or {}).get("dcc", "")).lower()
    if dcc != expected_dcc:
        raise ValueError("Request destination is {0}, not {1}.".format(dcc or "missing", expected_dcc))
    asset = AssetDescriptor.from_dict(message.get("asset") or {})
    validate_asset(asset)
    values = message.get("options") or {}
    options = ImportOptions(
        replace_existing=bool(values.get("replace_existing", False)),
        import_materials=bool(values.get("import_materials", True)),
        import_textures=bool(values.get("import_textures", True)),
        import_animation=bool(values.get("import_animation", True)),
        motion_only=bool(values.get("motion_only", False)),
        animation_clip=str(values.get("animation_clip") or ""),
    )
    return asset, options


def semantic_from_name(path: str) -> str:
    raw = Path(path).stem.lower()
    value = raw.replace("_", "").replace("-", "").replace(" ", "")
    tokens = set(filter(None, re.split(r"[^a-z0-9]+", raw)))
    aliases = {
        "base_color": ("basecolor", "albedo", "diffuse", "color"),
        "normal": ("normalmap", "normal", "n"),
        "roughness": ("roughness", "rough"),
        "metallic": ("metallic", "metalness", "metal"),
        "ao": ("ambientocclusion", "occlusion", "ao"),
        "opacity": ("opacity", "alpha", "mask"),
        "emission": ("emissive", "emission"),
    }
    for semantic, names in aliases.items():
        if any(name == value or name in tokens or (len(name) > 2 and name in value) for name in names):
            return semantic
    return "unknown"
