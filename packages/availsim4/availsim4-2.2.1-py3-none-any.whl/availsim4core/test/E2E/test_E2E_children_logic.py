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
    expected_degraded_mean = Result(1, "ROOT_0_1", "NONE", "DEGRADED", "_MEAN_OCCURRENCES")
    expected_running_mean = Result(11, "BLINKING_0_4", "NONE", "RUNNING", "_MEAN_OCCURRENCES")
    expected_result_scenario_1 = [expected_degraded_mean, expected_running_mean]
    scenario_1_OO = \
        ["./availsim4core/test/E2E/input/children_logic/simulation.xlsx",
         "./availsim4core/test/E2E/input/children_logic/OO1_system.xlsx",
         None,
         1,
         expected_result_scenario_1]
    scenario_1_TF = \
        ["./availsim4core/test/E2E/input/children_logic/simulation.xlsx",
         "./availsim4core/test/E2E/input/children_logic/TF1_system.xlsx",
         None,
         1,
         expected_result_scenario_1]
    scenario_1_RC = \
        ["./availsim4core/test/E2E/input/children_logic/simulation.xlsx",
         "./availsim4core/test/E2E/input/children_logic/RC1_system.xlsx",
         None,
         1,
         expected_result_scenario_1]

    # never enough systems to satisfy the children_logic logic
    expected_degraded_mean = Result(1, "ROOT_0_1", "NONE", "DEGRADED", "_MEAN_OCCURRENCES")
    expected_running_mean = Result(11, "BLINKING_0_4", "NONE", "RUNNING", "_MEAN_OCCURRENCES")
    expected_result_scenario_2 = [expected_degraded_mean, expected_running_mean]
    scenario_2_OO = \
        ["./availsim4core/test/E2E/input/children_logic/simulation.xlsx",
         "./availsim4core/test/E2E/input/children_logic/OO2_system.xlsx",
         None,
         1,
         expected_result_scenario_2]
    scenario_2_TF = \
        ["./availsim4core/test/E2E/input/children_logic/simulation.xlsx",
         "./availsim4core/test/E2E/input/children_logic/TF2_system.xlsx",
         None,
         1,
         expected_result_scenario_2]
    scenario_2_RC = \
        ["./availsim4core/test/E2E/input/children_logic/simulation.xlsx",
         "./availsim4core/test/E2E/input/children_logic/RC2_system.xlsx",
         None,
         1,
         expected_result_scenario_2]

    # blinking component satisfying the children_logic logic
    expected_degraded_mean = Result(11, "ROOT_0_1", "NONE", "DEGRADED", "_MEAN_OCCURRENCES")
    expected_running_mean = Result(11, "BLINKING_0_4", "NONE", "RUNNING", "_MEAN_OCCURRENCES")
    expected_result_scenario_3 = [expected_degraded_mean, expected_running_mean]
    scenario_3_OO = \
        ["./availsim4core/test/E2E/input/children_logic/simulation.xlsx",
         "./availsim4core/test/E2E/input/children_logic/OO3_system.xlsx",
         None,
         1,
         expected_result_scenario_3]
    scenario_3_TF = \
        ["./availsim4core/test/E2E/input/children_logic/simulation.xlsx",
         "./availsim4core/test/E2E/input/children_logic/TF3_system.xlsx",
         None,
         1,
         expected_result_scenario_3]
    scenario_3_RC = \
        ["./availsim4core/test/E2E/input/children_logic/simulation.xlsx",
         "./availsim4core/test/E2E/input/children_logic/RC3_system.xlsx",
         None,
         1,
         expected_result_scenario_3]

    param_scenario = [
        scenario_1_OO,
        scenario_1_TF,
        scenario_1_RC,
        scenario_2_OO,
        scenario_2_TF,
        scenario_2_RC,
        scenario_3_OO,
        scenario_3_TF,
        scenario_3_RC,
    ]


    def test_runner(self):
        # randomize the order of the test execution to detect hidden dependencies
        random.shuffle(self.param_scenario)
        for simulation_file, system_file, sensitivity_file, expected_number_file_result, expected_result_list in self.param_scenario:
            with self.subTest():
                self._runner_E2E(simulation_file, system_file, sensitivity_file, expected_number_file_result,
                                 expected_result_list)

    def _runner_E2E(self, simulation_file, system_file, sensitivity_file, expected_number_file_result,
                    expected_result_list):

        output_folder = "./availsim4core/test/E2E/output/children_logic/"

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
