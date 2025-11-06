# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw


class DeterministicLaw(ProbabilityLaw):
    """
    Class used to generate values according to the Deterministic law (= always returning the same value)
    """

    def __init__(self,
                 parameters):
        super().__init__(self.__class__.__name__,
                         parameters,
                         is_failure_on_demand=False)

    def __eq__(self, other):
        if not isinstance(other, DeterministicLaw):
            return NotImplemented
        return super().__eq__(other)

    def get_random_value(self) -> float:
        return self.parameters[0]

    def get_quantile_value(self, quantile: float) -> float:
        return self.parameters[0]

    def get_mean_value(self) -> float:
        return self.parameters[0]

    def get_variance_value(self) -> float:
        return 0.0
