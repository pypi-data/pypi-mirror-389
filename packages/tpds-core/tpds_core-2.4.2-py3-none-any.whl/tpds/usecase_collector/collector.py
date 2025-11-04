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

"""
Code to collect, import, verify, validate and parse usecases
"""
from __future__ import annotations

import importlib.util
import os
from urllib.parse import urlparse
from typing import Any, Mapping, Sequence, Union

from tpds.helper import log
from tpds.settings.tpds_settings import TpdsSettings

from .usecase import Usecase, UsecaseEntrypoint


class Collector:
    """
    Collector class
    """

    __shared_state: dict[str, Any] = {}

    def __new__(cls, **kwargs: str) -> Any:
        # Only ever allow one global instance of the usecase collector
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self, search_paths: Union[Sequence[str], None] = None) -> None:
        """
        Initialize the collector with an optional search path
        """
        if not self.__shared_state:
            log("Initializing usecase collector")
            cfg = getattr(TpdsSettings(), "usecases", {})
            self.__usecases: dict[str, Any] = {}
            self.search_modules = cfg.get("search_modules", True)

            if search_paths is None or len(search_paths) == 0:
                search_paths = cfg.get("paths", [])

            self.__search_paths = []
            for x in search_paths:
                try:
                    self.__search_paths += [{"path": Collector._get_workspace_path(x)}]
                except FileNotFoundError:
                    continue

            self.update(False)

    def __iter__(self):
        return iter(self.__usecases.values())

    def get_search_paths(self):
        return self.__search_paths

    @staticmethod
    def _get_workspace_path(inpath: str = "") -> str:
        ws = os.getcwd()
        if os.path.isabs(inpath):
            abspath = inpath
        else:
            abspath = os.path.abspath(os.path.join(ws, inpath))

        if not (os.path.exists(abspath) and os.path.isdir(abspath)):
            raise FileNotFoundError("Invalid search path")
        else:
            return str(abspath)

    @staticmethod
    def _handle_icon_config(
        source: Union[str, "os.PathLike[str]"], ico: Union[dict[str, str], str]
    ) -> Union[dict[str, str], str]:
        if isinstance(ico, Mapping):
            if ico_source := ico.get("path", None):
                ico["path"] = str(os.path.join(source, ico_source))
                return ico
        elif ico_source := os.path.exists(os.path.join(source, ico)):
            return str(ico_source)
        return ico

    def _process_entrypoint(
        self, uc: UsecaseEntrypoint, parent: Usecase, rescan: bool = False
    ) -> bool:
        """
        Adds a usecase based on a configuration dictionary
        """
        uc.path = parent.frontend.path

        # Process File Path with query param
        parsed_url = urlparse(uc.source)
        file_path = parsed_url.path

        if not os.path.exists(file_path):
            raise ValueError(f"Trying to add usecase entry but {uc.source} does not exist")

        if ico := uc.icon:
            uc.icon = self._handle_icon_config(parent.source, ico)

        if uc.name not in self.__usecases:
            self.__usecases[uc.name] = uc
        elif not rescan:
            log(
                "Duplicate usecase ({}) found in ({}) which conflicts with one found in ({})".format(
                    uc.name, parent.source, self.__usecases[uc.name].source
                )
            )

        return uc.is_notebook

    def _add_usecase(self, source: Union[str, "os.PathLike[str]"], rescan: bool = False) -> bool:
        """
        Checks if a folder is a valid usecase and adds it to the collection
        """
        notebook_found = False

        # Try the new nomenclature first
        cfg = os.path.join(source, "extension.yaml")

        if not os.path.exists(cfg):
            # Fallback and check if the old nomenclature is being used
            cfg = os.path.join(source, "usecase.yaml")

        if not os.path.exists(cfg):
            # No metadata was located to bail on this path
            return False

        try:
            uc = Usecase(cfg)

            if ico := uc.icon:
                uc.icon = self._handle_icon_config(source, ico)

            if uc.frontend and uc.frontend.entrypoints:
                for ep in uc.frontend.entrypoints:
                    if self._process_entrypoint(ep, uc, rescan):
                        notebook_found = True

            if uc.name not in self.__usecases:
                self.__usecases[uc.name] = uc
            elif not rescan:
                log(
                    "Duplicate usecase ({}) found in ({}) which conflicts with one found in ({})".format(
                        uc.name, source, self.__usecases[uc.name].root
                    )
                )
            return notebook_found
        except Exception as e:
            log(f"Problem processing usecase from {source}: {e}")
            return notebook_found

    def add_usecase(self, usecase: Union[Usecase, UsecaseEntrypoint]) -> None:
        self.__usecases[usecase.name] = usecase

    def get(self, name, default: Any = None) -> Union[Usecase, None]:
        return self.__usecases.get(name, default)

    def update(self, rescan: bool = True) -> None:
        """
        Scan the search patchs and installed modules for valid usecases
        """

        def add_module(name):
            if spec := importlib.util.find_spec(name):
                if spec.submodule_search_locations:
                    return [{"path": str(p)} for p in spec.submodule_search_locations]
            return []

        if self.search_modules:
            self.__search_paths += add_module("tpds_usecase")
            self.__search_paths += add_module("tpds_extension")

        for p in self.__search_paths:
            # Give priority to local directories
            for d in os.listdir(p["path"]):
                if os.path.isdir(d := os.path.join(p["path"], d)):
                    if self._add_usecase(d, rescan):
                        p["notebook"] = True


__all__ = ["Collector"]
