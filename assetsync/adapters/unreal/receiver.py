import queue
import threading
from typing import Any, Dict

from ...core.networking import ReceiverServer
from ...core.protocol import response
from ..common import parse_import_request
from .importer import import_asset


_tasks = queue.Queue()
_server = None
_tick_handle = None


def _tick(_delta_time):
    try:
        callback, event, holder = _tasks.get_nowait()
    except queue.Empty:
        return
    try:
        holder["result"] = callback()
    except Exception as exc:
        holder["result"] = response(False, "Unreal import failed: {0}".format(exc))
    finally:
        event.set()


def _handle(message: Dict[str, Any]) -> Dict[str, Any]:
    try:
        asset, options = parse_import_request(message, "unreal")
    except Exception as exc:
        return response(False, str(exc))
    event, holder = threading.Event(), {}
    _tasks.put((lambda: import_asset(asset, options), event, holder))
    if not event.wait(115.0):
        return response(False, "Unreal did not process the import on its editor thread in time.", asset.asset_id)
    return holder["result"]


def start(port: int = 18953):
    global _server, _tick_handle
    import unreal
    if _tick_handle is None:
        _tick_handle = unreal.register_slate_post_tick_callback(_tick)
    if _server is None:
        _server = ReceiverServer(_handle, port).start()
    return _server


def stop():
    global _server, _tick_handle
    if _server is not None:
        _server.stop()
        _server = None
    if _tick_handle is not None:
        import unreal
        unreal.unregister_slate_post_tick_callback(_tick_handle)
        _tick_handle = None

