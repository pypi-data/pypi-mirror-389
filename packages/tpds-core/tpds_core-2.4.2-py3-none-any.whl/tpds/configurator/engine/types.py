from typing import Any, Callable, TypeVar

# Unfortunately this isn't a standard part of the typing library yet
DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])
