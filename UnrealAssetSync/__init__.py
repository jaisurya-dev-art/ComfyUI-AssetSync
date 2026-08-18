"""Unreal Editor plugin entry point for ComfyUI-AssetSync."""

import atexit

_started = False


def startup():
    global _started
    if _started:
        return
    import unreal
    from .assetsync.adapters.unreal import receiver
    server = receiver.start(18953)
    _started = True
    unreal.log("AssetSync receiver running on 127.0.0.1:{0}".format(server.port))


def shutdown():
    global _started
    if not _started:
        return
    from .assetsync.adapters.unreal import receiver
    receiver.stop()
    _started = False


atexit.register(shutdown)

