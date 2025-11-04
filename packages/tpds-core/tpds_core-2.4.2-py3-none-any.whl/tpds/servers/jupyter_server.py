"""
Jupyter Notebook Server
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading

from tpds.helper import LogFacility, ProcessingUtils
from tpds.settings import TrustPlatformSettings


class JupyterServer:
    """JupyterServer [summary]

    [extended_summary]
    """

    def __init__(
        self,
        exp_version=None,
        port=8888,
        start_directory="",
        config_file=os.path.join(os.path.dirname(__file__), "TPDS_notebook_config.py"),
    ) -> None:
        self._log = LogFacility()
        self._port = port
        self._start_directory = start_directory
        self._config_file = config_file
        self._config = TrustPlatformSettings()
        self._proc = ProcessingUtils()
        self._logger = None

        self.locate_jupyter(exp_version=exp_version)
        self._web_address = None
        self._jupyter_process_handler = None
        self._log.log(
            (
                f"Jupyter Parameters - Port:{self._port}, Start Dir:{self._start_directory},"
                f"Config File:{self._config_file}"
            )
        )

    def locate_jupyter(self, exp_version):
        version = ""
        version, _ = self._proc.run_cmd(
            ["jupyter-notebook", "--version"], err_handling=self._proc.CAPTURE
        )
        self._log.log(f"Searching for {exp_version} and found {version}")

    def start_jupyter(self, start_directory=""):
        self._log.log("Starting Jupyter")

        if start_directory != "":
            self._start_directory = start_directory

        cmd = [
            "jupyter",
            "notebook",
            f"--config={self._config_file}",
            "--NotebookApp.token=" """""",
            "--VoilaConfiguration.template=tpds_tpl",
        ]

        if self._config.settings.develop:
            cmd += ["--VoilaConfiguration.show_tracebacks=True"]

        try:
            # On Windows platform
            # If the current PROCESS GROUP is used CTRL-C-EVENT will kill the
            # parent and everyone in the group we need the subprocess in a
            # new group...
            creationflags: int = subprocess.CREATE_NEW_PROCESS_GROUP
        except AttributeError:
            # Not on Windows
            creationflags = 0

        try:
            my_env = os.environ.copy()
            my_env["PYTHONPATH"] = os.path.pathsep.join(sys.path)
            self._jupyter_app = self._proc.start(
                cmd,
                err_handling=self._proc.LOG,
                cwd=self._start_directory,
                creationflags=creationflags,
                env=my_env,
            )
            attempts = 20
        except Exception as e:
            self._log.log(f"Starting {self._jupyter_exec} process failed with {e}")
            attempts = 0

        self._web_address = None
        while self._web_address is None and attempts > 0:
            # Windows specific line encoding UTF-8 works without problems on
            # osx
            output = self._jupyter_app.stderr.readline().strip()
            self._log.log(output)
            if "http://" in output:
                begining_output = output.find("http://")
                """ Jupyter notebook address is at the end
                of the output starting by http://
                """
                self._web_address = output[begining_output:]
                self._log.log("Jupyter Server found at %s" % self._web_address)
            # jupyter server not found. try again...
            attempts -= 1
        if attempts == 0:
            self._log.log("Jupyter server not found. Giving up ")
            sys.exit(1)
        elif self._config.settings.develop:
            self._logger = threading.Thread(target=self.log_thread)
            self._logger.daemon = True
            self._logger.start()

    def stop_jupyter(self):
        self._log.log("Shutting down jupyter if exists")
        result, _ = self._proc.run_cmd(
            ["jupyter", "notebook", "stop"], err_handling=self._proc.CAPTURE
        )
        self._log.log(f"{result}")

        if self._jupyter_app:
            self._proc.kill(self._jupyter_app)

    def log_thread(self):
        # Redirect jupyter process output to the logging facility
        while self._jupyter_app.poll() is None:  # while process is still alive
            self._log.log(self._jupyter_app.stderr.readline().strip())
