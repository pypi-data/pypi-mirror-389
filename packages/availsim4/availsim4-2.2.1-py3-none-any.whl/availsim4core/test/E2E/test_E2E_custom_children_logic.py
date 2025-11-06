# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import glob
import os
import random
import shutil
import unittest

from availsim4core import main
from availsim4core.test.E2E.E2E_utils import Result


class test_children_logic(unittest.TestCase):

    # always enough systems to satisfy the children_logic logic
    expected_result_scenario_1 = [
        Result(1, "ROOT_0_1", "STANDARD", "DEGRADED", "_MEAN_OCCURRENCES"),
        Result(0, "ROOT_0_1", "OTHER", "DEGRADED", "_MEAN_OCCURRENCES"),
        Result(4, "BLINKING_0_4", "STANDARD", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(2, "BLINKING_0_4", "OTHER", "RUNNING", "_MEAN_OCCURRENCES")

    ]
    scenario_1 = \
        ["./availsim4core/test/E2E/input/custom_children_logic/simulation.xlsx",
         "./availsim4core/test/E2E/input/custom_children_logic/system.xlsx",
         None,
         "./availsim4core/test/E2E/input/custom_children_logic/custom_children_logic.py",
         1,
         expected_result_scenario_1]

    param_scenario = [
        scenario_1
    ]

    def test_runner(self):
        # randomize the order of the test execution to detect hidden dependencies
        random.shuffle(self.param_scenario)
        for simulation_file, system_file, sensitivity_file, custom_children_logic_path, expected_number_file_result, expected_result_list\
                in self.param_scenario:
            with self.subTest():
                self._runner_E2E(simulation_file, system_file, sensitivity_file, custom_children_logic_path,
                                 expected_number_file_result, expected_result_list)

    def _runner_E2E(self, simulation_file, system_file, sensitivity_file, custom_children_logic_path,
                    expected_number_file_result, expected_result_list):

        output_folder = "./availsim4core/test/E2E/output/custom_children_logic/"

        # Clean folder
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)

        # Run the main process
        main.start(simulation_file, system_file, output_folder, sensitivity_file,
                   custom_children_logic_path=custom_children_logic_path)

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
