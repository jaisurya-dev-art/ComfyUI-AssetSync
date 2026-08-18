"""Executed by Blender: import glTF, externalize images, and export FBX."""

import json
import re
import struct
import sys
from pathlib import Path

import bpy


def uses_double_sided_material(source):
    """Read the glTF flag directly; FBX has no reliable equivalent for Maya VP2."""
    try:
        if source.suffix.lower() == ".gltf":
            document = json.loads(source.read_text(encoding="utf-8"))
        else:
            with source.open("rb") as stream:
                header = stream.read(12)
                if len(header) != 12 or header[:4] != b"glTF":
                    return False
                chunk_length, chunk_type = struct.unpack("<II", stream.read(8))
                if chunk_type != 0x4E4F534A:
                    return False
                document = json.loads(stream.read(chunk_length).decode("utf-8").rstrip("\x00 \t\r\n"))
        return any(bool(material.get("doubleSided")) for material in document.get("materials", []))
    except Exception as exc:
        print("[AssetSync] Could not inspect glTF material sidedness: {0}".format(exc))
        return False


def safe_name(value):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value or "Texture").strip(" .")
    return name or "Texture"


def unique_path(folder, stem, suffix):
    candidate = folder / (stem + suffix)
    index = 1
    while candidate.exists():
        candidate = folder / ("{0}_{1}{2}".format(stem, index, suffix))
        index += 1
    return candidate


def externalize_images(folder):
    folder.mkdir(parents=True, exist_ok=True)
    result = []
    for image in bpy.data.images:
        if image.source not in {"FILE", "GENERATED"} or image.name == "Render Result":
            continue
        original = Path(bpy.path.abspath(image.filepath)) if image.filepath else None
        suffix = original.suffix.lower() if original and original.suffix else ".png"
        if suffix not in {".png", ".jpg", ".jpeg", ".tga", ".bmp", ".tif", ".tiff", ".exr"}:
            suffix = ".png"
        target = unique_path(folder, safe_name(original.stem if original else image.name), suffix)
        try:
            if image.packed_file:
                image.filepath_raw = str(target)
                if suffix == ".png":
                    image.file_format = "PNG"
                image.save()
            elif original and original.is_file():
                target.write_bytes(original.read_bytes())
            else:
                image.filepath_raw = str(target)
                image.file_format = "PNG"
                image.save()
            image.filepath = str(target)
            image.reload()
            result.append(str(target.resolve()))
        except Exception as exc:
            print("[AssetSync] Could not externalize image {0}: {1}".format(image.name, exc))
    return result


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 4:
        raise RuntimeError("Expected input, output, texture directory, and manifest paths")
    source, output, texture_dir, manifest = map(Path, args)
    double_sided = uses_double_sided_material(source)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    textures = externalize_images(texture_dir)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(output), use_selection=False, path_mode="COPY", embed_textures=False,
        add_leaf_bones=False, use_mesh_modifiers=False, mesh_smooth_type="FACE",
    )
    Path(manifest).write_text(json.dumps({
        "success": True, "textures": textures, "double_sided": double_sided,
    }, indent=2), encoding="utf-8")
    print("[AssetSync] Exported {0} with {1} textures".format(output, len(textures)))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("[AssetSync] Conversion failed: {0}".format(exc), file=sys.stderr)
        raise
