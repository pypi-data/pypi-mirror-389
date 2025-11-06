# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import glob
import os
import random
import shutil
import unittest

from availsim4core import main
from availsim4core.test.E2E.E2E_utils import Result


class test_Inspection(unittest.TestCase):
    """
    Ensemble of tests used to test the inspection feature
    """

    expected_result_scenario_1 = [Result(4, "A2_0_11", "NONE", "INSPECTION", "_MEAN_OCCURRENCES"),
                                  Result(4, "B4_0_8", "NONE", "INSPECTION", "_MEAN_OCCURRENCES"),
                                  Result(4, "C2_0_5", "NONE", "DEGRADED", "_MEAN_OCCURRENCES"),
                                  Result(4, "D_0_1", "NONE", "DEGRADED", "_MEAN_OCCURRENCES")
                                  ]
    scenario_1_basic_inspection_no_failure = \
        ["./availsim4core/test/E2E/input/inspection/simulation.xlsx",
         "./availsim4core/test/E2E/input/inspection/basic_inspection_no_failure_system.xlsx",
         None,
         1,
         expected_result_scenario_1]

    expected_result_scenario_2 = [Result(4, "A2_0_11", "NONE", "INSPECTION", "_MEAN_OCCURRENCES"),
                                  Result(4, "B4_0_8", "NONE", "INSPECTION", "_MEAN_OCCURRENCES"),
                                  Result(4, "C2_0_5", "NONE", "DEGRADED", "_MEAN_OCCURRENCES"),
                                  Result(4, "D_0_1", "NONE", "DEGRADED", "_MEAN_OCCURRENCES")
                                  ]
    scenario_2_basic_inspection_before_failure = \
        ["./availsim4core/test/E2E/input/inspection/simulation.xlsx",
         "./availsim4core/test/E2E/input/inspection/basic_inspection_before_failure_system.xlsx",
         None,
         1,
         expected_result_scenario_2]

    expected_result_scenario_3 = [Result(2, "A2_0_11", "NONE", "INSPECTION", "_MEAN_OCCURRENCES"),
                                  Result(2, "B4_0_8", "NONE", "INSPECTION", "_MEAN_OCCURRENCES"),
                                  Result(2, "C2_0_5", "NONE", "DEGRADED", "_MEAN_OCCURRENCES"),
                                  Result(2, "D_0_1", "NONE", "DEGRADED", "_MEAN_OCCURRENCES")
                                  ]

    scenario_3_basic_inspection_after_failure = \
        ["./availsim4core/test/E2E/input/inspection/simulation.xlsx",
         "./availsim4core/test/E2E/input/inspection/basic_inspection_after_failure_system.xlsx",
         None,
         1,
         expected_result_scenario_3]

    param_scenario = [
        scenario_1_basic_inspection_no_failure,
        scenario_2_basic_inspection_before_failure,
        scenario_3_basic_inspection_after_failure
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
        output_folder = "./availsim4core/test/E2E/output/inspection/"

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
