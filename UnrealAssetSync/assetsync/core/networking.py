"""Small localhost-only HTTP/JSON transport."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .errors import ReceiverError


JsonHandler = Callable[[Dict[str, Any]], Dict[str, Any]]


class AssetSyncClient:
    def __init__(self, host: str = "127.0.0.1", timeout: float = 120.0):
        self.host = host
        self.timeout = timeout

    def send(self, port: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            "http://{0}:{1}/v1/assets".format(self.host, port), data=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))}, method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as result:
                response = json.loads(result.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise ReceiverError("Receiver rejected the request ({0}): {1}".format(exc.code, detail))
        except (URLError, OSError) as exc:
            raise ReceiverError("AssetSync receiver is not running or did not respond: {0}".format(exc))
        except ValueError:
            raise ReceiverError("AssetSync receiver returned invalid JSON.")
        if not response.get("success"):
            raise ReceiverError(response.get("message") or "The DCC could not import the asset.")
        return response


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: Tuple[str, int], handler: type, callback: JsonHandler):
        super().__init__(address, handler)
        self.callback = callback


class _Handler(BaseHTTPRequestHandler):
    server_version = "AssetSync/1"

    def _write(self, code: int, value: Dict[str, Any]) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path != "/v1/status":
            self._write(404, {"success": False, "message": "Not found"})
            return
        self._write(200, {"success": True, "message": "AssetSync Receiver is running"})

    def do_POST(self) -> None:
        if self.path != "/v1/assets":
            self._write(404, {"success": False, "message": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1024 * 1024:
                raise ValueError("Invalid request size")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self._write(200, self.server.callback(payload))  # type: ignore[attr-defined]
        except Exception as exc:
            self._write(400, {"success": False, "message": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        return


class ReceiverServer:
    def __init__(self, callback: JsonHandler, port: int, host: str = "127.0.0.1"):
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("AssetSync receivers bind to localhost by default.")
        self._server = _Server((host, port), _Handler, callback)
        self._thread: Optional[threading.Thread] = None

    @property
    def port(self) -> int:
        return int(self._server.server_address[1])

    def start(self) -> "ReceiverServer":
        if not self._thread or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._server.serve_forever, name="AssetSyncReceiver", daemon=True)
            self._thread.start()
        return self

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        if self._thread:
            self._thread.join(timeout=2.0)

