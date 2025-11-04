class RuleEngineException(Exception):
    """Rules Engine Base Exception"""


class ConditionFatal(RuleEngineException):
    """Rule is a fatal error"""


class ConditionSevere(RuleEngineException):
    """Rule is a severe warning"""


class ConditionWarning(RuleEngineException):
    """Rule is a regular warning"""


class InvalidRuleDefintionError(RuleEngineException):
    """The decorated object is an invalid rule defintion"""


class EngineRunDidNotConverge(RuleEngineException):
    """Processing of rules with the provided state did not reach convergence in the alloted cycles"""


class EngineRunFailed(RuleEngineException):
    """Rule failures were encountered during execution of the ruleset"""
