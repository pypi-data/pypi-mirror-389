from __future__ import annotations

"""
TPDS Process Management Utiltities
"""

import enum
import subprocess
from typing import Any, List, Literal, Sequence, Tuple, Union

# TPDS Common Resources
from tpds.helper import LogFacility


class ErrorHandling(enum.IntEnum):
    DISCARD = subprocess.DEVNULL
    CAPTURE = subprocess.STDOUT
    LOG = subprocess.PIPE


__allowed_handling = Literal[ErrorHandling.DISCARD, ErrorHandling.CAPTURE, ErrorHandling.LOG]


class ProcessingUtils:
    """
    Process Management Tools
    """

    __shared_state: dict[str, Any] = {}
    DISCARD = ErrorHandling.DISCARD
    CAPTURE = ErrorHandling.CAPTURE
    LOG = ErrorHandling.LOG

    def __new__(cls) -> Any:
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self) -> None:
        self._processes: List[subprocess.Popen[Any]] = []
        self._log = LogFacility()

    def _get_process(self, pid: int) -> Union[subprocess.Popen[Any], None]:
        for proc in self._processes:
            if proc.pid == pid:
                return proc
        return None

    def start(
        self,
        cmd: Sequence[str],
        err_handling: __allowed_handling = ErrorHandling.DISCARD,
        log_args: bool = True,
        **kwargs: Any,
    ) -> subprocess.Popen[Any]:
        """
        Start an external process
        """
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=err_handling, universal_newlines=True, **kwargs
        )
        if log_args:
            self._log.log('Started "{}" with pid {}'.format(" ".join(cmd), process.pid))
        else:
            self._log.log('Started "{}" with pid {}'.format(cmd[0], process.pid))
        self._processes += [process]
        return process

    def wait(
        self, process: subprocess.Popen[Any], timeout: Union[int, None] = None
    ) -> Tuple[str, int]:
        """
        Wait for the process to complete - will timeout if the timeout value is not None
        """
        try:
            out_data, error_data = process.communicate(timeout=timeout)
            self._log.log(
                "Process ({}) ended with code ({})".format(process.pid, process.returncode)
            )
        except subprocess.TimeoutExpired:
            process.kill()
            out_data, error_data = process.communicate()
            self._log.log(
                "Process ({}) Timed out after running for {}".format(process.pid, timeout)
            )
        finally:
            returncode = process.returncode
            if error_data:
                self._log.log(error_data)
            if process in self._processes:
                self._processes.remove(process)
            return out_data, returncode

    def run_cmd(
        self,
        cmd: Sequence[str],
        timeout: Union[int, None] = None,
        err_handling: __allowed_handling = ErrorHandling.DISCARD,
        **kwargs: Any,
    ) -> Tuple[str, int]:
        """
        Generic function to run a command and return the
        """
        process = self.start(cmd, err_handling=err_handling, **kwargs)
        return self.wait(process, timeout)

    def kill(self, process: Union[subprocess.Popen[Any], int, None]) -> None:
        """
        Kill a process that was started
        """
        self._log.log(f"Stopping {process}")
        if isinstance(process, int):
            process = self._get_process(process)

        if isinstance(process, subprocess.Popen):
            process.kill()

    def terminate_all(self) -> None:
        """
        Terminate all running process
        """
        self._log.log("Terminating {} processes".format(len(self._processes)))
        # Loop through and kill all processes
        for process in self._processes:
            try:
                self.kill(process)
            except Exception as e:
                self._log.log(e)
                # Process is probably already dead
                pass
            finally:
                self._processes.remove(process)


__all__ = ["ProcessingUtils", "ErrorHandling"]
