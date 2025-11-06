# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import glob
import os
import random
import shutil
import unittest

from availsim4core import main
from availsim4core.test.E2E.E2E_utils import Result


class test_E2E_held(unittest.TestCase):
    # no phase ==> already done by all other tests without phase
    # test with phases are for now done with AND logic only, that feature is customized for the LHC model

    expected_result_scenario_1 = [
        Result(9, "A_1_5", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(8, "A_1_5", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(9, "D_0_3", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(8, "D_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(9, "D_0_6", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(8, "D_0_6", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(9, "D_0_9", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(8, "D_0_9", "*", "FAILED", "_MEAN_OCCURRENCES")
    ]
    for component_name in ["Phase","ROOT_0_1",
                           "A_0_2","D_0_3","E_0_4","A_1_5","D_0_6","E_0_7","A_2_8","D_0_9","E_0_10","B_0_11","C_0_12"]:
        expected_result_scenario_1.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_1 = \
        ["./availsim4core/test/E2E/input/held/simulation.xlsx",
         "./availsim4core/test/E2E/input/held/no_phase__no_held__system.xlsx",
         None,
         1,
         expected_result_scenario_1]

    expected_result_scenario_2 = [
        Result(1, "A_1_5", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "*", "HELD", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "*", "HELD", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "*", "HELD", "_MEAN_OCCURRENCES")
    ]
    for component_name in ["Phase", "ROOT_0_1",
                           "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9", "E_0_10", "B_0_11",
                           "C_0_12"]:
        expected_result_scenario_2.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_2 = \
        ["./availsim4core/test/E2E/input/held/simulation.xlsx",
         "./availsim4core/test/E2E/input/held/no_phase__held_after_repair__system.xlsx",
         None,
         1,
         expected_result_scenario_2]

    expected_result_scenario_3 = [
        Result(6, "A_1_5", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(4, "A_1_5", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(6, "D_0_3", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(4, "D_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(6, "D_0_6", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(4, "D_0_6", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(6, "D_0_9", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(4, "D_0_9", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(5, "A_1_5", "P1", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(4, "A_1_5", "P1", "FAILED", "_MEAN_OCCURRENCES"),
        Result(5, "D_0_3", "P1", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(4, "D_0_3", "P1", "FAILED", "_MEAN_OCCURRENCES"),
        Result(5, "D_0_6", "P1", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(4, "D_0_6", "P1", "FAILED", "_MEAN_OCCURRENCES"),
        Result(5, "D_0_9", "P1", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(4, "D_0_9", "P1", "FAILED", "_MEAN_OCCURRENCES")
    ]
    for component_name in ["Phase", "ROOT_0_1",
                           "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9", "E_0_10", "B_0_11",
                           "C_0_12"]:
        expected_result_scenario_3.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_3 = \
        ["./availsim4core/test/E2E/input/held/simulation.xlsx",
         "./availsim4core/test/E2E/input/held/phase__no_held__system.xlsx",
         None,
         1,
         expected_result_scenario_3]

    expected_result_scenario_4 = [
        Result(2, "A_1_5", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(2, "D_0_3", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(2, "D_0_6", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(2, "D_0_9", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(1, "A_1_5", "P1", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "P1", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "P1", "FAILED", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "P1", "HELD", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "P1", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "P1", "FAILED", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "P1", "HELD", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "P1", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "P1", "FAILED", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "P1", "HELD", "_MEAN_OCCURRENCES"),
        Result(1, "A_1_5", "P2", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "P2", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "P2", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "P2", "RUNNING", "_MEAN_OCCURRENCES"),
    ]
    for component_name in ["Phase", "ROOT_0_1",
                           "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9", "E_0_10", "B_0_11",
                           "C_0_12"]:
        expected_result_scenario_4.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_4 = \
        ["./availsim4core/test/E2E/input/held/simulation.xlsx",
         "./availsim4core/test/E2E/input/held/phase__held_after_repair__system.xlsx",
         None,
         1,
         expected_result_scenario_4]

    expected_result_scenario_5 = [
        Result(1, "A_1_5", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(0, "D_0_3", "*", "HELD", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(0, "D_0_6", "*", "HELD", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(0, "D_0_9", "*", "HELD", "_MEAN_OCCURRENCES")
    ]
    for component_name in ["Phase", "ROOT_0_1",
                           "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9", "E_0_10", "B_0_11",
                           "C_0_12"]:
        expected_result_scenario_5.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_5 = \
        ["./availsim4core/test/E2E/input/held/simulation.xlsx",
         "./availsim4core/test/E2E/input/held/no_phase__held_before_repair__system.xlsx",
         None,
         1,
         expected_result_scenario_5]

    expected_result_scenario_6 = [
        Result(2, "A_1_5", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(2, "A_1_5", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(2, "D_0_3", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(2, "D_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(2, "D_0_6", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(2, "D_0_6", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(2, "D_0_9", "*", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(2, "D_0_9", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(1, "A_1_5", "P1", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "A_1_5", "P1", "FAILED", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "P1", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "P1", "FAILED", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "P1", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "P1", "FAILED", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "P1", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "P1", "FAILED", "_MEAN_OCCURRENCES"),
        Result(1, "A_1_5", "P2", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_3", "P2", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_6", "P2", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(1, "D_0_9", "P2", "RUNNING", "_MEAN_OCCURRENCES"),
    ]
    for component_name in ["Phase", "ROOT_0_1",
                           "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9", "E_0_10", "B_0_11",
                           "C_0_12"]:
        expected_result_scenario_6.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_6 = \
        ["./availsim4core/test/E2E/input/held/simulation.xlsx",
         "./availsim4core/test/E2E/input/held/phase__held_before_repair__system.xlsx",
         None,
         1,
         expected_result_scenario_6]

    param_scenario = [
        scenario_1,
        scenario_2,
        scenario_3,
        scenario_4,
        scenario_5,
        scenario_6,
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

        output_folder = "./availsim4core/test/E2E/output/held/"

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
