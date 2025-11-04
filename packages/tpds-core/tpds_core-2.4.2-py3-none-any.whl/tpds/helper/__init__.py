"""
    Trust Platform Design Suite Helper module
"""

from .logger import LogFacility, log, UsecaseLogger
from .processing import ErrorHandling, ProcessingUtils
from .singleton import make_singleton
from .utils import (
    TableIterator,
    checkIfProcessRunning,
    make_dir,
    merge_dicts,
    check_internet_connection,
    open_folder,
)

__all__ = [
    "LogFacility",
    "UsecaseLogger",
    "log",
    "ProcessingUtils",
    "ErrorHandling",
    "make_singleton",
    "checkIfProcessRunning",
    "make_dir",
    "merge_dicts",
    "TableIterator",
    "check_internet_connection",
    "open_folder",
]
