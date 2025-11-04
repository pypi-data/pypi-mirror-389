from __future__ import annotations

import threading
import time
from hashlib import sha256

from typing import Any
from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from uvicorn import Config, Server

from tpds.helper import make_singleton
from tpds.helper.logger import LogFacility
from tpds.servers.msg_handler import Messages, ResponseMessage


@make_singleton
class WebSocketManager:
    """
    Manage connected websockets and process the messages according to the defined
    tpds messages
    """

    def __init__(self, parent: Any = None) -> None:
        self.clients: dict[str, WebSocket] = {}
        self.logger = LogFacility()
        self.messages = Messages(parent)

    def shutdown(self) -> None:
        for ws in self.clients.values():
            ws.close()

    @staticmethod
    def _get_client_id(ws: WebSocket) -> str:
        if id := getattr(ws, "clientid", None):
            return id
        else:
            ws.clientid = sha256(f"{ws.client}:{ws.client}".encode("utf-8")).hexdigest()[
                :16
            ]
            return ws.clientid

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.log(
            f"Websocket - Connecting {ws.client}:{ws.client} as {self._get_client_id(ws)}"
        )
        self.clients[self._get_client_id(ws)] = ws

    def handle_disconnect(self, ws: WebSocket) -> None:
        self.clients.pop(self._get_client_id(ws), None)

    async def broadcast(self, message: str) -> None:
        for ws in self.clients.values():
            await ws.send_text(message)

    def log(self, msg: str) -> None:
        self.logger.log(msg)

    def parse_incoming(self, msg: str, ws: WebSocket) -> Any:
        _client_id = self._get_client_id(ws)
        self.log(f"Websocket - Recieved {msg} from {_client_id}")
        try:
            return self.messages.decode(msg, _client_id)
        except ValueError:
            self.log(f"Websocket - Ignored malformed message {msg} from {_client_id}")
            return ResponseMessage().json()


async def websocket_handler(ws: WebSocket):
    """
    This handler is used by the FastAPI (Starlette) server to process
    websocket message exchanges
    """
    manager = WebSocketManager()
    await manager.connect(ws)
    try:
        while True:
            message = await ws.receive_text()
            if response := manager.parse_incoming(message, ws):
                manager.log(f"Websocket - Response: {response}")
                await ws.send_text(response)

    except WebSocketDisconnect:
        manager.handle_disconnect(ws)


class WebSocketServer:
    def __init__(self, host_ip: str = "127.0.0.1", port: int = 1302, parent: Any = None) -> None:
        """
        Init function to get Uvicorn server parameters
        """
        self._manager: WebSocketManager = WebSocketManager(parent=parent)
        self._thread = None
        self._server: Server = None
        self._result: int = 0
        self._host_ip: str = host_ip
        self._port: int = port

    @property
    def host_ip(self):
        return self._host_ip

    @property
    def port(self):
        return self._port

    def _config_server(self):
        _inst = Starlette(
            debug=True,
            routes=[
                WebSocketRoute("/", websocket_handler),
                WebSocketRoute("/websocket", websocket_handler),
            ],
        )
        _config = Config(_inst, host=self.host_ip, port=self.port, log_level="info")
        self._server = Server(config=_config)

    def _can_start_server(self):
        if self._server is None:
            return True
        else:
            return not self._server.started

    def _run_api(self) -> None:
        self._server.run()

    def _wait_for_server_to_start(self) -> bool:
        while self._thread.is_alive():
            if self._server and self._server.started:
                return True
            time.sleep(1)
        return False

    def start(self) -> None:
        """
        Start Uvicorn server
        """
        if self._can_start_server():
            self._config_server()
            self._thread = threading.Thread(target=self._run_api)
            self._thread.daemon = True
            self._thread.start()
            if self._wait_for_server_to_start():
                return

    def up(self) -> bool:
        return self._server.started if self._server else False

    def stop(self) -> int:
        """
        Stop Uvicorn server
        """
        self._manager.shutdown()
        self._result = 0
        if self._server and self._thread.is_alive():
            # Try gracefull first
            self._server.should_exit = True
            self._thread.join(timeout=10)
            # Try to force exit
            if self._thread.is_alive():
                self._server.force_exit = True
                self._thread.join(timeout=10)
            # Note that the force exit failed as well
            if self._thread.is_alive():
                self._result = -1

        return self._result

    def join(self) -> None:
        """
        Join Uvicorn server process

        Join used to give chance for the background tasks to update the status
        of the object to reflect the termination of the process
        """
        if self._thread and self._thread.is_alive():
            try:
                self._thread.join()
                return self._result
            except BaseException:
                return self.stop()

    def is_alive(self) -> bool:
        """
        Returns process status, True if it is alive and False if it is closed
        """
        self._thread.is_alive()


def _ws_launch():
    ws_server = WebSocketServer(port=1302)
    ws_server.start()
    ws_server.join()


if __name__ == "__main__":
    """
    Directly launch this file for debug/testing
    """
    _ws_launch()
