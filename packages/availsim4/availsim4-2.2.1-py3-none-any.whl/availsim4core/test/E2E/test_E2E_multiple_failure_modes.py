# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import glob
import os
import random
import shutil
import unittest

from availsim4core import main
from availsim4core.test.E2E.E2E_utils import Result


class test_E2E_multiple_failure_modes(unittest.TestCase):

    expected_result_scenario_1 = [
        Result(95.5, "ROOT_0_1","*","RUNNING","_MEAN_DURATION"),
        Result(2, "A_1_5", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "A_1_5", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(1, "B_0_11", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(2, "D_0_3", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(2, "D_0_6", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(2, "D_0_9", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(2, "E_0_4", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "E_0_4", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(2, "E_0_7", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "E_0_7", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(2, "E_0_10", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "E_0_10", "*", "FAILED", "_MEAN_OCCURRENCES")
    ]
    for component_name in ["Phase","ROOT_0_1",
                           "A_0_2","D_0_3","E_0_4","A_1_5","D_0_6","E_0_7","A_2_8","D_0_9","E_0_10","B_0_11","C_0_12"]:
        expected_result_scenario_1.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_1 = \
        ["./availsim4core/test/E2E/input/multiple_failure_modes/simulation.xlsx",
         "./availsim4core/test/E2E/input/multiple_failure_modes/no_multiple_fm__no_phase__no_held__system.xlsx",
         None,
         1,
         expected_result_scenario_1]

    expected_result_scenario_2 = [
        Result(95.5, "ROOT_0_1", "*", "RUNNING", "_MEAN_DURATION"),
#        Result(2, "A_1_5", "*", "RUNNING", "_MEAN_OCCURRENCES"),
#        Result(1, "A_1_5", "*", "FAILED", "_MEAN_OCCURRENCES"),
#        Result(1, "B_0_11", "*", "RUNNING", "_MEAN_OCCURRENCES"),
#        Result(2, "D_0_3", "*", "RUNNING", "_MEAN_OCCURRENCES"),
#        Result(1, "D_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
#        Result(2, "D_0_6", "*", "RUNNING", "_MEAN_OCCURRENCES"),
#        Result(1, "D_0_6", "*", "FAILED", "_MEAN_OCCURRENCES"),
#        Result(2, "D_0_9", "*", "RUNNING", "_MEAN_OCCURRENCES"),
#        Result(1, "D_0_9", "*", "FAILED", "_MEAN_OCCURRENCES"),
#        Result(2, "E_0_4", "*", "RUNNING", "_MEAN_OCCURRENCES"),
#        Result(1, "E_0_4", "*", "FAILED", "_MEAN_OCCURRENCES"),
#        Result(2, "E_0_7", "*", "RUNNING", "_MEAN_OCCURRENCES"),
#        Result(1, "E_0_7", "*", "FAILED", "_MEAN_OCCURRENCES"),
#        Result(2, "E_0_10", "*", "RUNNING", "_MEAN_OCCURRENCES"),
#        Result(1, "E_0_10", "*", "FAILED", "_MEAN_OCCURRENCES")
    ]
    for component_name in ["Phase", "ROOT_0_1",
                           "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9", "E_0_10", "B_0_11",
                           "C_0_12"]:
        expected_result_scenario_2.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_2 = \
        ["./availsim4core/test/E2E/input/multiple_failure_modes/simulation.xlsx",
         "./availsim4core/test/E2E/input/multiple_failure_modes/multiple_fm__no_phase__no_held__system.xlsx",
         None,
         1,
         expected_result_scenario_2]

    param_scenario = [
        scenario_1,
        #scenario_2, # need for a bug fix !
    ]

    def test_runner(self):
        # randomize the order of the test execution to detect hidden dependencies
        random.shuffle(self.param_scenario)
        for simulation_file, system_file, sensitivity_file, expected_number_file_result, expected_result_list in self.param_scenario:
            with self.subTest():
                self._runner_E2E(simulation_file,
                                 system_file,
                                 sensitivity_file,
                                 expected_number_file_result,
                                 expected_result_list)

    def _runner_E2E(self,
                    simulation_file,
                    system_file,
                    sensitivity_file,
                    expected_number_file_result,
                    expected_result_list):

        output_folder = "./availsim4core/test/E2E/output/multiple_failure_modes/"

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
