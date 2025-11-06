# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.reader.xlsx import xlsx_utils
from availsim4core.src.reader.xlsx.monte_carlo_reader import MonteCarloReader
from availsim4core.src.simulation.simulation import Simulation
from availsim4core.src.simulation.splitting_mc import SplittingMonteCarlo
from availsim4core.resources.excel_strings import SimulationSplittingMonteCarloColumn


class SplittingMonteCarloReader(MonteCarloReader):
    """
    Specific reader for the MonteCarlo simulation.
    """

    @classmethod
    def build(cls, simulation_parameters) -> Simulation:
        params = cls.MonteCarloParameters(simulation_parameters)
        return SplittingMonteCarlo(
            params.minimum_number_of_simulations,
            params.maximum_number_of_simulations,
            params.convergence_margin,
            params.maximum_execution_time,
            params.seed,
            params.diagnostics,
            params.simulation_duration,
            xlsx_utils.clean_str_cell(simulation_parameters,
                                                 SimulationSplittingMonteCarloColumn.SYSTEM_ROOT_COMPONENT,
                                                 exception_message_hint='simulation file, system root component'))
