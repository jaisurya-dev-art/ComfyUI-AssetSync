from pathlib import Path

from .asset_descriptor import AssetDescriptor, SUPPORTED_SOURCE_FORMATS
from .capabilities import get_destination
from .errors import ValidationError


def validate_asset(asset: AssetDescriptor) -> Path:
    path = Path(asset.mesh_path).expanduser()
    if not path.exists():
        raise ValidationError("The generated asset file no longer exists: {0}".format(path))
    if not path.is_file():
        raise ValidationError("The generated asset path is not a file: {0}".format(path))
    if path.suffix.lower().lstrip(".") not in SUPPORTED_SOURCE_FORMATS:
        raise ValidationError("Unsupported asset format '.{0}'. Use GLB, GLTF, FBX, or OBJ.".format(path.suffix.lstrip(".")))
    try:
        size = path.stat().st_size
        with path.open("rb") as stream:
            stream.read(1)
    except OSError as exc:
        raise ValidationError("The generated asset file is not readable: {0}".format(exc))
    if size == 0:
        raise ValidationError("The generated asset file is empty: {0}".format(path))
    asset.mesh_path = str(path.resolve())
    asset.mesh_format = path.suffix.lower().lstrip(".")
    return path


def validate_destination(name: str) -> str:
    return get_destination(name).name

