"""A local stand-in for the Slack Web API and Socket Mode, for Keel's tests.

Issue #187: `keel chat bridge` talks to Slack. Its validation scenarios run
against this server instead, so they need no workspace, no token, and no
network — the mock sits at the system boundary, and Keel's own modules run
for real. It models only what the bridge uses, with the shapes Slack's public
documentation gives (design A2): a real run is the evidence that Slack agrees.

Web API: `POST /api/<method>` with a JSON or form body answers `ok: true` and
records the call. `chat.postMessage` assigns increasing `ts` values and keeps
the message, with its metadata, for `conversations.history`.
`apps.connections.open` returns a `ws://` URL served by the same process.

Socket Mode: the server speaks just enough RFC 6455 to push envelopes to a
connected client and collect its acknowledgements.

Tests drive the server through methods on `FakeSlack`, not over HTTP.
"""

from __future__ import annotations

import base64
import hashlib
import json
import socket
import struct
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WS_MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def ws_frame(text: str) -> bytes:
    data = text.encode("utf-8")
    header = bytearray([0x81])
    if len(data) < 126:
        header.append(len(data))
    elif len(data) < 65536:
        header.append(126)
        header += struct.pack(">H", len(data))
    else:
        header.append(127)
        header += struct.pack(">Q", len(data))
    return bytes(header) + data


class FakeSlack:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.messages: dict[str, list[dict]] = {}
        self.rate_limit_next: list[tuple[str, int]] = []
        self.lock = threading.Lock()
        # Later than any `ts` a test writes by hand, so what this server assigns
        # always sorts after the events a test pushed itself.
        self.next_ts = 1_900_000_000
        self.sockets: list[socket.socket] = []
        self.acks: list[str] = []
        self.connections_opened = 0
        # A token's identity, as `auth.test` and its posts report it. A token
        # not listed is the shared app's bot.
        self.identities: dict[str, dict] = {}
        # (token, channel) pairs `chat.postMessage` answers with
        # `not_in_channel`, for a bot nobody invited.
        self.not_in_channel: set[tuple[str, str]] = set()
        # Which app token each Socket Mode connection was opened with.
        self.socket_apps: dict[socket.socket, str] = {}
        self.pending_apps: dict[str, str] = {}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    # --- lifecycle -----------------------------------------------------------

    def __enter__(self) -> "FakeSlack":
        self.thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.drop_connections()
        self.server.shutdown()
        self.server.server_close()

    @property
    def api_base(self) -> str:
        return f"http://127.0.0.1:{self.port}/api"

    # --- test controls -------------------------------------------------------

    def rate_limit(self, method: str, retry_after: int) -> None:
        """Answer the next call of `method` with HTTP 429 and Retry-After."""
        with self.lock:
            self.rate_limit_next.append((method, retry_after))

    def calls_to(self, method: str) -> list[dict]:
        with self.lock:
            return [call for call in self.calls if call["method"] == method and not call.get("rate_limited")]

    def add_history(self, channel: str, message: dict) -> dict:
        """A message Slack holds that the bridge has not been told about."""
        with self.lock:
            stored = {"ts": self._ts(), "type": "message", **message}
            self.messages.setdefault(channel, []).append(stored)
            return stored

    def identify(self, token: str, user_id: str, bot_id: str) -> None:
        """Make `token` a bot of its own, as a role's app is."""
        with self.lock:
            self.identities[token] = {"user_id": user_id, "bot_id": bot_id}

    def push(self, payload: dict, kind: str = "events_api", app: str | None = None) -> str:
        """Send one Socket Mode envelope to every connected client, or only to
        the connections opened with app token `app`."""
        with self.lock:
            envelope_id = f"env-{self._ts()}"
        self._broadcast(json.dumps({"envelope_id": envelope_id, "type": kind, "payload": payload, "accepts_response_payload": False}), app)
        return envelope_id

    def sockets_for(self, app: str) -> list[socket.socket]:
        return [sock for sock in list(self.sockets) if self.socket_apps.get(sock) == app]

    def push_raw(self, message: dict) -> None:
        self._broadcast(json.dumps(message))

    def drop_connections(self) -> None:
        for sock in list(self.sockets):
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass
        self.sockets.clear()

    @staticmethod
    def wait_for(predicate, timeout: float = 10.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if predicate():
                return True
            time.sleep(0.05)
        return bool(predicate())

    # --- internals -----------------------------------------------------------

    def _ts(self) -> str:
        self.next_ts += 1
        return f"{self.next_ts}.000100"

    def _broadcast(self, text: str, app: str | None = None) -> None:
        frame = ws_frame(text)
        for sock in list(self.sockets):
            if app is not None and self.socket_apps.get(sock) != app:
                continue
            try:
                sock.sendall(frame)
            except OSError:
                pass

    def _answer(self, method: str, params: dict) -> tuple[int, dict, dict]:
        with self.lock:
            for index, (limited, retry_after) in enumerate(self.rate_limit_next):
                if limited == method:
                    del self.rate_limit_next[index]
                    self.calls.append({"method": method, "params": params, "rate_limited": True, "at": time.time()})
                    return 429, {"Retry-After": str(retry_after)}, {"ok": False, "error": "ratelimited"}
            self.calls.append({"method": method, "params": params, "at": time.time()})
            token = str(params.get("_auth", "")).removeprefix("Bearer ")
            identity = self.identities.get(token, {"user_id": "UBOT", "bot_id": "BBOT"})
            if method == "auth.test":
                return 200, {}, {"ok": True, **identity, "team_id": "T1"}
            if method == "apps.connections.open":
                self.connections_opened += 1
                key = f"c{self.connections_opened}"
                self.pending_apps[key] = token
                return 200, {}, {"ok": True, "url": f"ws://127.0.0.1:{self.port}/socket?app={key}"}
            if method == "conversations.open":
                return 200, {}, {"ok": True, "channel": {"id": f"D{params.get('users', '')}"}}
            if method == "chat.postMessage" and (token, params.get("channel", "")) in self.not_in_channel:
                return 200, {}, {"ok": False, "error": "not_in_channel"}
            if method == "chat.postMessage":
                metadata = params.get("metadata")
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)
                message = {
                    "ts": self._ts(),
                    "type": "message",
                    "text": params.get("text", ""),
                    "username": params.get("username"),
                    "bot_id": identity["bot_id"],
                    "metadata": metadata,
                }
                if params.get("thread_ts"):
                    message["thread_ts"] = params["thread_ts"]
                self.messages.setdefault(params.get("channel", ""), []).append(message)
                return 200, {}, {"ok": True, "channel": params.get("channel"), "ts": message["ts"], "message": message}
            if method in ("conversations.history", "conversations.replies"):
                channel = params.get("channel", "")
                oldest = float(params.get("oldest") or 0)
                found = [m for m in self.messages.get(channel, []) if float(m["ts"]) > oldest]
                if method == "conversations.replies":
                    root = params.get("ts")
                    found = [m for m in self.messages.get(channel, []) if m.get("thread_ts") == root or m["ts"] == root]
                if params.get("latest"):
                    latest = float(params["latest"])
                    inclusive = str(params.get("inclusive", "")).lower() in ("1", "true")
                    found = [m for m in found if float(m["ts"]) < latest or (inclusive and float(m["ts"]) == latest)]
                include = str(params.get("include_all_metadata", "")).lower() in ("1", "true")
                shown = [m if include else {k: v for k, v in m.items() if k != "metadata"} for m in found]
                return 200, {}, {"ok": True, "messages": list(reversed(shown)), "has_more": False}
            return 200, {}, {"ok": True}

    def _handler(self):
        fake = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args: object) -> None:
                return

            def do_GET(self) -> None:  # noqa: N802 - http.server API
                if self.path.startswith("/socket"):
                    self._upgrade()
                    return
                query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                self._api({k: v[0] for k, v in query.items()})

            def do_POST(self) -> None:  # noqa: N802 - http.server API
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length).decode("utf-8")
                if "json" in (self.headers.get("Content-Type") or ""):
                    params = json.loads(raw or "{}")
                else:
                    params = {k: v[0] for k, v in urllib.parse.parse_qs(raw).items()}
                self._api(params)

            def _api(self, params: dict) -> None:
                method = urllib.parse.urlparse(self.path).path.rsplit("/", 1)[-1]
                params["_auth"] = self.headers.get("Authorization", "")
                status, headers, body = fake._answer(method, params)
                data = json.dumps(body).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                for key, value in headers.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(data)

            def _upgrade(self) -> None:
                key = self.headers.get("Sec-WebSocket-Key", "")
                accept = base64.b64encode(hashlib.sha1((key + WS_MAGIC).encode()).digest()).decode()
                self.send_response(101, "Switching Protocols")
                self.send_header("Upgrade", "websocket")
                self.send_header("Connection", "Upgrade")
                self.send_header("Sec-WebSocket-Accept", accept)
                self.end_headers()
                self.wfile.flush()
                sock = self.connection
                try:
                    sock.sendall(ws_frame(json.dumps({"type": "hello", "num_connections": len(fake.sockets) + 1})))
                except OSError:
                    return
                fake.sockets.append(sock)
                key = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("app", [""])[0]
                fake.socket_apps[sock] = fake.pending_apps.get(key, "")
                self.close_connection = True
                self._read_frames(sock)

            def _read_frames(self, sock: socket.socket) -> None:
                stream = self.rfile
                while True:
                    try:
                        head = stream.read(2)
                        if not head or len(head) < 2:
                            break
                        opcode = head[0] & 0x0F
                        length = head[1] & 0x7F
                        if length == 126:
                            length = struct.unpack(">H", stream.read(2))[0]
                        elif length == 127:
                            length = struct.unpack(">Q", stream.read(8))[0]
                        mask = stream.read(4) if head[1] & 0x80 else b"\0\0\0\0"
                        data = bytearray(stream.read(length))
                    except (OSError, ValueError, struct.error):
                        break
                    for index in range(len(data)):
                        data[index] ^= mask[index % 4]
                    if opcode == 0x8:
                        break
                    if opcode != 0x1:
                        continue
                    try:
                        message = json.loads(data.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                    if isinstance(message, dict) and message.get("envelope_id"):
                        with fake.lock:
                            fake.acks.append(message["envelope_id"])
                if sock in fake.sockets:
                    fake.sockets.remove(sock)

        return Handler
