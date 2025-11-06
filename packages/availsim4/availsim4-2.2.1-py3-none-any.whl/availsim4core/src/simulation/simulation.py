# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from typing import List

from availsim4core.src.context.context import Context
from availsim4core.src.results.simulation_results import SimulationResults


class Simulation:
    """
    Defines a simulation that will be triggered by the Sensitivity Analysis.
    When a simulation is ran, it returns a ResultSimulation.
    """

    def __init__(self, maximum_execution_time: float) -> None:
        self.maximum_execution_time = maximum_execution_time

    def run(self, context: Context) -> SimulationResults:
        """
        Run a simulation against a given Component tree by calling multiple Discrete event Simulations.
        """
        pass

    def get_list_of_diagnosis(self) -> List[str]:
        """
        Get a simulation's list of diagnosis for the exporter
        """
        pass
