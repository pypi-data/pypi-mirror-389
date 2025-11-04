import ctypes
from dataclasses import dataclass, field
from typing import Dict, Mapping, Sequence

from .exceptions import (
    ConditionFatal,
    EngineRunDidNotConverge,
    EngineRunFailed,
    InvalidRuleDefintionError,
    RuleEngineException,
)
from .rule import Rule, Ruleset
from .state import State


@dataclass
class EngineRunInfo:
    start_hash: int = 0
    end_hash: int = 0
    failures: int = 0
    warnings: int = 0
    logs: Sequence[str] = field(default_factory=list)


class Engine(object):
    def __init__(
        self,
        state: State = None,
        rules: Dict[str, Ruleset] = None,
        warnings_are_failures: bool = False,
        continue_on_fail: bool = False,
    ) -> None:
        self._state: State = state if state else State()
        self._rulesets: Dict[str, Ruleset] = rules if rules else {}
        self._run_info: Sequence[EngineRunInfo] = []
        self._fail_warn: bool = warnings_are_failures
        self._continue: bool = continue_on_fail

    def add_ruleset(self, name: str, ruleset: Ruleset):
        self._rulesets[name] = ruleset

    @property
    def state(self) -> State:
        return self._state

    @property
    def rules(self) -> Dict[str, Ruleset]:
        return self._rulesets

    @property
    def warnings_are_failures(self) -> bool:
        return self._fail_warn

    @warnings_are_failures.setter
    def warnings_are_failures(self, value: bool) -> None:
        self._fail_warn = value

    @property
    def continue_on_fail(self) -> bool:
        return self._continue

    @continue_on_fail.setter
    def continue_on_fail(self, value: bool) -> None:
        self._continue = value

    def _log(self, msg: str, is_failure: bool) -> None:
        info = self._run_info[-1]
        if is_failure:
            info.failures += 1
        else:
            info.warnings += 1
        # Append a message to the last log set
        info.logs += [msg]

    def _run_rule(self, rule: Rule, **kwargs):
        """
        Execute the provided rule definition
        """
        try:
            # Match requested parameters for the rule from the state context
            arg_list = {
                k: v
                for k, v in dict(**self._state.context, **kwargs).items()
                if k in rule.func.__code__.co_varnames[: rule.func.__code__.co_argcount]
            }
            rule.func(**arg_list)
        except RuleEngineException as e:
            self._log(f"{rule.func.__name__}: {e}", isinstance(e, ConditionFatal))

    def _iterate_rule(self, rule: Rule):
        """
        Executes a rule using the provided iterator data
        """
        variable = eval(rule.iterate.expression, self._state.context.copy())
        if isinstance(variable, (Sequence, ctypes.Array)):
            for i, o in enumerate(variable):
                self._run_rule(rule, **{rule.iterate.name: (i, o)})
        elif isinstance(variable, Mapping):
            for k, v in enumerate(variable):
                self._run_rule(rule, **{rule.iterate.name: (k, v)})
        else:
            raise InvalidRuleDefintionError(
                f"Object {type(variable)} defined by {rule.iterate.expression} is not iterable"
            )

    def _run_ruleset(self, ruleset):
        """
        Execute all rules in a ruleset
        """
        for r in ruleset.rules:
            if r.iterate:
                self._iterate_rule(r)
            else:
                self._run_rule(r)

    def _run_rulesets(self) -> None:
        """
        Execute all rulesets for this instance
        """
        run_info = EngineRunInfo()
        self._run_info.append(run_info)
        run_info.start_hash = hash(self._state)

        self._state.modified = False

        for rs in self._rulesets.values():
            self._run_ruleset(rs)

        run_info.end_hash = hash(self._state)

    def run(self, passes: int = 3) -> int:
        """
        Executes the engine which iterates through the rulesets which are provided the require state variables to evaluate
        or modify
        """
        if passes <= 0 or not isinstance(passes, int):
            raise EngineRunFailed(
                f"The number of passes the engine will run must be a posstive integer. The value {passes} was provided"
            )

        # In order to track the change between passes and to detect metastable conditions the
        # before and after "memory" has to be tracked. This can cause performance issues if the rules are working with
        # are very large or complicated collections

        self._run_info = []
        for iteration in range(1, passes + 1):
            # Executates all of the rules attached to this engine
            self._run_rulesets()

            # Get the saved data from the last run
            run_info = self._run_info[-1]

            if run_info.failures and not self._continue:
                raise EngineRunFailed(
                    f"There were {run_info.failures} failures encountered during run {iteration}"
                )

            if run_info.warnings and self._fail_warn:
                raise EngineRunFailed(
                    f"There were {run_info.warnings} encountered during run {iteration} and warnings are treated as failures"
                )

            # If nothing was modified during this run then we've reached a stable state where successive runs should not
            # alter the state further
            if not self._state.modified:
                return iteration

        raise EngineRunDidNotConverge(f"Did not reach stable state after {passes}")

    def get_unique_states(self) -> Sequence[int]:
        hashes = []
        for i in self._run_info:
            hashes += [i.start_hash, i.end_hash]
        return set(hashes)

    def get_messages(self, iteration: int = -1):
        return self._run_info[iteration].logs

    def get_failures(self, iteration: int = -1):
        return self._run_info[iteration].failures

    def get_warnings(self, iteration: int = -1):
        return self._run_info[iteration].warnings
