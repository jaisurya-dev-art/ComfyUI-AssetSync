"""Headless Blender GLB/GLTF to FBX conversion with content-addressed caching."""

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, Optional

from ..core.asset_descriptor import AssetDescriptor
from ..core.config import AssetSyncConfig
from ..core.errors import ConversionError
from .base_converter import BaseConverter
from .conversion_result import ConversionResult


def _common_blender_locations() -> Iterable[Path]:
    roots = [
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Blender Foundation",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Blender Foundation",
        Path("/Applications"),
        Path("/usr/bin"),
        Path("/usr/local/bin"),
    ]
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            yield root
            continue
        patterns = ("Blender*/blender.exe", "Blender.app/Contents/MacOS/Blender", "blender")
        for pattern in patterns:
            yield from root.glob(pattern)


def discover_blender(configured: str = "") -> Optional[Path]:
    candidates = [configured, os.environ.get("ASSETSYNC_BLENDER", ""), os.environ.get("BLENDER_EXECUTABLE", ""), shutil.which("blender") or ""]
    for candidate in candidates:
        if candidate and Path(candidate).expanduser().is_file():
            return Path(candidate).expanduser().resolve()
    found = [item for item in _common_blender_locations() if item.is_file()]
    return sorted(found, reverse=True)[0].resolve() if found else None


def source_fingerprint(path: Path) -> Dict[str, object]:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    stat = path.stat()
    return {"source_hash": digest.hexdigest(), "source_size": stat.st_size, "source_modified_ns": stat.st_mtime_ns}


class BlenderFbxConverter(BaseConverter):
    source_formats = frozenset({"glb", "gltf"})
    target_format = "fbx"
    version = 3

    def __init__(self, config: AssetSyncConfig):
        self.config = config

    def convert(self, asset: AssetDescriptor, destination: str) -> ConversionResult:
        source = Path(asset.mesh_path).resolve()
        fingerprint = source_fingerprint(source)
        asset_cache = self.config.cache_path / asset.asset_id
        package = asset_cache / destination
        source_cache = asset_cache / "source" / source.name
        output = package / (source.stem + ".fbx")
        textures = package / "textures"
        metadata_path = package / "metadata.json"
        expected = {
            "asset_id": asset.asset_id, "source_format": asset.mesh_format,
            "target_format": "fbx", "converter": "blender", "conversion_version": self.version,
            **fingerprint,
        }
        if output.is_file() and output.stat().st_size and metadata_path.is_file():
            try:
                cached = json.loads(metadata_path.read_text(encoding="utf-8"))
                if all(cached.get(key) == value for key, value in expected.items()):
                    paths = [str(item.resolve()) for item in textures.glob("*") if item.is_file()]
                    return ConversionResult(True, str(source), str(output), "fbx", paths, "Reused cached conversion", cached)
            except (OSError, ValueError):
                pass
        blender = discover_blender(self.config.blender_executable)
        if not blender:
            raise ConversionError(
                "AssetSync could not send this asset to Maya. The source format is {0} and Maya requires FBX conversion. "
                "Blender could not be located. Configure blender_executable or ASSETSYNC_BLENDER.".format(asset.mesh_format.upper())
            )
        package.mkdir(parents=True, exist_ok=True)
        textures.mkdir(parents=True, exist_ok=True)
        source_cache.parent.mkdir(parents=True, exist_ok=True)
        if not source_cache.is_file() or source_fingerprint(source_cache)["source_hash"] != fingerprint["source_hash"]:
            shutil.copy2(str(source), str(source_cache))
        manifest = package / "conversion-result.json"
        script = Path(__file__).parent / "scripts" / "glb_to_fbx.py"
        command = [str(blender), "--background", "--factory-startup", "--python", str(script), "--", str(source), str(output), str(textures), str(manifest)]
        try:
            process = subprocess.run(command, capture_output=True, text=True, timeout=900, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ConversionError("Blender conversion could not run: {0}".format(exc))
        if process.returncode != 0 or not output.is_file() or not output.stat().st_size:
            logs = (process.stderr or process.stdout or "No Blender output").strip()[-3000:]
            raise ConversionError("GLB/GLTF to FBX conversion failed. Blender reported: {0}".format(logs))
        manifest_data = {}
        if manifest.is_file():
            try:
                manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            except ValueError:
                pass
        texture_paths = [str(Path(item).resolve()) for item in manifest_data.get("textures", []) if Path(item).is_file()]
        expected["texture_paths"] = texture_paths
        expected["double_sided"] = bool(manifest_data.get("double_sided", False))
        metadata_path.write_text(json.dumps(expected, indent=2, ensure_ascii=False), encoding="utf-8")
        return ConversionResult(True, str(source), str(output.resolve()), "fbx", texture_paths, "Converted with Blender", expected)
