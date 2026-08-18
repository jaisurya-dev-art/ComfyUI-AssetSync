from typing import Any, Dict

from ..conversion.resolver import ConversionResolver
from .asset_descriptor import AssetDescriptor
from .capabilities import get_destination
from .config import AssetSyncConfig, load_config
from .logging import configure_logging, get_logger
from .networking import AssetSyncClient
from .protocol import ImportOptions, import_request
from .validation import validate_asset


class AssetSyncService:
    def __init__(self, config: AssetSyncConfig = None):
        self.config = config or load_config()
        configure_logging(self.config.log_level)
        self.log = get_logger()
        self.converter = ConversionResolver(self.config)

    def sync(self, asset: AssetDescriptor, destination_name: str, options: ImportOptions) -> Dict[str, Any]:
        validate_asset(asset)
        destination = get_destination(destination_name)
        self.log.info("Destination: %s", destination.name.title())
        self.log.info("Input: %s", asset.mesh_path)
        resolved = self.converter.resolve(asset, destination)
        if resolved.mesh_path != asset.mesh_path:
            self.log.info("Resolved %s to %s", asset.mesh_format.upper(), resolved.mesh_format.upper())
        client = AssetSyncClient(timeout=self.config.response_timeout)
        result = client.send(self.config.port_for(destination.name), import_request(resolved, destination.name, options))
        self.log.info("Import successful")
        return result

