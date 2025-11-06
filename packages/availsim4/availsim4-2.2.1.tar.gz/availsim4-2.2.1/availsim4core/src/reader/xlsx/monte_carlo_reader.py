# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from dataclasses import dataclass
from typing import Dict
from availsim4core.src.reader.reader import Reader

from availsim4core.src.simulation.monte_carlo import MonteCarlo
from availsim4core.src.reader.xlsx import xlsx_utils
from availsim4core.resources import excel_strings
from availsim4core.src.simulation.simulation import Simulation


class MonteCarloReader(Reader):
    """
    Specific reader for the MonteCarlo simulation.
    """

    @dataclass
    class MonteCarloParameters:
        """Class used to parse parameters
        """
        EXCEPTION_HINT_MESSAGE =  "simulation file"

        def __init__(self, simulation_parameters: Dict[str, str]) -> None:
            self.simulation_duration = float(simulation_parameters[excel_strings.SimulationMonteCarloColumn.DURATION])
            self.minimum_number_of_simulations = int(simulation_parameters[
                excel_strings.SimulationMonteCarloColumn.MINIMUM_NUMBER_OF_SIMULATION])
            self.maximum_number_of_simulations = int(xlsx_utils.read_cell_str_with_default(
                simulation_parameters, excel_strings.SimulationMonteCarloColumn.MAXIMUM_NUMBER_OF_SIMULATION,
                self.EXCEPTION_HINT_MESSAGE,
                self.minimum_number_of_simulations))
            self.convergence_margin = float(xlsx_utils.read_cell_str_with_default(
                simulation_parameters, excel_strings.SimulationMonteCarloColumn.CONVERGENCE_MARGIN,
                self.EXCEPTION_HINT_MESSAGE, 0))
            self.maximum_execution_time = float(xlsx_utils.read_cell_str_with_default(
                simulation_parameters, excel_strings.SimulationMonteCarloColumn.MAXIMUM_EXECUTION_TIME,
                self.EXCEPTION_HINT_MESSAGE, self.simulation_duration * 10))
            self.seed = xlsx_utils.clean_int_cell(simulation_parameters, excel_strings.SimulationMonteCarloColumn.SEED,
                                                  self.EXCEPTION_HINT_MESSAGE, optional=True)
            self.diagnostics = xlsx_utils.read_cell_list_with_default(
                simulation_parameters, excel_strings.SimulationMonteCarloColumn.DIAGNOSTICS,
                self.EXCEPTION_HINT_MESSAGE, ["SUMMARY"])

    @classmethod
    def build(cls, simulation_parameters: Dict[str, str], stages_number: int = 1) -> Simulation:
        """MonteCarloReader takes parameters from the sumulation_parameters dictionary and returns a MonteCarlo object.
        """
        params = cls.MonteCarloParameters(simulation_parameters)
        return MonteCarlo(
            params.minimum_number_of_simulations,
            params.maximum_number_of_simulations,
            params.convergence_margin,
            params.maximum_execution_time,
            params.seed,
            params.diagnostics,
            params.simulation_duration,
            stages_number
        )
