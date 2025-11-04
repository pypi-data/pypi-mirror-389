"""
Defines the base rule class
"""

from dataclasses import dataclass
from typing import Callable, Dict, MutableMapping, Optional, Sequence, Union

from .types import DecoratedCallable


@dataclass
class RuleIterator:
    # The argument name where the tuple (index, object) or (key, object) will be provide
    name: str
    # The expression that returns an iterable object
    expression: str


@dataclass
class Rule:
    func: DecoratedCallable
    iterate: Optional[RuleIterator]


class Ruleset:
    def __init__(self) -> None:
        self._rules: Sequence[Rule] = []

    @property
    def rules(self) -> Sequence[Rule]:
        return self._rules

    def _add_rule(self, rule_def: DecoratedCallable, iterator: Optional[RuleIterator]) -> None:
        self._rules += [Rule(func=rule_def, iterate=iterator)]

    def rule(
        self, *, iterate: Union[RuleIterator, Dict[str, str], None] = None
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        if isinstance(iterate, MutableMapping):
            iterate = RuleIterator(**iterate)

        # Grab all the keyword args that are directives for the engine
        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self._add_rule(func, iterator=iterate)
            return func

        return decorator


__all__ = ["Rule", "Ruleset"]
