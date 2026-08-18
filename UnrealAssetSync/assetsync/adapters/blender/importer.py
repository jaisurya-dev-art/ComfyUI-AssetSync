from pathlib import Path
from typing import Any, Dict

from ...core.asset_descriptor import AssetDescriptor
from ...core.protocol import ImportOptions, response


def _remove_existing(bpy, asset_id: str) -> bool:
    removed = False
    for collection in list(bpy.data.collections):
        if collection.get("assetsync_id") == asset_id:
            for obj in list(collection.all_objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection)
            removed = True
    return removed


def _import(bpy, asset: AssetDescriptor) -> None:
    kwargs = {"filepath": asset.mesh_path}
    if asset.mesh_format in {"glb", "gltf"}:
        bpy.ops.import_scene.gltf(**kwargs)
    elif asset.mesh_format == "fbx":
        bpy.ops.import_scene.fbx(**kwargs)
    elif asset.mesh_format == "obj":
        if hasattr(bpy.ops.wm, "obj_import"):
            bpy.ops.wm.obj_import(**kwargs)
        else:
            bpy.ops.import_scene.obj(**kwargs)
    else:
        raise ValueError("Blender receiver does not support {0}.".format(asset.mesh_format.upper()))


def import_asset(asset: AssetDescriptor, options: ImportOptions) -> Dict[str, Any]:
    import bpy

    replaced = _remove_existing(bpy, asset.asset_id) if options.replace_existing else False
    before = set(bpy.data.objects)
    _import(bpy, asset)
    imported = list(set(bpy.data.objects) - before)
    if not imported:
        raise RuntimeError("Blender completed the import but created no objects.")
    root = bpy.data.collections.get("AssetSync")
    if root is None:
        root = bpy.data.collections.new("AssetSync")
        bpy.context.scene.collection.children.link(root)
    package = bpy.data.collections.new(asset.name)
    root.children.link(package)
    package["assetsync_id"] = asset.asset_id
    package["assetsync_source"] = asset.source or "ComfyUI"
    package["assetsync_original_path"] = asset.original_mesh or asset.mesh_path
    for obj in imported:
        obj["assetsync_id"] = asset.asset_id
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        package.objects.link(obj)
    materials = {slot.material for obj in imported for slot in getattr(obj, "material_slots", []) if slot.material}
    images = {node.image for material in materials if material and material.use_nodes for node in material.node_tree.nodes if getattr(node, "image", None)}
    return response(
        True, "{0} {1} successfully".format(asset.name, "replaced" if replaced else "imported"), asset.asset_id,
        objects=len(imported), materials=len(materials), textures=len(images), replaced=replaced,
    )

