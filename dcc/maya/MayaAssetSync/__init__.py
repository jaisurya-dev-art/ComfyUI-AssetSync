"""Maya plug-in registration for the AssetSync receiver."""

import maya.cmds as cmds
import maya.api.OpenMaya as om

PLUGIN_VERSION = "0.2.0"


def _start_server():
    try:
        from assetsync.adapters.maya import receiver
        receiver.start(18952)
        print("[AssetSync] Maya receiver running on 127.0.0.1:18952")
    except Exception as exc:
        cmds.warning("AssetSync receiver could not start: {0}".format(exc))


def initializePlugin(mobject):
    om.MFnPlugin(mobject, "ComfyUI AssetSync", PLUGIN_VERSION, "Any")
    cmds.evalDeferred(_start_server)


def uninitializePlugin(mobject):
    try:
        from assetsync.adapters.maya import receiver
        receiver.stop()
    except Exception as exc:
        cmds.warning("AssetSync receiver could not stop cleanly: {0}".format(exc))

