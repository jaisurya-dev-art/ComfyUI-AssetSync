"""Normalizers for path-oriented and custom ComfyUI node outputs."""

from os import PathLike
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .asset_descriptor import AssetDescriptor, SUPPORTED_SOURCE_FORMATS
from .errors import ValidationError


PATH_KEYS = ("mesh_path", "file_path", "filepath", "path", "glb_path", "gltf_path", "fbx_path", "obj_path", "filename")


def _comfyui_annotated_path(value: Dict[str, Any]) -> Optional[Path]:
    filename = value.get("filename")
    if not filename:
        return None
    path = Path(str(filename)).expanduser()
    if path.is_absolute():
        return path
    output_type = str(value.get("type", "output")).lower()
    try:
        import folder_paths
        getters = {
            "output": folder_paths.get_output_directory,
            "temp": folder_paths.get_temp_directory,
            "input": folder_paths.get_input_directory,
        }
        base = Path(getters.get(output_type, folder_paths.get_output_directory)())
        return base / str(value.get("subfolder") or "") / path
    except (ImportError, AttributeError):
        return None


def _candidate_paths(value: Any) -> Iterable[Any]:
    if isinstance(value, AssetDescriptor):
        yield value
    elif isinstance(value, (str, PathLike, Path)):
        yield value
    elif isinstance(value, dict):
        annotated = _comfyui_annotated_path(value)
        if annotated is not None:
            yield annotated
        for key in PATH_KEYS:
            if key == "filename" and annotated is not None:
                continue
            if value.get(key):
                yield value[key]
        for key in ("asset", "model", "result", "output", "files"):
            if key in value:
                yield from _candidate_paths(value[key])
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _candidate_paths(item)
    else:
        for key in PATH_KEYS:
            candidate = getattr(value, key, None)
            if candidate:
                yield candidate


def normalize_asset(value: Any, name: str = "", asset_id: str = "") -> AssetDescriptor:
    """Pick the first supported mesh from common upstream output shapes."""
    if isinstance(value, AssetDescriptor):
        result = value
    else:
        result = None
        for candidate in _candidate_paths(value):
            if isinstance(candidate, AssetDescriptor):
                result = candidate
                break
            path = Path(str(candidate)).expanduser()
            if path.suffix.lower().lstrip(".") in SUPPORTED_SOURCE_FORMATS:
                metadata: Optional[Dict[str, Any]] = None
                if isinstance(value, dict):
                    metadata = {
                        key: item for key, item in value.items()
                        if key not in PATH_KEYS and isinstance(item, (str, int, float, bool, type(None)))
                    }
                result = AssetDescriptor.from_path(path, name=name or None, asset_id=asset_id or None, metadata=metadata)
                break
        if result is None:
            raise ValidationError("No GLB, GLTF, FBX, or OBJ file path was found in the upstream output.")
    if name.strip():
        result.name = name.strip()
    if asset_id.strip():
        result.asset_id = asset_id.strip()
    return result
