# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import glob
import os
import random
import shutil
import unittest

from availsim4core import main
from availsim4core.test.E2E.E2E_utils import Result


class test_E2E_phase_jump(unittest.TestCase):

    expected_result_scenario_1 = [
        Result(0, "ROOT_0_11", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(0, "ROOT_0_11", "*", "DEGRADED", "_MEAN_OCCURRENCES"),
        Result(11, "Phase", "P1", "*", "_MEAN_OCCURRENCES"),
        Result(11, "Phase", "P2", "*", "_MEAN_OCCURRENCES"),
        Result(11, "Phase", "P3", "*", "_MEAN_OCCURRENCES"),
        Result(11, "Phase", "P4", "*", "_MEAN_OCCURRENCES"),
    ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "B_0_3"]:
        expected_result_scenario_1.append(Result(100, component_name, "*", "*", "_MEAN_DURATION",tolerance=6))
    scenario_1 = \
        ["./availsim4core/test/E2E/input/phase_jump/simulation.xlsx",
         "./availsim4core/test/E2E/input/phase_jump/base_scenario.xlsx",
         "",
         1,
         expected_result_scenario_1]

    expected_result_scenario_2 = [
        Result(0, "ROOT_0_11", "*", "FAILED", "_MEAN_OCCURRENCES"),
        Result(0, "ROOT_0_11", "*", "DEGRADED", "_MEAN_OCCURRENCES"),
        Result(11, "Phase", "P5", "*", "_MEAN_OCCURRENCES"),
    ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "B_0_3"]:
        expected_result_scenario_2.append(Result(100, component_name, "*", "*", "_MEAN_DURATION",tolerance=6))
    scenario_2 = \
        ["./availsim4core/test/E2E/input/phase_jump/simulation.xlsx",
         "./availsim4core/test/E2E/input/phase_jump/phase_jump.xlsx",
         "",
         1,
         expected_result_scenario_2]

    # Test of how well phase jumps mechanism handles potential infinite loops caused by user
    # defining same phase in FROM_PHASE and TO_PHASE in PHASE_JUMP sheet
    expected_result_scenario_3 = [
        Result(75, "ROOT_0_1", "*", "DEGRADED", "_MEAN_OCCURRENCES"),
        Result(25, "ROOT_0_1", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
        Result(26, "Phase", "NORMAL", "*", "_MEAN_OCCURRENCES"),
    ]
    scenario_3 = \
        ["./availsim4core/test/E2E/input/phase_jump/simulation.xlsx",
         "./availsim4core/test/E2E/input/phase_jump/phase_jump_inifinite_loop_test.xlsx",
         None,
         1,
         expected_result_scenario_3]

    param_scenario = [
        scenario_1,
        scenario_2,
        scenario_3
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

        output_folder = "./availsim4core/test/E2E/output/phase_jump/"

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
