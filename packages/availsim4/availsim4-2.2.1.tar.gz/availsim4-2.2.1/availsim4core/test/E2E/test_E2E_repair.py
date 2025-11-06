# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import glob
import os
import random
import shutil
import unittest

from availsim4core import main
from availsim4core.test.E2E.E2E_utils import Result


class test_repair(unittest.TestCase):
    """
    class testing the repair feature
    """

    # testing the failure and repair of a unique component
    expected_result_scenario_1 = [Result(10, "DUMB_0_1", "NONE", "UNDER_REPAIR", "_MEAN_OCCURRENCES")]
    scenario_1_no_sensitivity_analysis_single_component = \
        ["./availsim4core/test/E2E/input/repair/testRepair_simulation.xlsx",
         "./availsim4core/test/E2E/input/repair/testRepair_scenario_1_system.xlsx",
         None,
         1,
         expected_result_scenario_1]

    # testing the failure and repair of many components, results are similar to a unique component as failure and repair are in parallel
    expected_result_scenario_2 = [Result(10, "DUMB_0_1", "NONE", "UNDER_REPAIR", "_MEAN_OCCURRENCES")]
    scenario_2_no_sensitivity_analysis_single_component = \
        ["./availsim4core/test/E2E/input/repair/testRepair_simulation.xlsx",
         "./availsim4core/test/E2E/input/repair/testRepair_scenario_2_system.xlsx",
         None,
         1,
         expected_result_scenario_2]

    param_scenario = [
        scenario_1_no_sensitivity_analysis_single_component,
        scenario_2_no_sensitivity_analysis_single_component,
    ]

    def test_runner(self):
        # randomize the order of the test execution to detect hidden dependencies
        random.shuffle(self.param_scenario)
        for simulation_file, system_file, sensitivity_file, expected_number_file_result, expected_mean_result in self.param_scenario:
            with self.subTest():
                self._runner_E2E(simulation_file, system_file, sensitivity_file, expected_number_file_result,
                                 expected_mean_result)

    def _runner_E2E(self, simulation_file, system_file, sensitivity_file, expected_number_file_result,
                    expected_result_list):

        output_folder = "./availsim4core/test/E2E/output/repair/"

        # Clean folder
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)

        # Run the main process
        main.start(simulation_file, system_file, output_folder, sensitivity_file)

        result_simulation_file_list = glob.glob(output_folder + "/*.xlsx")
        self.assertEqual(len(result_simulation_file_list), expected_number_file_result)

        for expected_result in expected_result_list:
            actual_result = expected_result.extract_result(result_simulation_file_list)
            if expected_result.tolerance == -1:
                self.assertEqual(expected_result.expected_result, actual_result)
            else:
                self.assertAlmostEqual(expected_result.expected_result, actual_result, places=expected_result.tolerance)


if __name__ == '__main__':
    unittest.main()
