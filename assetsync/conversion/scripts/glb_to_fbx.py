"""Executed by Blender: import glTF, externalize images, and export FBX."""

import json
import re
import sys
from pathlib import Path

import bpy

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from assetsync.conversion.gltf_inspector import inspect_gltf


def select_animation(clips, requested):
    if not clips:
        raise RuntimeError("The input model contains no glTF animation clips.")
    if not requested:
        return clips[0]
    for clip in clips:
        if clip["name"].casefold() == requested.casefold():
            return clip
    raise RuntimeError(
        "Animation clip '{0}' was not found. Available clips: {1}".format(
            requested, ", ".join(clip["name"] for clip in clips),
        )
    )


def activate_animation(name):
    """Solo one imported glTF NLA clip so FBX emits one predictable take."""
    matched = False
    for obj in bpy.data.objects:
        animation_data = obj.animation_data
        if not animation_data:
            continue
        active = animation_data.action
        active_matches = bool(active and active.name.casefold() == name.casefold())
        matching_track = False
        for track in animation_data.nla_tracks:
            track_matches = track.name.casefold() == name.casefold() or any(
                strip.action and strip.action.name.casefold() == name.casefold()
                for strip in track.strips
            )
            track.mute = not track_matches
            matching_track = matching_track or track_matches
        if matching_track:
            animation_data.action = None
            matched = True
        elif active_matches:
            matched = True
        elif active:
            animation_data.action = None
    if not matched:
        raise RuntimeError("Blender imported the model but could not activate animation clip '{0}'.".format(name))


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
    if len(args) not in {4, 5}:
        raise RuntimeError("Expected input, output, texture directory, manifest, and optional conversion settings")
    source, output, texture_dir, manifest = map(Path, args[:4])
    options = json.loads(args[4]) if len(args) == 5 else {}
    metadata = inspect_gltf(source)
    motion_transfer = options.get("transfer_mode") == "motion"
    selected = None
    if motion_transfer:
        selected = select_animation(metadata["animation_clips"], str(options.get("animation_clip") or ""))
        if not options.get("include_source_model", False) and "weights" in selected["target_paths"]:
            raise RuntimeError(
                "The selected clip animates morph targets. Enable include_source_model to preserve that motion."
            )
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    if selected:
        activate_animation(selected["name"])
    textures = externalize_images(texture_dir)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    object_types = {"ARMATURE", "EMPTY"} if motion_transfer and not options.get("include_source_model", False) else {"ARMATURE", "CAMERA", "EMPTY", "LIGHT", "MESH", "OTHER"}
    bpy.ops.export_scene.fbx(
        filepath=str(output), use_selection=False, path_mode="COPY", embed_textures=False,
        add_leaf_bones=False, use_mesh_modifiers=False, mesh_smooth_type="FACE",
        object_types=object_types, bake_anim=True, bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=True, bake_anim_use_all_actions=not motion_transfer,
        bake_anim_force_startend_keying=True, bake_anim_step=1.0,
        bake_anim_simplify_factor=0.0,
    )
    metadata.update({
        "success": True,
        "textures": textures,
        "selected_animation": selected["name"] if selected else "",
    })
    Path(manifest).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print("[AssetSync] Exported {0} with {1} textures".format(output, len(textures)))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("[AssetSync] Conversion failed: {0}".format(exc), file=sys.stderr)
        raise
