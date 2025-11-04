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
from __future__ import annotations

import os
from abc import ABCMeta, abstractmethod
from functools import singledispatchmethod
from typing import Any, Iterable, Mapping, MutableSequence, Optional, Sequence, Union
from urllib.parse import quote as urlquote

from tpds.settings.validator import SettingsValidator


class UsecaseValidator(SettingsValidator):
    """
    Process and validate a usecase - acts as a singleton
    """

    __shared_state: dict[str, Any] = {}

    def __new__(cls) -> Any:
        # Only ever allow one global instance of the validator so it stays consistant
        # during runtime
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self, schema: Union[str, None] = None) -> None:
        if not self.__shared_state:
            if schema is None:
                schema = str(os.path.join(os.path.dirname(__file__), "usecase.yaml"))
            super(UsecaseValidator, self).__init__(schema)


class UsecaseBase:
    """
    Usecase base class
    """

    __metaclass__ = ABCMeta

    def __init__(self, **kwargs) -> None:
        self.name: str = ""
        self.title: str = ""
        self.description: str = ""
        self.icon: str = ""
        self.applications: Sequence[str] = []
        self.boards: Sequence[str] = []
        self.devices: Sequence[str] = []
        self._root = kwargs.pop("root", None)
        self._path = kwargs.pop("path", None)
        self.__dict__.update(kwargs)

    @property
    def root(self) -> Optional["os.PathLike[str]"]:
        return self._root

    @root.setter
    def root(self, value: Optional["os.PathLike[str]"]):
        self._root = value.replace("\\", "/") if value else None

    @property
    def _path(self) -> Optional["os.PathLike[str]"]:
        return self.__path

    @_path.setter
    def _path(self, value: Optional["os.PathLike[str]"]):
        self.__path = value.replace("\\", "/") if value else None
        self._refresh()

    @abstractmethod
    def _refresh(self) -> None:
        pass


class UsecaseEntrypoint(UsecaseBase):
    def __init__(
        self, parent: Optional[str] = None, entry: os.PathLike[str] = "", **kwargs
    ) -> None:
        self._parent = parent
        self._url = None
        self._entry = None
        self.is_notebook = False
        self.groupTitle = ""
        super().__init__(**kwargs)
        self.entry = entry

    @property
    def source(self) -> Optional["os.PathLike[str]"]:
        return self._source

    @property
    def entry(self) -> Optional["os.PathLike[str]"]:
        return self._entry

    @entry.setter
    def entry(self, value: Optional["os.PathLike[str]"]) -> None:
        self._entry = value.replace("\\", "/") if value else None
        self._refresh()

    @property
    def url(self) -> Optional[str]:
        return self._url

    def _refresh(self):
        self._source = os.path.join(*[x for x in [self._root, self._path, self._entry] if x])

        urlparts = []
        if self._entry:
            urlparts = [urlquote(x) for x in self._entry.split("/")]
            _, ext = os.path.splitext(self._entry)
            if ext.lower() in [".ipynb"]:
                self.is_notebook = True
        if self.is_notebook:
            if self._root:
                urlparts.insert(0, os.path.basename(self._root))
            if self._path:
                urlparts.insert(1, self._path)
        elif self._parent:
            urlparts.insert(0, self._parent)
        self._url = "/".join(urlparts)


class UsecaseEntrypoints(MutableSequence[UsecaseEntrypoint]):
    def __init__(self, __v: Sequence[Any], **kwargs: Any) -> None:
        super().__init__()
        self._extras = kwargs
        self.data = [UsecaseEntrypoint(**self._extras, **v) for v in __v]

    def _check(self, __v):
        return (
            __v if isinstance(__v, UsecaseEntrypoint) else UsecaseEntrypoint(**self._extras, **__v)
        )

    @singledispatchmethod
    def __setitem__(self, __i: int, __v: Any) -> None:
        self.data.__setitem__(__i, self._check(__v))

    @__setitem__.register
    def _(self, __s: slice, __o: Iterable[Any]) -> None:
        self.data.__setitem__(__s, [self._check(x) for x in __o])

    def __getitem__(self, __is: Union[int, slice]) -> Union[UsecaseEntrypoint, UsecaseEntrypoints]:
        return (
            UsecaseEntrypoints(self.data[__is], **self._extras)
            if isinstance(__is, slice)
            else self.data[__is]
        )

    def __delitem__(self, __i) -> None:
        del self.data[__i]

    def __len__(self) -> int:
        return len(self.data)

    def insert(self, __i: int, __v: Any) -> None:
        return self.data.insert(__i, self._check(__v))

    def __repr__(self) -> str:
        return str(self.data)


class UsecaseBackend:
    def __init__(
        self,
        path: Optional["os.PathLike[str]"] = None,
        routers: Sequence[str] = [],
        requires: Sequence[str] = [],
        **kwargs: Any,
    ) -> None:
        self.path = path
        self.routers = routers
        self.requires = requires
        self.__dict__.update(kwargs)

    def __set__(self, instance, value):
        if isinstance(value, Mapping):
            self.__dict__.update(value)
        super().__set__(instance, value)


class UsecaseFrontend:
    def __init__(
        self,
        path: Optional["os.PathLike[str]"] = None,
        entrypoints: Union[UsecaseEntrypoints, Sequence, None] = None,
        **kwargs: Any,
    ) -> None:
        self.path = path
        self._extras = kwargs
        self.entrypoints = entrypoints

    @property
    def entrypoints(self) -> Union[UsecaseEntrypoints, None]:
        return self._entrypoints

    @entrypoints.setter
    def entrypoints(self, value: Union[Sequence, None]):
        self._entrypoints = (
            UsecaseEntrypoints(value, path=self.path, **self._extras)
            if isinstance(value, Sequence)
            else None
        )


class Usecase(UsecaseBase):
    """
    Metadata about a specific usecase
    """

    def __init__(
        self,
        config: Union[str, dict[str, Any], "os.PathLike[str]", None] = None,
        validator: Union[SettingsValidator, None] = None,
    ) -> None:
        super().__init__()
        if validator is None:
            validator = UsecaseValidator()

        self._backend: Optional[UsecaseBackend] = None
        self._frontend: Optional[UsecaseFrontend] = None

        if config is not None:
            if v_config := validator.validated(config, True):
                self.name = v_config.pop("name", None)
                self.root = v_config.pop("root", os.path.dirname(config))
                self.backend = v_config.pop("backend", None)
                self.frontend = v_config.pop("frontend", None)
                self.__dict__.update(v_config)

    def _refresh(self) -> None:
        pass

    @property
    def source(self) -> str:
        return self.root

    @property
    def backend(self) -> Optional[UsecaseBackend]:
        return self._backend

    @backend.setter
    def backend(self, value: Optional[Mapping]):
        self._backend = (
            UsecaseBackend(parent=self.name, root=self.root, **value)
            if isinstance(value, Mapping)
            else None
        )

    @property
    def frontend(self) -> Optional[UsecaseFrontend]:
        return self._frontend

    @frontend.setter
    def frontend(self, value: Optional[Mapping]):
        self._frontend = (
            UsecaseFrontend(parent=self.name, root=self.root, **value)
            if isinstance(value, Mapping)
            else None
        )

    @property
    def url(self) -> Optional[str]:
        if self.frontend and self.frontend.path and not self.frontend.entrypoints:
            return urlquote(self.name) + "/"


__all__ = ["Usecase", "UsecaseEntrypoint"]
