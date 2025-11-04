# (c) 2021 Microchip Technology Inc. and its subsidiaries.

# Subject to your compliance with these terms, you may use Microchip software
# and any derivatives exclusively with Microchip products. It is your
# responsibility to comply with third party license terms applicable to your
# use of third party software (including open source software) that may
# accompany Microchip software.

# THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS".  NO WARRANTIES, WHETHER
# EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE, INCLUDING ANY IMPLIED
# WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR
# PURPOSE. IN NO EVENT WILL MICROCHIP BE LIABLE FOR ANY INDIRECT, SPECIAL,
# PUNITIVE, INCIDENTAL OR CONSEQUENTIAL LOSS, DAMAGE, COST OR EXPENSE OF ANY
# KIND WHATSOEVER RELATED TO THE SOFTWARE, HOWEVER CAUSED, EVEN IF MICROCHIP
# HAS BEEN ADVISED OF THE POSSIBILITY OR THE DAMAGES ARE FORESEEABLE. TO THE
# FULLEST EXTENT ALLOWED BY LAW, MICROCHIP'S TOTAL LIABILITY ON ALL CLAIMS IN
# ANY WAY RELATED TO THIS SOFTWARE WILL NOT EXCEED THE AMOUNT OF FEES, IF ANY,
# THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR THIS SOFTWARE.

import threading
import time

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from uvicorn import Config, Server

from tpds.configurator.api import configurator_api_router
from tpds.servers.websocket_server import websocket_handler

from .api.router import api_router
from .api.usecases import usecase_router
from .loader import load_app_root, load_usecases

try:
    from tpds.version.core import __version__
except ImportError:
    __version__ = "2.2.0"

description = """
TPDS API helps to explore various operations of Microchip Crypto Products.
"""


def _initializeApiInstance(port):
    # Global fastapi instance that will host usecase frontends and apis
    api_inst = FastAPI(
        title="TPDS API",
        description=description,
        version=__version__,
        servers=[{"url": f"http://localhost:{port}", "description": "Default"}],
    )
    api_inst.include_router(api_router)

    # Setup CORS for local access from other servers we'll be running
    origins = [
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        f"http://127.0.0.1:{port}",
        "http://localhost",
        "http://localhost:3000",
        f"http://localhost:{port}",
        "https://www.youtube.com",
        "https://www.youku.com/",
    ]
    api_inst.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Extend the app by loading usecases and plugins
    load_usecases(api_inst)

    # Attach the usecases
    api_inst.include_router(usecase_router, prefix="/usecases", tags=["Usecases"])

    # Attach the configurator
    api_inst.include_router(configurator_api_router, prefix="/config", tags=["Configurator"])

    # Add a websocket handler
    @api_inst.websocket("/websocket")
    async def websocket_endpoint(ws: WebSocket):
        await websocket_handler(ws)

    # Attach the root application - must be done after all attachments
    load_app_root(api_inst)

    # Exception handler for 404 Page
    @api_inst.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request, exc):
        return RedirectResponse("/")

    return api_inst


class TpdsApiServer:
    def __init__(self, host_ip="127.0.0.1", ports=[5001], port=None) -> None:
        """
        Init function to get Uvicorn server parameters
        """
        self._thread = None
        self._server = None
        self._result = 0
        self._host_ip = host_ip
        self._ports = [port] if port else ports
        self._port = 0

    @property
    def host_ip(self):
        return self._host_ip

    @property
    def port(self):
        return self._ports[self._port]

    def _config_server(self):
        if self._port < len(self._ports):
            api_inst = _initializeApiInstance(self.port)
            config = Config(api_inst, host=self.host_ip, port=self.port, log_level="info")
            self._server = Server(config=config)
        else:
            raise ValueError(f"Unable to find an open port in {self._ports}")

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
        while self._can_start_server():
            self._config_server()
            self._thread = threading.Thread(target=self._run_api)
            self._thread.daemon = True
            self._thread.start()
            if self._wait_for_server_to_start():
                return
            else:
                self._port += 1

    def up(self) -> bool:
        return self._server.started if self._server else False

    def stop(self) -> int:
        """
        Stop Uvicorn server
        """
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


def launch():
    api_server = TpdsApiServer(ports=range(5001, 5010))
    api_server.start()
    api_server.join()


if __name__ == "__main__":
    """
    Directly launch this file for debug/testing
    """
    launch()
