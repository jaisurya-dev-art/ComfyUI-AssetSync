"""ComfyUI node entry point."""

from uuid import NAMESPACE_URL, uuid5

if __package__:
    from .assetsync.core.errors import AssetSyncError
    from .assetsync.core.normalization import normalize_asset
    from .assetsync.core.protocol import ImportOptions
    from .assetsync.core.service import AssetSyncService
else:
    # Supports direct development imports without weakening ComfyUI package loading.
    from assetsync.core.errors import AssetSyncError
    from assetsync.core.normalization import normalize_asset
    from assetsync.core.protocol import ImportOptions
    from assetsync.core.service import AssetSyncService


class AnyAssetType(str):
    """ComfyUI wildcard that accepts custom generator sockets as well as strings."""

    def __ne__(self, other):
        return False


ANY_ASSET = AnyAssetType("*")


class AssetSyncNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "asset": (ANY_ASSET,),
                "destination": (["Blender", "Maya", "Unreal"],),
                "asset_name": ("STRING", {"default": ""}),
                "replace_existing": ("BOOLEAN", {"default": True}),
                "import_materials": ("BOOLEAN", {"default": True}),
                "import_textures": ("BOOLEAN", {"default": True}),
            },
            "optional": {"assetsync_id": ("STRING", {"default": ""})},
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("assetsync_id", "status")
    FUNCTION = "sync"
    CATEGORY = "AssetSync"
    OUTPUT_NODE = True

    def sync(self, asset, destination, asset_name, replace_existing, import_materials, import_textures, assetsync_id="", unique_id=""):
        stable_id = assetsync_id.strip() or str(uuid5(NAMESPACE_URL, "comfyui-assetsync:{0}".format(unique_id)))
        descriptor = normalize_asset(asset, name=asset_name, asset_id=stable_id)
        options = ImportOptions(replace_existing, import_materials, import_textures)
        try:
            result = AssetSyncService().sync(descriptor, destination, options)
        except AssetSyncError as exc:
            raise RuntimeError("AssetSync failed: {0}".format(exc))
        details = result.get("details") or {}
        counts = ", ".join("{0}: {1}".format(key.title(), details[key]) for key in ("objects", "materials", "textures", "assets") if key in details)
        status = result.get("message", "Asset imported successfully") + (("\n" + counts) if counts else "")
        return {"ui": {"text": [status]}, "result": (descriptor.asset_id, status)}


NODE_CLASS_MAPPINGS = {"AssetSync": AssetSyncNode}
NODE_DISPLAY_NAME_MAPPINGS = {"AssetSync": "AssetSync"}
