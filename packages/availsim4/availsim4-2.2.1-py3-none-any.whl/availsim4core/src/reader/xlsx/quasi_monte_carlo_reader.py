# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from typing import Dict

from availsim4core.src.reader.xlsx.monte_carlo_reader import MonteCarloReader
from availsim4core.src.simulation.quasi_monte_carlo import QuasiMonteCarlo
from availsim4core.src.simulation.simulation import Simulation


class QuasiMonteCarloReader(MonteCarloReader):
    """
    Specific reader for the Quasi-Monte Carlo simulation.
    """

    @classmethod
    def build(cls, simulation_parameters: Dict, stages_number: int = 1) -> Simulation:
        params = cls.MonteCarloParameters(simulation_parameters)
        return QuasiMonteCarlo(
            params.minimum_number_of_simulations,
            params.maximum_number_of_simulations,
            params.convergence_margin,
            params.maximum_execution_time,
            params.seed,
            params.diagnostics,
            params.simulation_duration,
            stages_number
        )
