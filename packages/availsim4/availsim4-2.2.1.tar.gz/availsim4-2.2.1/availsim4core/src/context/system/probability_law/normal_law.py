# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import numpy
from scipy.special import erfinv

from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw


class NormalLaw(ProbabilityLaw):
    """
    Class used to generate values according to the Normal law
    """

    def __init__(self,
                 parameters):
        super().__init__(self.__class__.__name__,
                         parameters,
                         is_failure_on_demand=False)

    def __eq__(self, other):
        if not isinstance(other, NormalLaw):
            return NotImplemented
        return super().__eq__(other)

    def get_random_value(self):
        return self.random_number_generator.normal(self.parameters[0], self.parameters[1])

    def get_quantile_value(self, quantile: float) -> float:
        # https://en.wikipedia.org/wiki/Normal_distribution
        return self.parameters[0] + self.parameters[1] * numpy.sqrt(2) * erfinv(2 * quantile - 1)

    def get_mean_value(self) -> float:
        return self.parameters[0]

    def get_variance_value(self) -> float:
        return self.parameters[0] ** 2
