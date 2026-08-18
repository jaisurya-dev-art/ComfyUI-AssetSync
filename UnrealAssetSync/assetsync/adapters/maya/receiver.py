from typing import Any, Dict

from ...core.networking import ReceiverServer
from ...core.protocol import response
from ..common import parse_import_request
from .importer import import_asset


_server = None


def _handle(message: Dict[str, Any]) -> Dict[str, Any]:
    try:
        import maya.utils
        asset, options = parse_import_request(message, "maya")
        return maya.utils.executeInMainThreadWithResult(lambda: import_asset(asset, options))
    except Exception as exc:
        return response(False, "Maya import failed: {0}".format(exc))


def start(port: int = 18952):
    global _server
    if _server is None:
        _server = ReceiverServer(_handle, port).start()
    return _server


def stop():
    global _server
    if _server is not None:
        _server.stop()
        _server = None

