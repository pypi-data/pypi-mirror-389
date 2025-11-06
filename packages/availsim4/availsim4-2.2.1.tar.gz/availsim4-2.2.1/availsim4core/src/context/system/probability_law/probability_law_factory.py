# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for a factory of ProbabilityLaw objects
"""


from typing import List
import logging

from availsim4core.src.context.system.probability_law.exponentiated_weibull_law import ExponentiatedWeibullLaw
from availsim4core.src.context.system.probability_law.weibull_law import ProbabilityLaw
from availsim4core.src.context.system.probability_law.deterministic_law import DeterministicLaw
from availsim4core.src.context.system.probability_law.exponential_law import ExponentialLaw
from availsim4core.src.context.system.probability_law.normal_law import NormalLaw
from availsim4core.src.context.system.probability_law.binomial_law import BinomialLaw
from availsim4core.src.context.system.probability_law.weibull_law import WeibullLaw


class ProbabilityLawFactoryError(Exception):
    """
    Error thrown when no defined probability distribution matches the user-defined string
    """


def build(distribution: str, parameters: List[float]) -> ProbabilityLaw:
    """
    This function returns an object of a class implementing ProbabilityLaw interface which fulfills the criteria defined
    by the 1st parameter - matching distribution name - and is initialized by parameters passed on in the 2nd arg.
    """

    if distribution in ["EXP", "EXPONENTIAL", "EXPONENTIALLAW", "EXPONENTIAL_LAW"]:
        return ExponentialLaw(parameters)
    elif distribution in ["NORMAL", "NORMALLAW", "NORMAL_LAW"]:
        return NormalLaw(parameters)
    elif distribution in ["FIX", "DETERMINISTIC", "DETERMINISTIC_LAW", "DETERMINISTICLAW"]:
        return DeterministicLaw(parameters)
    elif distribution in ["POFOD", "FOD","BINOMIAL", "BINOMIALLAW", "BINOMIAL_LAW"]:
        return BinomialLaw(parameters)
    elif distribution in ["WEIBULL", "WEIBULLLAW", "WEIBULL_LAW"]:
        return WeibullLaw(parameters)
    elif distribution in ["EW", "EXPWEI", "EXPWEIBULL", "EXPONENTIATEDWEIBULL"]:
        return ExponentiatedWeibullLaw(parameters)
    else:
        message_exception = f"wrong type of distribution function: {distribution}"
        logging.exception(message_exception)
        raise ProbabilityLawFactoryError(message_exception)
