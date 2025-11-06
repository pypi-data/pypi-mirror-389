# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for WeibullLaw class
"""

from typing import List
import numpy as np
import scipy.special
from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw

class WeibullLaw(ProbabilityLaw):
    """
    Class used to generate values according to the Weibull law
    """

    def __init__(self,
                 parameters: List[float]):
        super().__init__(self.__class__.__name__,
                         parameters,
                         is_failure_on_demand = False)
        self.set_parameters(parameters)

    def set_parameters(self, parameters: List[float]) -> None:
        """Setting the values of Weibull law parameters: scale, shape and location.

        Args:
            parameters (List[float]): a list of three values for scale, shape and location (in this order).
        """
        self.parameters = parameters
        self._scale = parameters[0]
        self._shape = parameters[1]
        self._shift = 0
        if len(parameters) > 2:
            self._shift = parameters[2]

    def __eq__(self, other):
        if not isinstance(other, WeibullLaw):
            return NotImplemented
        return super().__eq__(other)

    def get_random_value(self) -> float:
        return self._scale * self.random_number_generator.weibull(self._shape) + self._shift

    def get_quantile_value(self, quantile)-> float:
        return self._scale * (-np.log(1-quantile)**(1/self._shape)) + self._shift

    def get_mean_value(self) -> float:
        return self._scale * scipy.special.gamma(1+1/self._shape) + self._shift

    def get_variance_value(self) -> float:
        return self._scale ** 2 * (
            scipy.special.gamma(1 + 2 / self._shape) - scipy.special.gamma(1 + 1 / self._shape) ** 2
        )
