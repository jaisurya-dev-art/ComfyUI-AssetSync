from typing import Any, Dict, List

from ...core.asset_descriptor import AssetDescriptor
from ...core.protocol import ImportOptions, response


def import_asset(asset: AssetDescriptor, options: ImportOptions) -> Dict[str, Any]:
    import unreal

    safe_name = "".join(char if char.isalnum() or char == "_" else "_" for char in asset.name).strip("_") or "Asset"
    destination = "/Game/AssetSync/Generated/{0}".format(safe_name)
    existing: List[str] = unreal.EditorAssetLibrary.list_assets(destination, recursive=True, include_folder=False) or []
    replaced = False
    if options.replace_existing:
        for path in existing:
            loaded = unreal.EditorAssetLibrary.load_asset(path)
            if loaded and unreal.EditorAssetLibrary.get_metadata_tag(loaded, "assetsync_id") == asset.asset_id:
                unreal.EditorAssetLibrary.delete_asset(path)
                replaced = True
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", asset.mesh_path)
    task.set_editor_property("destination_path", destination)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", options.replace_existing)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths") or [])
    if not imported:
        raise RuntimeError("Unreal completed the import task but returned no imported assets.")
    for path in imported:
        loaded = unreal.EditorAssetLibrary.load_asset(path)
        if loaded:
            unreal.EditorAssetLibrary.set_metadata_tag(loaded, "assetsync_id", asset.asset_id)
            unreal.EditorAssetLibrary.set_metadata_tag(loaded, "assetsync_source", asset.original_mesh or asset.mesh_path)
            unreal.EditorAssetLibrary.save_loaded_asset(loaded, only_if_is_dirty=False)
    return response(True, "{0} imported successfully".format(asset.name), asset.asset_id, assets=len(imported), replaced=replaced, paths=imported)

