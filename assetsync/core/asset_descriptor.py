"""Normalized asset model shared by ComfyUI, converters, and receivers."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


SUPPORTED_SOURCE_FORMATS = frozenset({"glb", "gltf", "fbx", "obj"})


@dataclass
class TextureDescriptor:
    path: str
    semantic: Optional[str] = None
    material: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AssetDescriptor:
    asset_id: str
    name: str
    mesh_path: str
    mesh_format: str
    source: Optional[str] = None
    original_mesh: Optional[str] = None
    textures: List[TextureDescriptor] = field(default_factory=list)
    materials: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_path(
        cls, path: object, name: Optional[str] = None, asset_id: Optional[str] = None,
        source: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
    ) -> "AssetDescriptor":
        mesh = Path(str(path)).expanduser()
        return cls(
            asset_id=asset_id or str(uuid4()),
            name=(name or mesh.stem or "Asset").strip(),
            mesh_path=str(mesh),
            mesh_format=mesh.suffix.lower().lstrip("."),
            source=source,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "AssetDescriptor":
        path = value.get("mesh_path") or value.get("resolved_mesh") or value.get("path") or value.get("file_path")
        if not path:
            raise ValueError("The asset mapping does not contain a mesh path.")
        textures = []
        for item in value.get("textures") or []:
            textures.append(item if isinstance(item, TextureDescriptor) else TextureDescriptor(**item) if isinstance(item, dict) else TextureDescriptor(str(item)))
        descriptor = cls.from_path(
            path,
            name=value.get("name"),
            asset_id=value.get("asset_id") or value.get("id"),
            source=value.get("source"),
            metadata=value.get("metadata"),
        )
        descriptor.mesh_format = str(value.get("mesh_format") or descriptor.mesh_format).lower().lstrip(".")
        descriptor.original_mesh = value.get("original_mesh")
        descriptor.textures = textures
        descriptor.materials = list(value.get("materials") or [])
        return descriptor

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["id"] = data.pop("asset_id")
        return data

    def with_resolved_mesh(
        self, path: str, mesh_format: str, textures: List[str],
        conversion_metadata: Optional[Dict[str, Any]] = None,
    ) -> "AssetDescriptor":
        metadata = dict(self.metadata)
        metadata.setdefault("original_format", self.mesh_format)
        metadata["conversion_target_format"] = mesh_format
        metadata.update(conversion_metadata or {})
        return AssetDescriptor(
            asset_id=self.asset_id,
            name=self.name,
            mesh_path=path,
            mesh_format=mesh_format,
            source=self.source,
            original_mesh=self.original_mesh or self.mesh_path,
            textures=[TextureDescriptor(path=item) for item in textures],
            materials=list(self.materials),
            metadata=metadata,
        )
