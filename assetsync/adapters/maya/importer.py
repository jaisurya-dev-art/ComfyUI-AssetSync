from typing import Any, Dict, List

from ...core.asset_descriptor import AssetDescriptor
from ...core.protocol import ImportOptions, response
from .materials import rebuild_material


GLTF_TO_MAYA_CENTIMETERS = 100.0


def _roots_with_id(cmds, asset_id: str) -> List[str]:
    result = []
    for plug in cmds.ls("*.assetsync_id") or []:
        try:
            if cmds.getAttr(plug) == asset_id:
                result.append(plug.rsplit(".", 1)[0])
        except Exception:
            pass
    return result


def import_asset(asset: AssetDescriptor, options: ImportOptions) -> Dict[str, Any]:
    import maya.cmds as cmds

    if asset.mesh_format == "fbx":
        if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
            try:
                cmds.loadPlugin("fbxmaya", quiet=True)
            except Exception as exc:
                raise RuntimeError("The Maya FBX plugin is unavailable: {0}".format(exc))
        file_type = "FBX"
        try:
            import maya.mel as mel
            mel.eval("FBXResetImport;")
            mel.eval("FBXImportSmoothingGroups -v true;")
            mel.eval("FBXImportUnlockNormals -v false;")
        except Exception:
            # Older FBX plug-ins may not expose every option; import still works.
            pass
    elif asset.mesh_format == "obj":
        file_type = "OBJ"
    else:
        raise ValueError("Maya receiver expects FBX or OBJ, not {0}.".format(asset.mesh_format.upper()))
    old = _roots_with_id(cmds, asset.asset_id)
    replaced = bool(old and options.replace_existing)
    if replaced:
        cmds.delete(old)
    imported = cmds.file(
        asset.mesh_path, i=True, type=file_type, ignoreVersion=True,
        mergeNamespacesOnClash=False, namespace=":", returnNewNodes=True, options="v=0;",
    ) or []
    transforms = cmds.ls(imported, type="transform", long=True) or []
    transform_set = set(transforms)
    roots = []
    for node in transforms:
        parent = cmds.listRelatives(node, parent=True, fullPath=True) or []
        if not parent or parent[0] not in transform_set:
            roots.append(node)
    original_format = str(asset.metadata.get("original_format", asset.mesh_format)).lower()
    if original_format in {"glb", "gltf"}:
        for root in roots:
            scale = cmds.getAttr(root + ".scale")[0]
            cmds.setAttr(
                root + ".scale",
                scale[0] * GLTF_TO_MAYA_CENTIMETERS,
                scale[1] * GLTF_TO_MAYA_CENTIMETERS,
                scale[2] * GLTF_TO_MAYA_CENTIMETERS,
            )
            cmds.makeIdentity(root, apply=True, translate=False, rotate=False, scale=True)
    group = cmds.group(roots, name="AssetSync_{0}_GRP".format(asset.name)) if roots else cmds.group(empty=True, name="AssetSync_{0}_GRP".format(asset.name))
    for attribute, value in (("assetsync_id", asset.asset_id), ("assetsync_source", asset.source or "ComfyUI"), ("assetsync_original_format", original_format)):
        cmds.addAttr(group, longName=attribute, dataType="string")
        cmds.setAttr(group + "." + attribute, str(value), type="string")
    shapes = cmds.listRelatives(group, allDescendents=True, type="mesh", fullPath=True) or []
    texture_paths = [item.path for item in asset.textures]
    rebuilt = rebuild_material(asset.name, shapes, texture_paths) if options.import_materials and options.import_textures else 0
    materials = set()
    for shape in shapes:
        materials.update(cmds.listConnections(shape, type="shadingEngine") or [])
    return response(
        True, "{0} {1} successfully".format(asset.name, "replaced" if replaced else "imported"), asset.asset_id,
        objects=len(shapes), materials=len(materials), textures=rebuilt, replaced=replaced, root=group,
    )
