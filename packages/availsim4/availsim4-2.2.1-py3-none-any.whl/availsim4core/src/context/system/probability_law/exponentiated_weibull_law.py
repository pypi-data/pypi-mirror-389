# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from typing import List
import scipy.stats as st

from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw


class ExponentiatedWeibullLaw(ProbabilityLaw):
    """
    Class used to generate values according to the Exponentiated Weibull law
    """

    def __init__(self, parameters: List[float]):
        super().__init__(self.__class__.__name__,
                         parameters,
                         is_failure_on_demand=False)
        self.set_parameters(parameters)

    def set_parameters(self, parameters: List[float]) -> None:
        """Setting the values of Exponentiated Weibull law parameters: scale, first shape, second shape and location.

        Args:
            parameters (List[float]): list of four parameters: scale, first shape, second shape and location.
        """
        self.parameters = parameters
        self._scale = parameters[0]
        self._first_shape = parameters[1]
        self._second_shape = parameters[2]
        self._shift = parameters[3] # aka location
        self.dist = st.exponweib(self._first_shape, self._second_shape, loc=self._shift, scale=self._scale)

    def __eq__(self, other):
        if not isinstance(other, ExponentiatedWeibullLaw):
            return NotImplemented
        return super().__eq__(other)

    def get_random_value(self) -> float:
        """Alternatively
        ```
        uniform_random_sample = numpy.random.random()
        return self.get_quantile_value(uniform_random_sample)
        ```
        """
        return float(self.dist.rvs(size=1)[0])

    def get_quantile_value(self, quantile: float) -> float:
        """Alternatively
        ```self._scale * ( -numpy.log(1 - (quantile) ** (1/self._second_shape)) ) ** (1/self._first_shape) + self._shift```
        """
        return float(self.dist.ppf(quantile))

    def get_mean_value(self) -> float:
        return float(self.dist.mean())

    def get_variance_value(self) -> float:
        return float(self.dist.var())
