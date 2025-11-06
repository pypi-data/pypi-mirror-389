# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw


class BinomialLaw(ProbabilityLaw):
    """
    Represents a binomial distribution and provides methods for common calculations.

    It will be used only for the failure on demand. Therefore, the distribution has a fixed number of trials set to
    value 1.

    Attributes:
        parameters: The probability of success for the single trial.
    """
    def __init__(self,
                 parameters):
        super().__init__(self.__class__.__name__,
                         parameters,
                         is_failure_on_demand=True)

    def __eq__(self, other):
        if not isinstance(other, BinomialLaw):
            return NotImplemented
        return super().__eq__(other)

    def get_random_value(self) -> float:
        return self.random_number_generator.binomial(1, self.parameters[0])

    def get_quantile_value(self, quantile: float):
        return quantile <= self.parameters[0]

    def get_mean_value(self) -> float:
        return self.parameters[0]

    def get_variance_value(self) -> float:
        return self.parameters[0]*(1-self.parameters[0])
