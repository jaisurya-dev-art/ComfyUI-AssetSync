import queue
import threading
from typing import Any, Dict

from ...core.networking import ReceiverServer
from ...core.protocol import response
from ..common import parse_import_request
from .importer import import_asset


_tasks = queue.Queue()
_server = None
_timer_registered = False


def _pump():
    try:
        callback, event, holder = _tasks.get_nowait()
    except queue.Empty:
        return 0.1
    try:
        holder["result"] = callback()
    except Exception as exc:
        holder["result"] = response(False, "Blender import failed: {0}".format(exc))
    finally:
        event.set()
    return 0.01


def _handle(message: Dict[str, Any]) -> Dict[str, Any]:
    try:
        asset, options = parse_import_request(message, "blender")
    except Exception as exc:
        return response(False, str(exc))
    event, holder = threading.Event(), {}
    _tasks.put((lambda: import_asset(asset, options), event, holder))
    if not event.wait(115.0):
        return response(False, "Blender did not process the import on its main thread in time.", asset.asset_id)
    return holder["result"]


def start(port: int = 18951):
    global _server, _timer_registered
    import bpy
    if not _timer_registered:
        bpy.app.timers.register(_pump, first_interval=0.1, persistent=True)
        _timer_registered = True
    if _server is None:
        _server = ReceiverServer(_handle, port).start()
    return _server


def stop():
    global _server, _timer_registered
    if _server is not None:
        _server.stop()
        _server = None
    if _timer_registered:
        try:
            import bpy
            if bpy.app.timers.is_registered(_pump):
                bpy.app.timers.unregister(_pump)
        except Exception:
            pass
        _timer_registered = False
