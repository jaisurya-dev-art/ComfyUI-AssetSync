from pathlib import Path
from typing import Dict, Iterable, List

from ..common import semantic_from_name


def rebuild_material(asset_name: str, mesh_shapes: Iterable[str], texture_paths: List[str]) -> int:
    """Build one portable standardSurface from recognized PBR maps."""
    import maya.cmds as cmds

    maps: Dict[str, str] = {}
    for path in texture_paths:
        semantic = semantic_from_name(path)
        if semantic != "unknown" and semantic not in maps:
            maps[semantic] = path
    if not maps:
        return 0
    shader = cmds.shadingNode("standardSurface", asShader=True, name="{0}_AssetSync_MAT".format(asset_name))
    shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shader + "SG")
    cmds.connectAttr(shader + ".outColor", shading_group + ".surfaceShader", force=True)
    targets = {
        "base_color": ("baseColor", True), "roughness": ("specularRoughness", False),
        "metallic": ("metalness", False), "opacity": ("opacity", False),
        "emission": ("emissionColor", True),
    }
    texture_nodes = {}
    for semantic, (attribute, color) in targets.items():
        if semantic not in maps:
            continue
        node = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name="{0}_{1}_TEX".format(asset_name, semantic))
        cmds.setAttr(node + ".fileTextureName", str(Path(maps[semantic]).resolve()), type="string")
        if not color:
            cmds.setAttr(node + ".colorSpace", "Raw", type="string")
        output = ".outColor" if color or attribute == "opacity" else ".outColorR"
        cmds.connectAttr(node + output, shader + "." + attribute, force=True)
        texture_nodes[semantic] = node
        if semantic == "emission":
            cmds.setAttr(shader + ".emission", 1.0)
    if "ao" in maps:
        ao = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name=asset_name + "_ao_TEX")
        cmds.setAttr(ao + ".fileTextureName", str(Path(maps["ao"]).resolve()), type="string")
        cmds.setAttr(ao + ".colorSpace", "Raw", type="string")
        if "base_color" in texture_nodes:
            multiply = cmds.shadingNode("multiplyDivide", asUtility=True, name=asset_name + "_ao_MULT")
            cmds.disconnectAttr(texture_nodes["base_color"] + ".outColor", shader + ".baseColor")
            cmds.connectAttr(texture_nodes["base_color"] + ".outColor", multiply + ".input1", force=True)
            cmds.connectAttr(ao + ".outColor", multiply + ".input2", force=True)
            cmds.connectAttr(multiply + ".output", shader + ".baseColor", force=True)
        else:
            cmds.connectAttr(ao + ".outColor", shader + ".baseColor", force=True)
    if "normal" in maps:
        texture = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name=asset_name + "_normal_TEX")
        cmds.setAttr(texture + ".fileTextureName", str(Path(maps["normal"]).resolve()), type="string")
        cmds.setAttr(texture + ".colorSpace", "Raw", type="string")
        bump = cmds.shadingNode("bump2d", asUtility=True, name=asset_name + "_normal_BUMP")
        cmds.setAttr(bump + ".bumpInterp", 1)
        cmds.connectAttr(texture + ".outAlpha", bump + ".bumpValue", force=True)
        cmds.connectAttr(bump + ".outNormal", shader + ".normalCamera", force=True)
    for shape in mesh_shapes:
        cmds.sets(shape, edit=True, forceElement=shading_group)
    return len(maps)
