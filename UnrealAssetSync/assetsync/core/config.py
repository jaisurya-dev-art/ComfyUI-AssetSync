import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class AssetSyncConfig:
    blender_executable: str = ""
    blender_port: int = 18951
    maya_port: int = 18952
    unreal_port: int = 18953
    cache_directory: str = ""
    log_level: str = "INFO"
    connect_timeout: float = 2.0
    response_timeout: float = 120.0

    @property
    def cache_path(self) -> Path:
        override = self.cache_directory or os.environ.get("ASSETSYNC_CACHE_DIR", "")
        return Path(override).expanduser() if override else Path.home() / ".assetsync" / "cache"

    def port_for(self, destination: str) -> int:
        return int(getattr(self, "{0}_port".format(destination.lower())))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def default_config_path() -> Path:
    override = os.environ.get("ASSETSYNC_CONFIG", "")
    return Path(override).expanduser() if override else Path.home() / ".assetsync" / "config.json"


def load_config(path: Optional[Path] = None) -> AssetSyncConfig:
    config_path = path or default_config_path()
    config = AssetSyncConfig()
    if not config_path.exists():
        return config
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Could not read AssetSync config {0}: {1}".format(config_path, exc))
    allowed = set(config.to_dict())
    return AssetSyncConfig(**{key: value for key, value in data.items() if key in allowed})

