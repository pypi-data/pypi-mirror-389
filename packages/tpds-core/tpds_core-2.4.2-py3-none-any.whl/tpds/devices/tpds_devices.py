from __future__ import annotations

import os
from typing import Any, Mapping, Optional, Sequence, Union

from tpds.settings.validator import SettingsValidator

from .tpds_models import DeviceDetails, DevicePartDetails


class TpdsDeviceValidator(SettingsValidator):
    """
    Process and validate device information - acts as a singleton
    """

    __shared_state: dict[str, Any] = {}

    def __new__(cls) -> Any:
        # Only ever allow one global instance of the validator so it stays consistant
        # during runtime
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self, schema: Optional[str] = None) -> None:
        if not self.__shared_state:
            if schema is None:
                schema = str(os.path.join(os.path.dirname(__file__), "devices_schema.yaml"))
            super().__init__(schema)


class TpdsDevices:
    """
    Global TPDS Device Information Store - acts as a singleton
    """

    __shared_state: dict[str, Any] = {}
    __validator: SettingsValidator = TpdsDeviceValidator()

    def __new__(cls) -> Any:
        """
        Creates a new instance of the TpdsSettings class - one can replace the validator
        which will impact all existing instances
        """
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self) -> None:
        """
        Initialize a new instances of the TpdsSettings class
        """
        super().__init__()

        if not getattr(self, "_parts", None):
            self._parts = []
            self._devices = {}
            self.add_device_info(os.path.join(os.path.dirname(__file__), "data"))

    def __add_part(self, v: DevicePartDetails) -> None:
        for x in self._parts:
            if x.partNumber == v.partNumber:
                self._parts.remove(x)
        self._parts += [v]

    @property
    def parts(self) -> Sequence[DevicePartDetails]:
        return self._parts

    @parts.setter
    def parts(self, v: Union[Sequence, Mapping]) -> None:
        if isinstance(v, Mapping):
            self.__add_part(DevicePartDetails(**v))
        elif isinstance(v, Sequence):
            for item in v:
                self.__add_part(DevicePartDetails(**item))

    @property
    def devices(self) -> Mapping[DeviceDetails]:
        return self._devices

    @devices.setter
    def devices(self, _v: Mapping) -> None:
        self._devices.update({k: DeviceDetails(**v) for k, v in _v.items()})

    def __check_parts(self) -> None:
        for part in self.parts:
            if part.partInterface is None:
                if base := self.devices.get(part.deviceName, None):
                    part.partInterface = base.partInterface

    def __add_device_info(self, data: Union[Mapping, str, "os.PathLike[str]"]) -> None:
        if v_config := self.__validator.validated(data, True):
            if devices := v_config.get("devices", None):
                self.devices = devices
            if parts := v_config.get("parts", None):
                self.parts = parts
            self.__check_parts()

    def __add_device_info_from_dir(self, dir: "os.PathLike[str]") -> None:
        for name in os.listdir(dir):
            _, ext = os.path.splitext(name)
            if ext.lower() in [".yaml", ".yml"] and os.path.isfile(path := os.path.join(dir, name)):
                self.__add_device_info(path)

    def add_device_info(self, data: Union[Mapping, str, "os.PathLike[str]"]) -> None:
        if isinstance(data, Mapping):
            self.__add_device_info(data)
        elif os.path.exists(data):
            if os.path.isfile(data):
                self.__add_device_info(data)
            else:
                self.__add_device_info_from_dir(data)


__all__ = ["TpdsDevices"]
