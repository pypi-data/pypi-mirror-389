# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for a class SimpleWeights implementing Weights interface
"""

import numpy as np

from availsim4core.src.simulation.importance_splitting.weights import Weights
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.component_tree.status import Status


class SimpleWeights(Weights):
    """
    This class implements straightforward way to weight failures of different components for use in importance
    splitting mode of the simulations. It uses the inverse of the mean time to failure (for exponential distribution)
    or other mean value provided with other failure laws multiplied by a constant.
    """
    MULTIPLICATION_CONSTANT = 1000000000

    @staticmethod
    def calculate_component_failure_weight(component: Basic) -> float:
        """
        Simple weights implementation is limited to returning an inverse of the smallest mean of any distribution
        describing any failure mode. Multiplication by one billion is for user-friendliness of the results.
        """
        return SimpleWeights.MULTIPLICATION_CONSTANT/component.failure_mode.failure_law.get_mean_value()

    @staticmethod
    def is_cfp_component(component: Component) -> bool:
        """
        In simple weights, only basic components which failed blindly are considered to fit the requirements to be
        failed in a way relevant to CFP.
        """
        return isinstance(component, Basic) and (component.status == Status.BLIND_FAILED)

    @staticmethod
    def calculate_distance_to_critical_failure(failure_states_atm: np.ndarray) -> float:
        """
        This implementation has a very straightforward distance calculation. All failures are summed and the number of
        failures relevant to CFP (meaning - registered in failure_states_atm vector) is returned as the distance.
        """
        return np.sum(failure_states_atm)
