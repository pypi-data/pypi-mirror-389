# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import glob
import os
import random
import shutil
import unittest

from availsim4core import main
from availsim4core.test.E2E.E2E_utils import Result, RCAResult


class test_E2E_RCA(unittest.TestCase):
    # the Root Cause Analysis (RCA) makes it possible to save the state of the system when a selected component enters
    # a given status (both paramters specified in the input). Tests checking if the RCA feature detects and dumps the
    # results correctly are defined here - they compare the "summary" output to the "rca" output. Different input files
    # are used to identify cases where any other feature (like inspections, MRU or shared children) could prevent the
    # RCA to work properly.

    # WARNING: results size in the RCA sheet depend strongly on the number of performed simulations, as snapshots are
    # appended to the results list every time the conditions are met. Therefore, performing 10 simulations instead of
    # 1 increases the results size by a factor 10. The feature is designed primarily for rare events, but it is not
    # enforced in any way, i.e., it is ultimately user's decision of how many snapshots they want to record.

    expected_result_scenario_1 = [Result(10, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES",),
                                  Result(10, "A_0_2", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  RCAResult(100, "ROOT_0_1", "*", "FAILED")]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2"]:
        expected_result_scenario_1.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_1 = \
        ["./availsim4core/test/E2E/input/RCA/simulation.xlsx",
         "./availsim4core/test/E2E/input/RCA/ROOT__AND__system.xlsx",
         None,
         1,
         expected_result_scenario_1]

    expected_result_scenario_2 = [Result(10, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(10, "A_0_2", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  RCAResult(100, "ROOT_0_1", "*", "FAILED"),
                                  RCAResult(100, "A_0_2", "*", "FAILED")]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2"]:
        expected_result_scenario_2.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_2 = \
        ["./availsim4core/test/E2E/input/RCA/simulation.xlsx",
         "./availsim4core/test/E2E/input/RCA/ROOT_A__AND__system.xlsx",
         None,
         1,
         expected_result_scenario_2]

    expected_result_scenario_3 = [Result(0, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(10, "A_0_2", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  RCAResult(0, "ROOT_0_1", "*", "FAILED")]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2"]:
        expected_result_scenario_3.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_3 = \
        ["./availsim4core/test/E2E/input/RCA/simulation.xlsx",
         "./availsim4core/test/E2E/input/RCA/ROOT__1OO2__system.xlsx",
         None,
         1,
         expected_result_scenario_3]

    expected_result_scenario_4 = [Result(0, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(10, "A_0_2", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  RCAResult(0, "ROOT_0_1", "*", "FAILED"),
                                  RCAResult(100, "A_0_2", "*", "FAILED")]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2"]:
        expected_result_scenario_4.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_4 = \
        ["./availsim4core/test/E2E/input/RCA/simulation.xlsx",
         "./availsim4core/test/E2E/input/RCA/ROOT_A__1OO2__system.xlsx",
         None,
         1,
         expected_result_scenario_4]

    expected_result_scenario_5 = [Result(10, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(10, "A_0_2", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(10, "S_0_4", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  RCAResult(100, "ROOT_0_1", "*", "FAILED"),
                                  RCAResult(100, "S_0_4", "*", "FAILED")]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "B_0_5", "C_0_3", "S_0_4"]:
        expected_result_scenario_5.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_5 = \
        ["./availsim4core/test/E2E/input/RCA/simulation.xlsx",
         "./availsim4core/test/E2E/input/RCA/shared__AND__AND__system.xlsx",
         None,
         1,
         expected_result_scenario_5]

    expected_result_scenario_6 = [Result(5, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(5, "A_0_2", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(0, "B_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  RCAResult(50, "ROOT_0_1", "*", "FAILED"),
                                  RCAResult(50, "A_0_2", "*", "FAILED")]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "B_0_3"]:
        expected_result_scenario_6.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_6 = \
        ["./availsim4core/test/E2E/input/RCA/simulation.xlsx",
         "./availsim4core/test/E2E/input/RCA/ROOT_A__AND__with_phases__v1__system.xlsx",
         None,
         1,
         expected_result_scenario_6]

    expected_result_scenario_7 = [Result(5, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(5, "A_0_2", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(0, "B_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  RCAResult(50, "ROOT_0_1", "*", "FAILED"),
                                  RCAResult(50, "A_0_2", "*", "FAILED"),
                                  RCAResult(50, "ROOT_0_1", "P1", "FAILED"),
                                  RCAResult(50, "A_0_2", "P1", "FAILED"),
                                  RCAResult(0, "ROOT_0_1", "P2", "FAILED"),
                                  RCAResult(0, "A_0_2", "P2", "FAILED"),
                                  RCAResult(0, "ROOT_0_1", "SAFE", "FAILED"),
                                  RCAResult(0, "A_0_2", "SAFE", "FAILED")
                                  ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "B_0_3"]:
        expected_result_scenario_7.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_7 = \
        ["./availsim4core/test/E2E/input/RCA/simulation.xlsx",
         "./availsim4core/test/E2E/input/RCA/ROOT_A__AND__with_phases__v2__system.xlsx",
         None,
         1,
         expected_result_scenario_7]

    expected_result_scenario_8 = [Result(5, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(5, "A_0_2", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(0, "B_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  RCAResult(50, "ROOT_0_1", "*", "FAILED"),
                                  RCAResult(50, "A_0_2", "*", "FAILED"),
                                  RCAResult(50, "ROOT_0_1", "P1", "FAILED"),
                                  RCAResult(50, "A_0_2", "P1", "FAILED"),
                                  RCAResult(0, "ROOT_0_1", "P2", "FAILED"),
                                  RCAResult(0, "A_0_2", "P2", "FAILED"),
                                  RCAResult(0, "ROOT_0_1", "SAFE", "FAILED"),
                                  RCAResult(0, "A_0_2", "SAFE", "FAILED"),
                                  RCAResult(150, "ROOT_0_1", "*", "RUNNING"),
                                  RCAResult(100, "A_0_2", "*", "RUNNING"),
                                  RCAResult(100, "ROOT_0_1", "P1", "RUNNING"),
                                  RCAResult(100, "A_0_2", "P1", "RUNNING"),
                                  RCAResult(0, "ROOT_0_1", "P2", "RUNNING"),
                                  RCAResult(0, "A_0_2", "P2", "RUNNING"),
                                  RCAResult(50, "ROOT_0_1", "SAFE", "RUNNING"),
                                  RCAResult(0, "A_0_2", "SAFE", "RUNNING")
                                  ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "B_0_3"]:
        expected_result_scenario_8.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_8 = \
        ["./availsim4core/test/E2E/input/RCA/simulation.xlsx",
         "./availsim4core/test/E2E/input/RCA/ROOT_A__AND__with_phases__v3__system.xlsx",
         None,
         1,
         expected_result_scenario_8]

    param_scenario = [
        scenario_1,
        scenario_2,
        scenario_3,
        scenario_4,
        scenario_5,
        scenario_6,
        scenario_7,
        scenario_8
    ]

    def test_runner(self):
        # randomize the order of the test execution to detect hidden dependencies
        # random.shuffle(self.param_scenario)
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

        output_folder = "./availsim4core/test/E2E/output/RCA/"

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
