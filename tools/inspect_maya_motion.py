"""Inspect FBX takes and imported animation using Maya's standalone Python.

Run with mayapy:
    mayapy tools/inspect_maya_motion.py input.fbx [take-index]
"""

import json
import sys
from pathlib import Path

import maya.cmds as cmds
import maya.mel as mel
import maya.standalone


def mel_path(path):
    return str(path).replace("\\", "/").replace('"', '\\"')


def main():
    if len(sys.argv) not in {2, 3}:
        raise RuntimeError("Expected an FBX path and optional take index")
    source = Path(sys.argv[1]).resolve()
    requested_take = int(sys.argv[2]) if len(sys.argv) == 3 else 1

    maya.standalone.initialize(name="python")
    cmds.loadPlugin("fbxmaya", quiet=True)
    path = mel_path(source)
    mel.eval('FBXRead -f "{0}";'.format(path))
    take_count = int(mel.eval("FBXGetTakeCount;") or 0)
    takes = [str(mel.eval("FBXGetTakeName {0};".format(index))) for index in range(1, take_count + 1)]
    mel.eval("FBXClose;")

    mel.eval("FBXResetImport;")
    mel.eval("FBXImportMode -v add;")
    mel.eval("FBXImportFillTimeline -v true;")
    mel.eval("FBXImportQuaternion -v resample;")
    mel.eval('FBXImport -f "{0}" -t {1};'.format(path, requested_take))

    curves = cmds.ls(type="animCurve") or []
    joints = cmds.ls(type="joint") or []
    meshes = cmds.ls(type="mesh", long=True) or []
    key_times = cmds.keyframe(curves, query=True, timeChange=True) if curves else []
    sample_times = sorted(set(key_times)) if key_times else []
    animated_transforms = sorted(set(cmds.listConnections(curves, destination=True, type="transform") or []))
    motion_samples = {}
    for transform in animated_transforms:
        motion_samples[transform] = []
        for frame in ((sample_times[0], sample_times[-1]) if sample_times else []):
            cmds.currentTime(frame, edit=True)
            motion_samples[transform].append([frame, cmds.xform(transform, query=True, worldSpace=True, translation=True)])
    result = {
        "takes": takes,
        "joints": joints,
        "meshes": meshes,
        "animation_curves": curves,
        "key_range": [min(key_times), max(key_times)] if key_times else [],
        "timeline": [cmds.playbackOptions(query=True, min=True), cmds.playbackOptions(query=True, max=True)],
        "motion_samples": motion_samples,
    }
    print("ASSETSYNC_MOTION_INSPECTION=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
