from __future__ import annotations

"""
Tools to manage the full TPDS backend
"""
import os
import signal
import sys
import time
import webbrowser
from typing import Any

from tpds.api import TpdsApiServer
from tpds.helper import LogFacility, ProcessingUtils
from tpds.servers import JupyterServer, WebSocketServer
from tpds.settings import TrustPlatformSettings
from tpds.usecase_collector import Collector

_tpds_running = False


def sigint_handler(sig_id, frame):
    global _tpds_running
    _tpds_running = False


class TpdsBackend:
    """
    Manage TPDS backend services
    """

    __shared_state: dict[str, Any] = {}

    def __new__(cls, **kwargs: str) -> Any:
        # Only ever allow one global instance of the usecase collector
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self, parent: Any = None) -> None:
        if not self.__shared_state:
            self._config = TrustPlatformSettings()
            self._log = LogFacility()
            self._proc = ProcessingUtils()
            self._usecases = Collector()
            self._websocket_server = None
            self._voila = []
            self._api_server = None
            self._parent = parent

    def start(self) -> None:
        # Start the websocket server in a separate thread
        self._websocket_server = WebSocketServer(parent=self._parent if self._parent else self)
        self._websocket_server.start()

        # Start new API Server and usecase collector
        self._api_server = TpdsApiServer(ports=range(5001, 5010))
        self._api_server.start()

        self.start_jupyter()

    def _check_jupyter_instances(self, path):
        for js in self._voila:
            if js._start_directory == path:
                return True
        return False

    def start_jupyter(self):
        for uc_path_info in self._usecases.get_search_paths():
            if uc_path_info.get("notebook", False):
                uc_path = uc_path_info["path"]
                if not self._check_jupyter_instances(uc_path):
                    js = JupyterServer(
                        port=self._config.settings.jupyter_port, start_directory=uc_path
                    )
                    js.start_jupyter()
                    self._voila += [js]

    def stop(self) -> None:
        if self._websocket_server:
            self._websocket_server.stop()

        for js in self._voila:
            js.stop_jupyter()

        if self._api_server:
            self._api_server.stop()

    def run(self) -> None:
        """
        Run until an exit signal is encountered
        """
        self.start()

        webbrowser.open(f"http://localhost:{self._api_server.port}")

        if sys.platform == "win32":
            global _tpds_running
            _tpds_running = True
            signal.signal(signal.SIGINT, sigint_handler)

            while _tpds_running:
                time.sleep(1)
        else:
            signal.sigwait([signal.SIGINT])

        self.stop()

    def log(self, message) -> None:
        self._log.log(message)

    def is_ready(self) -> bool:
        return self._api_server and self._api_server.up()

    def api_port(self) -> int:
        return self._api_server.port

    def get_jupyter_path(self, path) -> str:
        for js in self._voila:
            if os.path.exists(os.path.join(js._start_directory, path)):
                return f"{js._web_address}voila/render/{path}"

    def open_url(self, path):
        webbrowser.open(path)


def launch_tpds_core():
    """
    Launch all backend services used by TPDS
    """
    # The websocket server and message handlers are all based on QT so they
    # require this to be run as part of a QApplication
    backend = TpdsBackend()
    backend.run()


__all__ = ["launch_tpds_core", "TpdsBackend"]


if __name__ == "__main__":
    launch_tpds_core()
