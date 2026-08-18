from ..core.asset_descriptor import AssetDescriptor
from ..core.capabilities import DestinationCapability, conversion_target
from ..core.config import AssetSyncConfig
from ..core.errors import ConversionError
from .blender_converter import BlenderFbxConverter


class ConversionResolver:
    def __init__(self, config: AssetSyncConfig):
        self.converters = [BlenderFbxConverter(config)]

    def resolve(self, asset: AssetDescriptor, destination: DestinationCapability) -> AssetDescriptor:
        target = conversion_target(asset.mesh_format, destination)
        if target is None:
            return asset
        for converter in self.converters:
            if asset.mesh_format in converter.source_formats and target == converter.target_format:
                result = converter.convert(asset, destination.name)
                if result.success and result.output_path and result.output_format:
                    return asset.with_resolved_mesh(
                        result.output_path, result.output_format, result.texture_paths, result.metadata,
                    )
                raise ConversionError(result.message or "Asset conversion failed.")
        raise ConversionError("No converter is available for {0} to {1}.".format(asset.mesh_format.upper(), target.upper()))
