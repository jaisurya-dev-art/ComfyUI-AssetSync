from dataclasses import dataclass, field
from typing import Any, Dict

from .asset_descriptor import AssetDescriptor
from .errors import ValidationError


PROTOCOL_NAME = "assetsync"
PROTOCOL_VERSION = 1


@dataclass
class ImportOptions:
    replace_existing: bool = False
    import_materials: bool = True
    import_textures: bool = True

    def to_dict(self) -> Dict[str, bool]:
        return {
            "replace_existing": self.replace_existing,
            "import_materials": self.import_materials,
            "import_textures": self.import_textures,
        }


def import_request(asset: AssetDescriptor, destination: str, options: ImportOptions) -> Dict[str, Any]:
    return {
        "protocol": PROTOCOL_NAME,
        "version": PROTOCOL_VERSION,
        "action": "import_asset",
        "asset": asset.to_dict(),
        "destination": {"dcc": destination},
        "options": options.to_dict(),
    }


def validate_request(message: Dict[str, Any]) -> None:
    if message.get("protocol") != PROTOCOL_NAME:
        raise ValidationError("This is not an AssetSync protocol message.")
    if message.get("version") != PROTOCOL_VERSION:
        raise ValidationError("Unsupported AssetSync protocol version: {0}".format(message.get("version")))
    if message.get("action") not in {"import_asset", "status"}:
        raise ValidationError("Unsupported AssetSync action: {0}".format(message.get("action")))


def response(success: bool, message: str, asset_id: str = "", **details: Any) -> Dict[str, Any]:
    return {"success": success, "asset_id": asset_id, "message": message, "details": details}

