from typing import Any, Dict, List

from ...core.asset_descriptor import AssetDescriptor
from ...core.protocol import ImportOptions, response
from .materials import rebuild_material


GLTF_TO_MAYA_CENTIMETERS = 100.0


def _enable_double_sided_viewport(cmds, shapes: List[str]) -> None:
    """Match glTF doubleSided rendering in Maya Viewport 2.0."""
    for shape in shapes:
        try:
            cmds.setAttr(shape + ".doubleSided", True)
            cmds.setAttr(shape + ".opposite", False)
        except Exception:
            pass
    try:
        for panel in cmds.getPanel(type="modelPanel") or []:
            cmds.modelEditor(panel, edit=True, twoSidedLighting=True)
    except Exception:
        # maya.standalone has no model panels; the mesh attributes still apply.
        pass


def _roots_with_id(cmds, asset_id: str) -> List[str]:
    result = []
    for plug in cmds.ls("*.assetsync_id") or []:
        try:
            if cmds.getAttr(plug) == asset_id:
                result.append(plug.rsplit(".", 1)[0])
        except Exception:
            pass
    return result


def _mel_path(path: str) -> str:
    return str(path).replace("\\", "/").replace('"', '\\"')


def _fbx_take_names(mel, path: str) -> List[str]:
    mel.eval('FBXRead -f "{0}";'.format(_mel_path(path)))
    try:
        count = int(mel.eval("FBXGetTakeCount;") or 0)
        return [str(mel.eval("FBXGetTakeName {0};".format(index))) for index in range(1, count + 1)]
    finally:
        mel.eval("FBXClose;")


def _take_index(takes: List[str], requested: str) -> int:
    if not takes:
        return 0
    if not requested:
        return 1
    needle = requested.casefold()
    for index, name in enumerate(takes, 1):
        if name.casefold() == needle or name.rsplit("|", 1)[-1].casefold() == needle:
            return index
    raise RuntimeError(
        "Animation clip '{0}' was not found in the FBX. Available clips: {1}".format(
            requested, ", ".join(takes),
        )
    )


def _import_fbx(cmds, mel, path: str, options: ImportOptions):
    takes = _fbx_take_names(mel, path)
    selected_take = _take_index(takes, options.animation_clip) if options.import_animation else 0
    if options.motion_only and not selected_take:
        raise RuntimeError("The input model contains no FBX animation takes.")
    mel.eval("FBXResetImport;")
    mel.eval("FBXImportMode -v add;")
    mel.eval("FBXImportSmoothingGroups -v true;")
    mel.eval("FBXImportUnlockNormals -v false;")
    mel.eval("FBXImportFillTimeline -v {0};".format("true" if selected_take else "false"))
    mel.eval("FBXImportQuaternion -v resample;")
    mel.eval("FBXImportSetLockedAttribute -v false;")
    mel.eval("FBXImportSetMayaFrameRate -v false;")
    before = set(cmds.ls(long=True) or [])
    take_flag = " -t {0}".format(selected_take) if takes or not options.import_animation else ""
    mel.eval('FBXImport -f "{0}"{1};'.format(_mel_path(path), take_flag))
    imported = sorted(set(cmds.ls(long=True) or []) - before)
    return imported, takes, selected_take


def _remove_source_meshes(cmds, imported: List[str]) -> None:
    for shape in cmds.ls(imported, type="mesh", long=True) or []:
        parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
        if not parents:
            continue
        transform = parents[0]
        joints = cmds.listRelatives(transform, allDescendents=True, type="joint", fullPath=True) or []
        cmds.delete(shape if joints else transform)


def import_asset(asset: AssetDescriptor, options: ImportOptions) -> Dict[str, Any]:
    import maya.cmds as cmds

    mel = None
    if asset.mesh_format == "fbx":
        if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
            try:
                cmds.loadPlugin("fbxmaya", quiet=True)
            except Exception as exc:
                raise RuntimeError("The Maya FBX plugin is unavailable: {0}".format(exc))
        file_type = "FBX"
        try:
            import maya.mel as mel
        except Exception as exc:
            raise RuntimeError("Maya MEL is unavailable for FBX import: {0}".format(exc))
    elif asset.mesh_format == "obj":
        file_type = "OBJ"
    else:
        raise ValueError("Maya receiver expects FBX or OBJ, not {0}.".format(asset.mesh_format.upper()))
    old = _roots_with_id(cmds, asset.asset_id)
    replaced = bool(old and options.replace_existing)
    if replaced:
        cmds.delete(old)
    if file_type == "FBX":
        imported, take_names, selected_take = _import_fbx(cmds, mel, asset.mesh_path, options)
    else:
        imported = cmds.file(
            asset.mesh_path, i=True, type=file_type, ignoreVersion=True,
            mergeNamespacesOnClash=False, namespace=":", returnNewNodes=True, options="v=0;",
        ) or []
        take_names, selected_take = [], 0
    imported_curves = cmds.ls(imported, type="animCurve") or []
    if options.motion_only and not imported_curves:
        raise RuntimeError("Maya imported the skeleton but found no animation curves in the selected take.")
    if options.motion_only:
        _remove_source_meshes(cmds, imported)
        imported = [node for node in imported if cmds.objExists(node)]
    transforms = cmds.ls(imported, type="transform", long=True) or []
    joints = cmds.ls(imported, type="joint", long=True) or []
    dag_nodes = list(dict.fromkeys(transforms + joints))
    transform_set = set(dag_nodes)
    roots = []
    for node in dag_nodes:
        parent = cmds.listRelatives(node, parent=True, fullPath=True) or []
        if not parent or parent[0] not in transform_set:
            roots.append(node)
    original_format = str(asset.metadata.get("original_format", asset.mesh_format)).lower()
    if original_format in {"glb", "gltf"} and not options.motion_only and not asset.metadata.get("has_animation"):
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
    if asset.metadata.get("double_sided"):
        _enable_double_sided_viewport(cmds, shapes)
    texture_paths = [item.path for item in asset.textures]
    rebuilt = rebuild_material(asset.name, shapes, texture_paths) if options.import_materials and options.import_textures else 0
    materials = set()
    for shape in shapes:
        materials.update(cmds.listConnections(shape, type="shadingEngine") or [])
    return response(
        True, "{0} {1} successfully".format(asset.name, "replaced" if replaced else "imported"), asset.asset_id,
        objects=len(shapes), materials=len(materials), textures=rebuilt, replaced=replaced, root=group,
        joints=len(joints), animation_curves=len(imported_curves),
        clip=take_names[selected_take - 1] if selected_take else "", animation_takes=take_names,
    )
