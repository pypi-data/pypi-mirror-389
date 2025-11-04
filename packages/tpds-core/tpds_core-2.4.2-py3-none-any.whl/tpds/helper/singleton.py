from __future__ import annotations

from typing import Any


def make_singleton(classdef: Any) -> Any:
    """
    Decorator that creates a singleton from the provided class definition. While you can inherit a
    singleton the state is shared between the base single and any instances so adding or altering
    a class variable will reflect everywhere. It is possible to add methods via inheritance without
    affecting other instances
    """

    class Singleton(classdef):
        __shared_state: dict[str, Any] = {}

        def __new__(cls, *args: Any, **kwargs: Any) -> Any:
            # Only ever allow one global instance of the config validator
            instance = super().__new__(cls)
            instance.__dict__ = cls.__shared_state
            return instance

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            if not self.__shared_state:
                super().__init__(*args, **kwargs)

    return Singleton
