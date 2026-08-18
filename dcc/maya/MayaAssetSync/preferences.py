"""Small Maya receiver status/control window."""

import maya.cmds as cmds

WINDOW_NAME = "MayaAssetSyncWindow"


def _start(*_args):
    from assetsync.adapters.maya import receiver
    try:
        port = int(cmds.intFieldGrp("MayaAssetSync_port", query=True, value1=True))
        receiver.start(port)
        cmds.confirmDialog(title="AssetSync", message="Receiver running on 127.0.0.1:{0}".format(port), button=["OK"])
    except Exception as exc:
        cmds.warning("AssetSync could not start: {0}".format(exc))


def _stop(*_args):
    from assetsync.adapters.maya import receiver
    receiver.stop()
    cmds.confirmDialog(title="AssetSync", message="Receiver stopped", button=["OK"])


def show_window():
    if cmds.window(WINDOW_NAME, exists=True):
        cmds.deleteUI(WINDOW_NAME)
    window = cmds.window(WINDOW_NAME, title="ComfyUI AssetSync", widthHeight=(330, 120))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=8, columnOffset=("both", 10))
    cmds.text(label="AssetSync Receiver", font="boldLabelFont", align="center")
    cmds.text(label="Host: 127.0.0.1   Default status: auto-started")
    cmds.intFieldGrp("MayaAssetSync_port", label="Port", value1=18952)
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(155, 155))
    cmds.button(label="Start Receiver", command=_start)
    cmds.button(label="Stop Receiver", command=_stop)
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.showWindow(window)

