from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from tpds.helper import make_singleton, merge_dicts

from .engine import Ruleset


@dataclass
class TpdsConfiguratorData:
    #
    # Rules that apply for this device
    rules: list[Ruleset] = field(default_factory=list)
    # Model of the device
    model: dict[str, Any] = field(default_factory=dict)


@make_singleton
class TpdsConfiguratorCache:
    def __init__(self) -> None:
        self.__data: dict[str, list[TpdsConfiguratorData]] = {}

    def get_rules(self, name: str) -> list[Ruleset]:
        rules = []
        for item in self.__data.get(name, []):
            rules += item.rules
        return rules

    def get_model(self, name: str) -> dict[str, Any]:
        model = {}
        for item in self.__data.get(name, []):
            merge_dicts(model, item.model)
        return model


class TpdsConfigurator:
    def __init__(self) -> None:
        self.__data = {}

    def register_device(
        self, name: str, rules: list[Ruleset], model: Optional[dict[str, Any]] = None
    ) -> None:
        self.__data[name] = TpdsConfiguratorData(name=name, rules=rules, model=model)


__all__ = ["TpdsConfigurator"]
