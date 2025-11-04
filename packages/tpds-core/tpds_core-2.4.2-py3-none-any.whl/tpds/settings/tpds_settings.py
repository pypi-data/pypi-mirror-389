# -*- coding: utf-8 -*-
"""All rights reserved. Copyright 2019 - 2020, Microchip Technology inc

This module implements the Trust Platform Settings
"""
from __future__ import annotations

import json
import logging
import os
from functools import singledispatchmethod
from itertools import filterfalse
from typing import (
    KT,
    VT,
    Any,
    Callable,
    Iterable,
    Iterator,
    MutableMapping,
    MutableSequence,
    Sequence,
    T,
    T_co,
    Union,
    VT_co,
)

from tpds.helper import LogFacility, log, merge_dicts
from tpds.settings.validator import SettingsValidator


def _make_path_abs(*args) -> str:
    """
    Turn a list of args into an absolute path
    """
    path = os.path.expanduser(os.path.join(*list(filter(lambda x: x, args))))
    if not os.path.isabs(path):
        os.path.join(os.getcwd(), path)
    return str(os.path.realpath(path))


def _get_homepath(home_path: Union[str, None] = None) -> str:
    """
    Retrieve the default homepath for the trust platform which is where settings
    and logs are stored
    """
    if home_path:
        return _make_path_abs(home_path)
    else:
        return _make_path_abs("~", ".trustplatform")


def _check_home_path(home_path: Union[str, "os.PathLike[str]"]) -> None:
    """
    Verify the home path is valid
    """
    if os.path.exists(home_path):
        if not os.path.isdir(home_path):
            raise FileNotFoundError("{} is not a valid directory".format(home_path))
    else:
        os.makedirs(home_path, exist_ok=True)


def _setting_type_check(value: Any, observer: Callable[[Any], Any]) -> Any:
    if isinstance(value, MutableMapping):
        return TpdsSettingsDict(value, observer=observer)
    elif isinstance(value, MutableSequence):
        return TpdsSettingsList(value, observer)
    return value


class TpdsSettingsList(MutableSequence[T]):
    def __init__(self, __v: Sequence[T], observer: Callable[[Any], Any]) -> None:
        super().__init__()
        self.data = __v
        self.observer = observer

    @singledispatchmethod
    def __setitem__(self, __i: int, __v: T) -> None:
        self.observer(True)
        self.data.__setitem__(__i, _setting_type_check(__v, self.observer))

    @__setitem__.register
    def _(self, __s: slice, __o: Iterable[T]) -> None:
        self.observer(True)
        self.data.__setitem__(__s, [_setting_type_check(x, self.observer) for x in __o])

    def __getitem__(self, __is: Union[int, slice]) -> T:
        return self.data[__is]

    def __delitem__(self, __i) -> None:
        self.observer(True)
        del self.data[__i]

    def __len__(self) -> int:
        return len(self.data)

    def insert(self, __i: int, __v: T) -> None:
        self.observer(True)
        return self.data.insert(__i, __v)

    def __repr__(self) -> str:
        return str(self.data)


class TpdsSettingsDict(MutableMapping[KT, VT]):
    def __init__(self, *args: Any, observer: Callable[[Any], Any], **kwargs: Any) -> None:
        super().__init__()
        self.__observer = observer
        self.__dict__.update(dict(*args, **kwargs))

    def __getitem__(self, __k: KT) -> VT_co:
        return self.__dict__[__k]

    def __delitem__(self, __k: KT) -> None:
        self.__observer(True)
        self.__dict__.__delitem__(__k)

    def __setitem__(self, __k: KT, __v: VT) -> None:
        self.__observer(True)
        self.__dict__[__k] = _setting_type_check(__v, self.__observer)

    def __iter__(self) -> Iterator[T_co]:
        return filterfalse(lambda x: x[0].startswith("_"), iter(self.__dict__))

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name.startswith("_"):
            super().__setattr__(__name, __value)
        else:
            self.__setitem__(__name, __value)

    def __delattr__(self, __name: str) -> None:
        if __name.startswith("_"):
            self.__dict__.__delitem__(__name)
        else:
            self.__delitem__(__name)

    def __len__(self) -> int:
        return len(self.__dict__) - 1

    def __repr__(self) -> str:
        return str(self.__dict__)


class TpdsSettingsEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, MutableMapping):
            return {k: v for k, v in o.items()}
        elif isinstance(o, MutableSequence):
            return [v for v in iter(o)]
        else:
            print(type(o))
        return super().default(o)


class TpdsSettingsValidator(SettingsValidator):
    """
    Process and validate a usecase - acts as a singleton
    """

    __shared_state: dict[str, Any] = {}

    def __new__(cls, **kwargs: str) -> Any:
        # Only ever allow one global instance of the config validator
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self, schema: Union[str, None] = None) -> None:
        if not self.__shared_state:
            if schema is None:
                schema = os.path.join(os.path.dirname(__file__), "tpds_config.yaml")
            super(TpdsSettingsValidator, self).__init__(schema)


class TpdsSettings(TpdsSettingsDict[str, Any]):
    """
    Global TPDS Configuration Resource - acts as a singleton
    """

    __changed: bool = False
    __shared_state: dict[str, Any] = {}
    __default_source = os.path.join(os.path.dirname(__file__), "tpds_default.yaml")
    __validator: SettingsValidator = TpdsSettingsValidator()
    __config_source = os.path.join(_get_homepath(), "TPDS_config.json")

    def __new__(
        cls,
        home_path: Union[str, "os.PathLike[str]", None] = None,
        config: Union[str, "os.PathLike[str]", None] = None,
        validator: Union[SettingsValidator, None] = None,
        **kwargs: str,
    ) -> Any:
        """
        Creates a new instance of the TpdsSettings class - one can replace the validator
        which will impact all existing instances
        """
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        if validator is not None:
            cls.__validator = validator

        if config is not None:
            if not os.path.isabs(config):
                cls.__config_source = _make_path_abs(_get_homepath(home_path), config)
            else:
                cls.__config_source = _make_path_abs(config)

        return instance

    def __init__(
        self,
        home_path: Union[str, "os.PathLike[str]", None] = None,
        config: Union[str, "os.PathLike[str]", None] = None,
        **kwargs: str,
    ) -> None:
        """
        Initialize a new instances of the TpdsSettings class
        """
        super().__init__(observer=lambda x: TpdsSettings.set_changed(x))

        if len(self) == 0:
            self.load_new_config(self.__default_source)
            first_time = True
        else:
            first_time = False

        if (config or first_time) and os.path.exists(self.__config_source):
            # Load settings from the file
            log("Loading configuration data from {}".format(self.__config_source))
            self.load_new_config(self.__config_source)
            self.set_changed(False)

        app_settings = getattr(self, "app_settings", {})
        if "home_path" not in app_settings:
            app_settings["home_path"] = _get_homepath(home_path)

        # Make the home path if it doesn't exist
        _check_home_path(app_settings["home_path"])

        if not os.path.exists(self.__config_source) or (
            home_path and (_make_path_abs(home_path) != app_settings["home_path"])
        ):
            # Save is there is a change to the home path or we're setting up defaults
            self.save_json(self.__config_source)

    def get_homepath(self) -> str:
        """
        Getings the TPDS homepath where TPDS will stores it's logs and by default
        its configuration file
        """
        return str(getattr(self, "app_settings", {}).get("home_path", _get_homepath()))

    @staticmethod
    def _make_config_path(home_path: str, file_name: Union[str, "os.PathLike[str]"]) -> str:
        if not os.path.isabs(file_name):
            return _make_path_abs(_get_homepath(home_path), file_name)
        return _make_path_abs(file_name)

    def defaults(self) -> None:
        """
        Reset to the defaults and clear any custom entries
        """
        config = self.__validator.validated(self.__default_source)
        if config is not None:
            remove_keys = set(self.keys()).difference(set(config.keys()))
            for key in remove_keys:
                self.pop(key)
            merge_dicts(self, config)

    def load_new_config(self, config: Union[str, "os.PathLike[str]"]) -> None:
        """
        Load/Parse a new configuration
        """
        v_config = self.__validator.validated(config, True)
        if v_config is not None:
            merge_dicts(self, v_config)

    @classmethod
    def is_changed(cls) -> bool:
        """
        Indicates if a setting has been modified, added, or deleted
        """
        return cls.__changed

    @classmethod
    def set_changed(cls, is_changed: bool = True) -> None:
        """
        Sets the changed indicator for the settings
        """
        cls.__changed = is_changed

    def save_json(self, file_name: Union[str, "os.PathLike[str]", None] = None) -> None:
        """
        Attempts to save the configuration if it is able.
        """
        config_file = self._make_config_path(None, file_name) if file_name else self.__config_source
        json_data = json.dumps(self, indent=2, cls=TpdsSettingsEncoder)
        if self.__validator.validated(json_data, True):
            log("Saving configuration to {}".format(config_file))
            with open(config_file, "w") as j_file:
                j_file.write(json_data)
                self.set_changed(False)
        else:
            log("Unable to save the configuration because it is invalid - see previous message")


class TrustPlatformSettings:
    """TrustPlatformSettings - all application settings"""

    def __init__(
        self,
        file_name: Union[str, "os.PathLike[str]", None] = None,
        values: Union[dict[str, Any], None] = None,
        log_enable: bool = True,
    ) -> None:
        if not log_enable:
            LogFacility(level=logging.FATAL)

        self._settings = TpdsSettings(config=file_name)

        self.settings = getattr(self._settings, "app_settings")
        if values and "settings" in values:
            self.settings.update(values["settings"])

        self.packages = getattr(self._settings, "packages")
        if values and "packages" in values:
            self.packages.update(values["packages"])

        self.runtime_settings = getattr(self._settings, "runtime_settings")
        if values and "runtime_settings" in values:
            self.packages.update(values["runtime_settings"])

    def save(self, file_name: Union[str, "os.PathLike[str]", None] = None) -> None:
        self._settings.save_json(file_name)

    def load(self, file_name: Union[str, "os.PathLike[str]"]) -> None:
        if os.path.exists(file_name):
            TpdsSettings(config=file_name)
        else:
            log("configuration file not found - using defaults")

    def is_changed(self) -> bool:
        return self._settings.is_changed()

    def get_base_folder(self):
        return self.settings.home_path


def reset_runtime_settings() -> None:
    config = TrustPlatformSettings()
    setattr(config.runtime_settings, "active_board", "")
    config.save()


__all__ = ["TrustPlatformSettings", "reset_runtime_settings"]
