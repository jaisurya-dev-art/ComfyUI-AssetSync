bl_info = {
    "name": "ComfyUI AssetSync Receiver",
    "author": "ComfyUI-AssetSync contributors",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > AssetSync",
    "category": "Import-Export",
}

import sys
from pathlib import Path

import bpy


_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


class ASSETSYNC_OT_receiver(bpy.types.Operator):
    bl_idname = "assetsync.toggle_receiver"
    bl_label = "Toggle AssetSync Receiver"

    def execute(self, context):
        from assetsync.adapters.blender import receiver
        if getattr(context.scene, "assetsync_receiver_running", False):
            receiver.stop()
            context.scene.assetsync_receiver_running = False
            self.report({"INFO"}, "AssetSync Receiver stopped")
        else:
            port = context.scene.assetsync_receiver_port
            receiver.start(port)
            context.scene.assetsync_receiver_running = True
            self.report({"INFO"}, "AssetSync Receiver running on 127.0.0.1:{0}".format(port))
        return {"FINISHED"}


class ASSETSYNC_PT_panel(bpy.types.Panel):
    bl_label = "AssetSync Receiver"
    bl_idname = "ASSETSYNC_PT_receiver"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AssetSync"

    def draw(self, context):
        layout = self.layout
        running = context.scene.assetsync_receiver_running
        layout.label(text="Status: " + ("Running" if running else "Stopped"), icon="CHECKMARK" if running else "PAUSE")
        layout.prop(context.scene, "assetsync_receiver_port")
        layout.operator("assetsync.toggle_receiver", text="Stop Receiver" if running else "Start Receiver")


_CLASSES = (ASSETSYNC_OT_receiver, ASSETSYNC_PT_panel)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.assetsync_receiver_running = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.assetsync_receiver_port = bpy.props.IntProperty(default=18951, min=1024, max=65535)


def unregister():
    from assetsync.adapters.blender import receiver
    receiver.stop()
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.assetsync_receiver_running
    del bpy.types.Scene.assetsync_receiver_port

