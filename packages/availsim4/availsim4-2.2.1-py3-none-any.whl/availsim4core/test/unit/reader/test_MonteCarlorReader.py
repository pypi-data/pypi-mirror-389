# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.reader.xlsx.monte_carlo_reader import MonteCarloReader
from availsim4core.src.simulation.monte_carlo import MonteCarlo


class test_MonteCarloReader(unittest.TestCase):

    def test_build(self):
        line = {'SIMULATION_TYPE': "MONTE_CARLO",
                'MIN_NUMBER_OF_SIMULATION': "100",
                'MAX_NUMBER_OF_SIMULATION': "100",
                'CONVERGENCE_MARGIN': "2",
                'MAX_EXECUTION_TIME': "600",
                'SEED': "1",
                'DIAGNOSTICS': "summary",
                'SIMULATION_DURATION': "1000"}

        expected_result = MonteCarlo(100, 100, 2, 600, 1, ["SUMMARY"], 1000)
        result = MonteCarloReader.build(line)
        self.assertEqual(expected_result, result)

    def test_build_with_list_of_diagnosis(self):
        line = {'SIMULATION_TYPE': "MONTE_CARLO",
                'MIN_NUMBER_OF_SIMULATION': "100",
                'MAX_NUMBER_OF_SIMULATION': "100",
                'CONVERGENCE_MARGIN': "2",
                'MAX_EXECUTION_TIME': "600",
                'SEED': "1",
                'DIAGNOSTICS': "summary,last_timeline",
                'SIMULATION_DURATION': "1000"}

        expected_result = MonteCarlo(100, 100, 2, 600, 1, ["SUMMARY","LAST_TIMELINE"], 1000)
        result = MonteCarloReader.build(line)
        self.assertEqual(expected_result, result)
