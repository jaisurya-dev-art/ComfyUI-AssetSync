from dataclasses import dataclass
from typing import Dict, FrozenSet, Optional

from .errors import ValidationError


@dataclass(frozen=True)
class DestinationCapability:
    name: str
    supported_formats: FrozenSet[str]
    preferred_format: str
    port: int
    conversions: Dict[str, str]


DESTINATIONS = {
    "blender": DestinationCapability("blender", frozenset({"glb", "gltf", "fbx", "obj"}), "glb", 18951, {}),
    "maya": DestinationCapability("maya", frozenset({"fbx", "obj"}), "fbx", 18952, {"glb": "fbx", "gltf": "fbx"}),
    "unreal": DestinationCapability("unreal", frozenset({"glb", "gltf", "fbx"}), "fbx", 18953, {}),
}


def get_destination(name: str) -> DestinationCapability:
    key = str(name).strip().lower().replace(" engine", "")
    try:
        return DESTINATIONS[key]
    except KeyError:
        raise ValidationError("Unknown destination '{0}'. Choose Blender, Maya, or Unreal.".format(name))


def conversion_target(source_format: str, destination: DestinationCapability) -> Optional[str]:
    source = source_format.lower().lstrip(".")
    if source in destination.supported_formats:
        return None
    target = destination.conversions.get(source)
    if not target:
        raise ValidationError("{0} cannot reliably import {1}, and no conversion is configured.".format(destination.name.title(), source.upper()))
    return target

