"""Installable Blender receiver add-on for ComfyUI-AssetSync."""

bl_info = {
    "name": "ComfyUI AssetSync",
    "author": "ComfyUI-AssetSync contributors",
    "version": (0, 2, 0),
    "blender": (3, 6, 0),
    "location": "Edit > Preferences > Add-ons",
    "description": "Receives and imports generated 3D assets from ComfyUI.",
    "category": "Import-Export",
}

import bpy


def _receiver():
    from .assetsync.adapters.blender import receiver
    return receiver


class ASSETSYNC_OT_start_server(bpy.types.Operator):
    bl_idname = "assetsync.start_server"
    bl_label = "Start Server"

    def execute(self, context):
        preferences = context.preferences.addons[__package__].preferences
        try:
            server = _receiver().start(preferences.port)
            preferences.server_running = True
            self.report({"INFO"}, "AssetSync listening on 127.0.0.1:{0}".format(server.port))
            return {"FINISHED"}
        except Exception as exc:
            preferences.server_running = False
            self.report({"ERROR"}, "AssetSync could not start: {0}".format(exc))
            return {"CANCELLED"}


class ASSETSYNC_OT_stop_server(bpy.types.Operator):
    bl_idname = "assetsync.stop_server"
    bl_label = "Stop Server"

    def execute(self, context):
        preferences = context.preferences.addons[__package__].preferences
        _receiver().stop()
        preferences.server_running = False
        self.report({"INFO"}, "AssetSync server stopped")
        return {"FINISHED"}


class AssetSyncPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    port: bpy.props.IntProperty(name="Port", default=18951, min=1024, max=65535)
    auto_start: bpy.props.BoolProperty(name="Start automatically with Blender", default=True)
    server_running: bpy.props.BoolProperty(default=False, options={"HIDDEN"})

    def draw(self, context):
        layout = self.layout
        layout.label(text="Status: " + ("Running" if self.server_running else "Stopped"), icon="CHECKMARK" if self.server_running else "PAUSE")
        layout.label(text="Host: 127.0.0.1")
        layout.prop(self, "port")
        layout.prop(self, "auto_start")
        row = layout.row(align=True)
        row.operator(ASSETSYNC_OT_start_server.bl_idname)
        row.operator(ASSETSYNC_OT_stop_server.bl_idname)


CLASSES = (ASSETSYNC_OT_start_server, ASSETSYNC_OT_stop_server, AssetSyncPreferences)


def _auto_start():
    addon = bpy.context.preferences.addons.get(__package__)
    if addon:
        addon.preferences.server_running = False
    if addon and addon.preferences.auto_start:
        try:
            _receiver().start(addon.preferences.port)
            addon.preferences.server_running = True
            print("[AssetSync] Blender receiver running on 127.0.0.1:{0}".format(addon.preferences.port))
        except Exception as exc:
            print("[AssetSync] Blender receiver could not start: {0}".format(exc))
    return None


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.app.timers.register(_auto_start, first_interval=1.0)


def unregister():
    _receiver().stop()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
