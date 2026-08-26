"""Dependency-free glTF metadata inspection used before DCC conversion."""

import json
import struct
from pathlib import Path
from typing import Any, Dict, List


GLB_JSON_CHUNK = 0x4E4F534A


def read_gltf_document(path: Path) -> Dict[str, Any]:
    source = Path(path)
    if source.suffix.lower() == ".gltf":
        return json.loads(source.read_text(encoding="utf-8"))
    with source.open("rb") as stream:
        header = stream.read(12)
        if len(header) != 12 or header[:4] != b"glTF":
            raise ValueError("Invalid GLB header")
        chunk_header = stream.read(8)
        if len(chunk_header) != 8:
            raise ValueError("GLB has no JSON chunk")
        chunk_length, chunk_type = struct.unpack("<II", chunk_header)
        if chunk_type != GLB_JSON_CHUNK:
            raise ValueError("The first GLB chunk is not JSON")
        return json.loads(stream.read(chunk_length).decode("utf-8").rstrip("\x00 \t\r\n"))


def animation_clips(document: Dict[str, Any]) -> List[Dict[str, Any]]:
    accessors = document.get("accessors") or []
    result = []
    for index, animation in enumerate(document.get("animations") or []):
        starts = []
        ends = []
        for sampler in animation.get("samplers") or []:
            accessor_index = sampler.get("input")
            if not isinstance(accessor_index, int) or not 0 <= accessor_index < len(accessors):
                continue
            accessor = accessors[accessor_index]
            minimum = accessor.get("min") or []
            maximum = accessor.get("max") or []
            if minimum:
                starts.append(float(minimum[0]))
            if maximum:
                ends.append(float(maximum[0]))
        paths = sorted({
            str((channel.get("target") or {}).get("path"))
            for channel in animation.get("channels") or []
            if (channel.get("target") or {}).get("path")
        })
        start = min(starts) if starts else None
        end = max(ends) if ends else None
        result.append({
            "name": str(animation.get("name") or "Animation_{0}".format(index + 1)),
            "duration_seconds": round(end - start, 6) if start is not None and end is not None else None,
            "channels": len(animation.get("channels") or []),
            "target_paths": paths,
        })
    return result


def inspect_gltf(path: Path) -> Dict[str, Any]:
    document = read_gltf_document(Path(path))
    clips = animation_clips(document)
    return {
        "animation_clips": clips,
        "animation_count": len(clips),
        "has_animation": bool(clips),
        "skeleton_count": len(document.get("skins") or []),
        "has_skeleton": bool(document.get("skins") or []),
        "double_sided": any(bool(material.get("doubleSided")) for material in document.get("materials") or []),
    }
