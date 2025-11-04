from __future__ import annotations

import os
from typing import Any, Mapping, Optional, Union

from tpds.settings.validator import SettingsValidator

from .tpds_models import BoardDetails

try:
    from tpds.proto_boards import get_proto_board_data
except ImportError:
    get_proto_board_data = None


class TpdsBoardValidator(SettingsValidator):
    """
    Process and validate device information - acts as a singleton
    """

    __shared_state: dict[str, Any] = {}

    def __new__(cls) -> Any:
        # Only ever allow one global instance of the validator so
        #  it stays consistant during runtime
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self, schema: Optional[str] = None) -> None:
        if not self.__shared_state:
            if schema is None:
                schema = str(os.path.join(os.path.dirname(__file__), "boards_schema.yaml"))
            super().__init__(schema)


class TpdsBoards:
    """
    Global TPDS Device Information Store - acts as a singleton
    """

    __shared_state: dict[str, Any] = {}
    __validator: SettingsValidator = TpdsBoardValidator()

    def __new__(cls) -> Any:
        """
        Creates a new instance of the TpdsBoards class
        one can replace the validator
        which will impact all existing instances
        """
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self) -> None:
        """
        Initialize a new instances of the TpdsBoards class
        """
        super().__init__()
        if not getattr(self, "_boards", None):
            self._boards = {}
            if get_proto_board_data:
                self.add_board_info(get_proto_board_data())

    @property
    def boards(self) -> Mapping[BoardDetails]:
        return self._boards

    @boards.setter
    def boards(self, values) -> None:
        _v, path = values
        for k, v in _v.items():
            v.update({"board_path": path})
            self._boards.update({k: BoardDetails(**v)})

    def __add_board_info(self, data: Union[Mapping, str, "os.PathLike[str]"]) -> None:
        if v_config := self.__validator.validated(data, True):
            if boards := v_config.get("boards", None):
                self.boards = (boards, os.path.dirname(data))

    def __add_board_info_from_dir(self, dir: "os.PathLike[str]") -> None:
        for name in os.listdir(dir):
            _, ext = os.path.splitext(name)
            if ext.lower() in [".yaml", ".yml"] and os.path.isfile(path := os.path.join(dir, name)):
                self.__add_board_info(path)

    def add_board_info(self, data: Union[Mapping, str, "os.PathLike[str]"]) -> None:
        if isinstance(data, Mapping):
            self.__add_board_info(data)
        elif os.path.exists(data):
            if os.path.isfile(data):
                self.__add_board_info(data)
            else:
                self.__add_board_info_from_dir(data)

    def get_board_info(self, board_name: str) -> Optional[BoardDetails]:
        for board, details in self.boards.items():
            if board == board_name:
                return details
        return None


__all__ = ["TpdsBoards", "TpdsBoardValidator"]
