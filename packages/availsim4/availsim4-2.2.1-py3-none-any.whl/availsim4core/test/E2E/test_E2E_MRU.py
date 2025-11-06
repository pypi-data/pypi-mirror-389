# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import glob
import os
import random
import shutil
import unittest

from availsim4core import main
from availsim4core.test.E2E.E2E_utils import Result


class test_MRU(unittest.TestCase):
    """
    Ensemble of tests used to test the Minimal Replaceable Unit feature
    """

    expected_result_scenario_1 = [Result(3, "B1_0_3", "NONE", "FAILED", "_MEAN_OCCURRENCES")]
    scenario_1_no_MRU = \
        ["./availsim4core/test/E2E/input/mru/simulation.xlsx",
         "./availsim4core/test/E2E/input/mru/no_active_mru_system.xlsx",
         None,
         1,
         expected_result_scenario_1]

    expected_result_scenario_2 = [Result(2, "B1_0_3", "NONE", "FAILED", "_MEAN_OCCURRENCES")]
    scenario_2_basic_trigger_itself = \
        ["./availsim4core/test/E2E/input/mru/simulation.xlsx",
         "./availsim4core/test/E2E/input/mru/basic_trigger_itself_system.xlsx",
         None,
         1,
         expected_result_scenario_2]

    expected_result_scenario_3 = [Result(3, "A2_0_11", "NONE", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(3, "B1_0_3", "NONE", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(3, "B2_0_4", "NONE", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(3, "B3_0_6", "NONE", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(3, "B3_1_7", "NONE", "UNDER_REPAIR", "_MEAN_OCCURRENCES")]
    scenario_3_basic_trigger = \
        ["./availsim4core/test/E2E/input/mru/simulation.xlsx",
         "./availsim4core/test/E2E/input/mru/basic_trigger_system.xlsx",
         None,
         1,
         expected_result_scenario_3]

    expected_result_scenario_4 = [Result(3, "A2_0_11", "NONE", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(3, "B1_0_3", "NONE", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(3, "B2_0_4", "NONE", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(3, "B3_0_6", "NONE", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(3, "B3_1_7", "NONE", "UNDER_REPAIR", "_MEAN_OCCURRENCES")]
    scenario_4_compound_trigger = \
        ["./availsim4core/test/E2E/input/mru/simulation.xlsx",
         "./availsim4core/test/E2E/input/mru/compound_trigger_system.xlsx",
         None,
         1,
         expected_result_scenario_4]

    # multiple MRU in the system
    # one component trigger its own replacement plus other replacements
    expected_result_scenario_5_v1 = [Result(2, "D_0_1", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(1, "D_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(1, "D_0_1", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(2, "C1_0_2", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(1, "C1_0_2", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(1, "C1_0_2", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(2, "C2_0_3", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(0, "C2_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(1, "C2_0_3", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(1, "C3_0_4", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(0, "C3_0_4", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(0, "C3_0_4", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  ]
    scenario_5_v1 = \
        ["./availsim4core/test/E2E/input/mru/simulation.xlsx",
         "./availsim4core/test/E2E/input/mru/multiple_mru_v1_system.xlsx",
         None,
         1,
         expected_result_scenario_5_v1]

    # multiple MRU in the system
    # one component trigger its own replacement plus other replacements, BLIND_FAILURES used
    expected_result_scenario_5_v2 = [Result(2, "D_0_1", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                     Result(1, "D_0_1", "*", "BLIND_FAILED", "_MEAN_OCCURRENCES"),
                                     Result(0, "D_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                     Result(1, "D_0_1", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                     Result(2, "C1_0_2", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                     Result(1, "C1_0_2", "*", "BLIND_FAILED", "_MEAN_OCCURRENCES"),
                                     Result(0, "C1_0_2", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                     Result(1, "C1_0_2", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                     Result(2, "C2_0_3", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                     Result(0, "C2_0_3", "*", "BLIND_FAILED", "_MEAN_OCCURRENCES"),
                                     Result(0, "C2_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                     Result(1, "C2_0_3", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                     Result(1, "C3_0_4", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                     Result(0, "C3_0_4", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                     Result(0, "C3_0_4", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  ]
    scenario_5_v2 = \
        ["./availsim4core/test/E2E/input/mru/simulation.xlsx",
         "./availsim4core/test/E2E/input/mru/multiple_mru_v2_system.xlsx",
         None,
         1,
         expected_result_scenario_5_v2]

    # multiple MRU in the system
    # one component trigger several MRU for several components
    expected_result_scenario_5_v3 = [Result(2, "D_0_1", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(1, "D_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(1, "D_0_1", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(2, "C1_0_2", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(1, "C1_0_2", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(1, "C1_0_2", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(2, "C2_0_3", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(0, "C2_0_3", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(1, "C2_0_3", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(2, "C3_0_4", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(0, "C3_0_4", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(1, "C3_0_4", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(1, "C4_0_5", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(0, "C4_0_5", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(0, "C4_0_5", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  ]
    scenario_5_v3 = \
        ["./availsim4core/test/E2E/input/mru/simulation.xlsx",
         "./availsim4core/test/E2E/input/mru/multiple_mru_v3_system.xlsx",
         None,
         1,
         expected_result_scenario_5_v3]

    # multiple MRU in the system
    # idem than v3, only some permutations in the input are performed but they should not have any impacts
    scenario_5_v4 = \
        ["./availsim4core/test/E2E/input/mru/simulation.xlsx",
         "./availsim4core/test/E2E/input/mru/multiple_mru_v4_system.xlsx",
         None,
         1,
         expected_result_scenario_5_v3]

    param_scenario = [
        scenario_1_no_MRU,
        scenario_2_basic_trigger_itself,
        scenario_3_basic_trigger,
        scenario_4_compound_trigger,
        scenario_5_v1,
        scenario_5_v2,
        scenario_5_v3,
        scenario_5_v4,
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

        output_folder = "./availsim4core/test/E2E/output/mru/"

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
