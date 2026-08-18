"""Blender-side diagnostic for comparing glTF and FBX mesh corner normals."""

import json
import sys
from pathlib import Path

import bpy


def mesh_stats(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    suffix = Path(path).suffix.lower()
    if suffix in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=path)
    elif suffix == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        raise ValueError("Expected GLB, GLTF, or FBX")
    result = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        mesh = obj.data
        mesh.calc_loop_triangles()
        corner_normals = mesh.corner_normals
        dots = []
        for triangle in mesh.loop_triangles:
            face_normal = mesh.polygons[triangle.polygon_index].normal
            for loop_index in triangle.loops:
                dots.append(face_normal.dot(corner_normals[loop_index].vector))
        result.append({
            "name": obj.name,
            "vertices": len(mesh.vertices),
            "polygons": len(mesh.polygons),
            "triangles": len(mesh.loop_triangles),
            "determinant": obj.matrix_world.to_3x3().determinant(),
            "normal_dot_min": min(dots) if dots else None,
            "normal_dot_average": sum(dots) / len(dots) if dots else None,
            "normal_dot_below_0_1": sum(value < 0.1 for value in dots),
            "normal_dot_below_0_5": sum(value < 0.5 for value in dots),
        })
    return result


def main():
    paths = sys.argv[sys.argv.index("--") + 1:]
    print(json.dumps({path: mesh_stats(path) for path in paths}, indent=2))


if __name__ == "__main__":
    main()
