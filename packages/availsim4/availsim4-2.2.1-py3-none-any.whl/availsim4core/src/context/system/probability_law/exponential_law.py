# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from typing import List
import numpy

from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw


class ExponentialLaw(ProbabilityLaw):
    """
    Class used to generate values according to the Exponential law
    """

    def __init__(self, parameters: List[float]):
        super().__init__(self.__class__.__name__,
                         parameters,
                         is_failure_on_demand=False)
        self.set_parameters(parameters)

    def set_parameters(self, parameters: List[float]) -> None:
        """Setting the values of Exponential law parameters: scale and location.

        Args:
            parameters (List[float]): list of two values: scale and location.
        """
        self.parameters = parameters
        self._scale = parameters[0]
        self._shift = 0
        if len(parameters) > 1:
            self._shift = parameters[1]

    def __eq__(self, other):
        if not isinstance(other, ExponentialLaw):
            return NotImplemented
        return super().__eq__(other)

    def get_random_value(self) -> float:
        return self.random_number_generator.exponential(self._scale) + self._shift

    def get_quantile_value(self, quantile: float) -> float:
        return - numpy.log(1 - quantile) * self._scale  + self._shift

    def get_mean_value(self) -> float:
        return self._scale + self._shift

    def get_variance_value(self) -> float:
        return self._scale ** 2
