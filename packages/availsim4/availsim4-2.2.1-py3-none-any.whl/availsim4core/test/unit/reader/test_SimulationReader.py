# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest
from unittest.mock import patch
from availsim4core.src.reader.xlsx import xlsx_utils

from availsim4core.src.reader.xlsx.simulation_reader import SimulationReader, SimulationNotFoundError, \
    DiagnosticNotFoundError
from availsim4core.src.simulation.monte_carlo import MonteCarlo


class test_SimulationReader(unittest.TestCase):

    def test_generate_simulation(self):
        simulation_dict = {'SIMULATION':
            {
                0: {'SIMULATION_TYPE': 'MONTE_CARLO',
                    'MIN_NUMBER_OF_SIMULATION': "100",
                    'MAX_NUMBER_OF_SIMULATION': "100",
                    'CONVERGENCE_MARGIN': "2",
                    'MAX_EXECUTION_TIME': "600",
                    'SEED': "1",
                    'DIAGNOSTICS': "[summary]",
                    'SIMULATION_DURATION': "1000"}
            }
        }

        expected_result = MonteCarlo(100, 100, 2, 600, 1, ["SUMMARY"], 1000)

        with patch.object(xlsx_utils, "read", return_value=simulation_dict):
            result = SimulationReader().read("fake_path")

        self.assertEqual(expected_result, result)

    def test_generate_simulation_with_list_of_diagnostics(self):
        simulation_dict = {'SIMULATION':
            {
                0: {'SIMULATION_TYPE': 'MONTE_CARLO',
                    'MIN_NUMBER_OF_SIMULATION': "100",
                    'MAX_NUMBER_OF_SIMULATION': "100",
                    'CONVERGENCE_MARGIN': "2",
                    'MAX_EXECUTION_TIME': "600",
                    'SEED': "1",
                    'DIAGNOSTICS': "[summary,last_timeline]",
                    'SIMULATION_DURATION': "1000"}
            }
        }

        expected_result = MonteCarlo(100, 100, 2, 600, 1, ["SUMMARY","LAST_TIMELINE"], 1000)

        with patch.object(xlsx_utils, "read", return_value=simulation_dict):
            result = SimulationReader().read("fake_path")

        self.assertEqual(expected_result, result)

    def test_generate_simulation__exception(self):
        simulation_dict = {'SIMULATION':
            {
                0: {'SIMULATION_TYPE': 'FAKE'}
            }
        }

        with patch.object(xlsx_utils, "read", return_value=simulation_dict):
            self.assertRaises(SimulationNotFoundError,
                              SimulationReader().read,
                              "") # TODO what to put here?

    def test_generate_simulation_with_non_existent_diagnostics__exception(self):
        simulation_dict = {'SIMULATION':
            {
                0: {'SIMULATION_TYPE': 'MONTE_CARLO',
                    'MIN_NUMBER_OF_SIMULATION': "100",
                    'MAX_NUMBER_OF_SIMULATION': "100",
                    'CONVERGENCE_MARGIN': "2",
                    'MAX_EXECUTION_TIME': "600",
                    'SEED': "1",
                    'DIAGNOSTICS': "[summary,42]",
                    'SIMULATION_DURATION': "1000"}
            }
        }

        with patch.object(xlsx_utils, "read", return_value=simulation_dict):
            self.assertRaises(DiagnosticNotFoundError,
                              SimulationReader().read,
                              "") # TODO what to put here?
