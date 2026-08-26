"""Create a tiny skinned GLB with one skeletal animation for DCC validation.

Run with Blender:
    blender --background --factory-startup --python tools/create_animated_fixture.py -- output.glb
"""

import sys
from pathlib import Path

import bpy


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 1:
        raise RuntimeError("Expected one output GLB path")
    output = Path(args[0]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = 25

    bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 1.0))
    mesh = bpy.context.object
    mesh.name = "AnimatedMesh"
    mesh.scale = (0.25, 0.25, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    bpy.ops.object.armature_add(location=(0.0, 0.0, 0.0))
    armature = bpy.context.object
    armature.name = "MotionRig"
    bpy.ops.object.mode_set(mode="EDIT")
    root = armature.data.edit_bones[0]
    root.name = "Root"
    root.head = (0.0, 0.0, 0.0)
    root.tail = (0.0, 0.0, 1.0)
    child = armature.data.edit_bones.new("Child")
    child.head = root.tail
    child.tail = (0.0, 0.0, 2.0)
    child.parent = root
    child.use_connect = True
    bpy.ops.object.mode_set(mode="OBJECT")

    group = mesh.vertex_groups.new(name="Root")
    group.add(list(range(len(mesh.data.vertices))), 1.0, "REPLACE")
    modifier = mesh.modifiers.new(name="Armature", type="ARMATURE")
    modifier.object = armature
    mesh.parent = armature

    pose_bone = armature.pose.bones["Root"]
    pose_bone.rotation_mode = "XYZ"
    for frame, angle in ((1, 0.0), (13, 0.6), (25, 0.0)):
        pose_bone.rotation_euler[1] = angle
        pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame, group="Root")
    for frame, distance in ((1, 0.0), (13, 1.0), (25, 2.0)):
        armature.location[0] = distance
        armature.keyframe_insert(data_path="location", frame=frame, group="RootMotion")
    armature.animation_data.action.name = "MotionClip"

    bpy.ops.export_scene.gltf(
        filepath=str(output), export_format="GLB", export_animations=True,
        export_frame_range=True, export_skins=True,
    )
    print("[AssetSync] Created animated fixture: {0}".format(output))


if __name__ == "__main__":
    main()
