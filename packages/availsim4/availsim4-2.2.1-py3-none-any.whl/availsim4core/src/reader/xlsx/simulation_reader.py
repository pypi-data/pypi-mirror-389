# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
This module contains classes used for handling the reading the simulation file.
"""

import logging
import pathlib
from availsim4core.resources import excel_strings

from availsim4core.src.exporter.export_manager import DiagnosticType
from availsim4core.src.reader.reader import Reader
from availsim4core.src.reader.xlsx.monte_carlo_reader import MonteCarloReader
from availsim4core.src.reader.xlsx.quasi_monte_carlo_reader import QuasiMonteCarloReader
from availsim4core.src.reader.xlsx.splitting_monte_carlo_reader import SplittingMonteCarloReader
from availsim4core.src.reader.xlsx import xlsx_utils


class SimulationNotFoundError(Exception):
    """
    Error thrown if the string specifying simulation type is not found among the options defined in
    the framework.
    """


class DiagnosticNotFoundError(Exception):
    """
    Error thrown if the string specifying a diagnostic type is not found among the options defined
    in the framework.
    """


class SimulationReader(Reader):
    """
    Specific reader for the simulation file. Its primary objective is to create a Simulation object initialized with
    parameters defined by the user in the input file.
    """

    def read(self, file_path: pathlib.Path, stages_number: int = 1):
        """
        Generate a simulation based on the given XLSX file path.

        Args:
            simulation_file_path: pathlib.Path
                Path to the XLSX file with the simulation configuration.

        Returns:
            Simulation object with parameters according to the input file.
        """

        initial_simulation_dictionary = xlsx_utils.read(file_path)

        simulation_parameters = initial_simulation_dictionary[excel_strings.SimulationSheet.SHEET][0]
        simulation_type = simulation_parameters[excel_strings.SimulationSheet.TYPE]
        logging.debug("Reading simulation = %s", simulation_type)

        if excel_strings.SimulationType.MONTE_CARLO == simulation_type:
            simulation = MonteCarloReader.build(simulation_parameters, stages_number)
        elif excel_strings.SimulationType.QUASI_MONTE_CARLO == simulation_type:
            simulation = QuasiMonteCarloReader.build(simulation_parameters, stages_number)
        elif excel_strings.SimulationType.SPLITTING_MONTE_CARLO == simulation_type:
            simulation = SplittingMonteCarloReader.build(simulation_parameters)
        else:
            message_exception = f"Simulation {simulation_type} not found"
            logging.exception(message_exception)
            raise SimulationNotFoundError(message_exception)

        for diagnostic in simulation.list_of_diagnosis:
            if diagnostic not in DiagnosticType.DIAGNOSTIC_EXPORTER:
                if "CRITICAL_FAILURE_PATHS" in str(diagnostic):
                    # the CRITICAL_FAILURE_PATHS diagnostic could have an argument between
                    # parenthesis such as:
                    # CRITICAL_FAILURE_PATHS(specific_component_name)
                    pass
                else:
                    message_exception = f"Diagnostic {diagnostic} not found"
                    logging.exception(message_exception)
                    raise DiagnosticNotFoundError(message_exception)

        return simulation
