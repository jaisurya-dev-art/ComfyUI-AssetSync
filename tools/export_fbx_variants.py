"""Generate FBX shading variants for Maya compatibility testing."""

import sys
from pathlib import Path

import bpy


def main():
    source, output_directory = sys.argv[sys.argv.index("--") + 1:]
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=source)
    variants = {
        "off": {"mesh_smooth_type": "OFF", "use_triangles": False},
        "face": {"mesh_smooth_type": "FACE", "use_triangles": False},
        "edge": {"mesh_smooth_type": "EDGE", "use_triangles": False},
        "face_triangles": {"mesh_smooth_type": "FACE", "use_triangles": True},
    }
    for name, settings in variants.items():
        path = output / (name + ".fbx")
        bpy.ops.export_scene.fbx(
            filepath=str(path), use_selection=False, path_mode="COPY", embed_textures=False,
            add_leaf_bones=False, use_mesh_modifiers=False, **settings
        )
        print("[AssetSync] Wrote", path)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.length_unit = "METERS"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.ops.export_scene.fbx(
        filepath=str(output / "metric.fbx"), use_selection=False, path_mode="COPY",
        embed_textures=False, add_leaf_bones=False, use_mesh_modifiers=False,
        mesh_smooth_type="FACE", use_triangles=False, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE",
    )
    bpy.ops.export_scene.fbx(
        filepath=str(output / "scale100.fbx"), use_selection=False, path_mode="COPY",
        embed_textures=False, add_leaf_bones=False, use_mesh_modifiers=False,
        mesh_smooth_type="FACE", use_triangles=False, global_scale=100.0,
        apply_unit_scale=False, apply_scale_options="FBX_SCALE_NONE",
    )
    bpy.ops.object.select_all(action="DESELECT")
    roots = [obj for obj in bpy.context.scene.objects if obj.parent is None]
    for obj in roots:
        obj.select_set(True)
        obj.scale = tuple(value * 100.0 for value in obj.scale)
    bpy.context.view_layer.objects.active = roots[0]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.export_scene.fbx(
        filepath=str(output / "baked_centimeters.fbx"), use_selection=False,
        path_mode="COPY", embed_textures=False, add_leaf_bones=False,
        use_mesh_modifiers=False, mesh_smooth_type="FACE", use_triangles=False,
    )


if __name__ == "__main__":
    main()
