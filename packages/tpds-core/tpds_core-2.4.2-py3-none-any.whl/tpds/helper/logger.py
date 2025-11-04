# -*- coding: utf-8 -*-
# 2019 to present - Copyright Microchip Technology Inc. and its subsidiaries.

# Subject to your compliance with these terms, you may use Microchip software
# and any derivatives exclusively with Microchip products. It is your
# responsibility to comply with third party license terms applicable to your
# use of third party software (including open source software) that may
# accompany Microchip software.

# THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS". NO WARRANTIES, WHETHER
# EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE, INCLUDING ANY IMPLIED
# WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR
# PURPOSE. IN NO EVENT WILL MICROCHIP BE LIABLE FOR ANY INDIRECT, SPECIAL,
# PUNITIVE, INCIDENTAL OR CONSEQUENTIAL LOSS, DAMAGE, COST OR EXPENSE OF ANY
# KIND WHATSOEVER RELATED TO THE SOFTWARE, HOWEVER CAUSED, EVEN IF MICROCHIP
# HAS BEEN ADVISED OF THE POSSIBILITY OR THE DAMAGES ARE FORESEEABLE. TO THE
# FULLEST EXTENT ALLOWED BY LAW, MICROCHIP'S TOTAL LIABILITY ON ALL CLAIMS IN
# ANY WAY RELATED TO THIS SOFTWARE WILL NOT EXCEED THE AMOUNT OF FEES, IF ANY,
# THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR THIS SOFTWARE.

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Union


class LogFacility:
    """
    Logging Facility - acts as a singleton
    """

    __shared_state: dict[str, Any] = {}
    _default_log_format = "[%(levelname)s %(asctime)s %(process)-5d %(thread)-5d] %(message)s"

    def __new__(cls, **kwargs: Union[str, os.PathLike[str], None]) -> Any:
        # Only ever allow one global instance of the logger
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(
        self,
        logfile: Union[str, os.PathLike[str], None] = None,
        level: int = logging.DEBUG,
        logstream: bool = True,
        logformat: str = _default_log_format,
        mode="w",
    ) -> None:
        if not hasattr(self, "_callback"):
            self._callback: Union[Callable[[str], None], None] = None
        if not hasattr(self, "_log"):
            self._log = logging.getLogger("tpds")
            self._log.setLevel(level)

        if not hasattr(self, "_formatter"):
            self._formatter = logging.Formatter(logformat)

        sh = None
        fh = None
        for h in self._log.handlers:
            if isinstance(h, logging.FileHandler):
                fh = h
            elif isinstance(h, logging.StreamHandler):
                sh = h

        if logstream and sh is None:
            sh = logging.StreamHandler()
            sh.setLevel(level)
            sh.setFormatter(self._formatter)
            self._log.addHandler(sh)

        if logfile is not None and fh is None:
            fh = logging.FileHandler(logfile, mode=mode)
            fh.setLevel(level)
            fh.setFormatter(self._formatter)
            self._log.addHandler(fh)

    def log(self, message: str, logtype: int = logging.DEBUG) -> None:
        """
        Default logging mechanism which emits to all connected loggers
        """
        self._log.log(logtype, message)
        try:
            if self._callback is not None:
                self._callback(str(message).strip())
        except Exception as e:
            self._log.error(e)

    def set_logger(self, logger: Callable[[str], None]) -> None:
        """
        Add a custom logging callback that will also be used
        """
        self._callback = logger


def log(*messages: Union[str, bytes]) -> None:
    logger = LogFacility()
    message = ""
    for msg in messages:
        message += str(msg)
    logger.log(str(message).strip())


class UsecaseLogger:
    def __init__(self, usecase_dir: str, fileName: str = "provision.log") -> None:
        os.makedirs(usecase_dir, exist_ok=True)
        self.file = os.path.join(usecase_dir, fileName)
        self.logger = LogFacility(logfile=self.file, mode="a")
        self.log_history = ""

    def log_to_history(self, info, level):
        log_entry = self.logger._formatter.format(
            logging.LogRecord(
                name=self.logger._log.name,
                level=level,
                pathname="",
                lineno=0,
                msg=info,
                args=(),
                exc_info=None,
            )
        )
        self.log_history += log_entry + "\n"

    def get_log(self):
        log, self.log_history = self.log_history, ""
        return log

    def log(self, info: str, logtype: int = logging.DEBUG):
        self.logger.log(info)
        self.log_to_history(info, logtype)

    def close(self):
        handlers = self.logger._log.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger._log.removeHandler(handler)


__all__ = ["LogFacility", "log"]
