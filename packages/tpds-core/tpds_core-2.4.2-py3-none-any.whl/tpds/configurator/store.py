from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Union

from .models import CompleteConfiguration


@dataclass
class TpdsConfiguratorFileInfo:
    name: str
    path: os.PathLike
    config: Optional[CompleteConfiguration]
    mappings: Optional[Dict[uuid.UUID, Any]]


class TpdsConfiguratorStore:
    __shared_state: dict[str, Any] = {}

    def __new__(cls, **kwargs: str) -> Any:
        # Only ever allow one global instance of the store
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self) -> None:
        if not self.__shared_state:
            self._configs: Dict[str, TpdsConfiguratorFileInfo] = {}

    def _create_uuid_map(self, mapping: Dict[uuid.UUID, Any], obj: Any):
        if id := getattr(obj, "id", None):
            mapping[id] = obj
            if fields := list(obj.__fields__.keys()):
                fields.remove("id")
            for field in fields:
                if item := getattr(obj, field, None):
                    self._create_uuid_map(mapping, item)

    def get_names(self) -> Sequence[str]:
        return list(self._configs.keys())

    def load_config(self, config_name: str) -> Union[CompleteConfiguration, None]:
        config_info = self._configs[config_name]
        if config_info.config is None:
            config_info.config = CompleteConfiguration.parse_file(config_info.path)
            config_info.mappings = {}
            self._create_uuid_map(config_info.mappings, config_info.config)
        return config_info.config

    def new_config(self, config_name: str) -> CompleteConfiguration:
        if config_name in self._configs:
            raise Exception(f"{config_name} already exists")

        config_info = TpdsConfiguratorFileInfo(
            config_name, "", CompleteConfiguration(name=config_name), {}
        )
        self._create_uuid_map(config_info.mappings, config_info.config)
        self._configs[config_name] = config_info
        return config_info.config

    def update_config(self, config_name: str, id: uuid.UUID, data: Any) -> None:
        config = self._configs[config_name]
        obj = config.mappings[id]
        for field in obj.__fields__.keys():
            setattr(obj, field, getattr(data, field, None))
