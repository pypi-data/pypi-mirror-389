# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module defining an interface for Weights used in Importance Splitting
"""

import numpy as np
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.component_tree.compound import Compound


class Weights:
    """
    Interface for all classes providing weighting functionality to importance splitting in the framework
    """

    @staticmethod
    def calculate_component_failure_weight(component: Compound) -> float:
        """
        Implementations of this function should return a weight for a failure of an individual component.
        """

    @staticmethod
    def is_cfp_component(component: Component) -> bool:
        """
        Functions implementing this abstract method should accept a component as a parameter and return true
        if that component is to be considered in critical failure paths and false otherwise.
        """

    @staticmethod
    def calculate_distance_to_critical_failure(failure_states_atm: np.ndarray) -> float:
        """
        Those functions should implement a mechanism to calculate distance of failure configurations
        (provided to the function as the only argument) and return that distance.
        """
