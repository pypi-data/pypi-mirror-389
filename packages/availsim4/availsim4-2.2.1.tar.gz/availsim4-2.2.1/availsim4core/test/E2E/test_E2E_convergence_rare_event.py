# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import glob
import os
import shutil
import unittest

from availsim4core import main
from availsim4core.test.E2E.E2E_utils import Result


class test_convergence_rare_event(unittest.TestCase):
    """
    class used to recover analytical results: the probability of failure of simple systems after a given time,
    following an exponential distribution law of failure.
    For the system with 2oo4 logic and a mttf of 15 and a duration of simulation of 1, the result is 0.0010211...
    For the system with 3oo4 logic and a mttf of 5 and a duration of simulation of 1, the result is 0.0010797...
    """


    scenario_2oo4_MC = [
        "./availsim4core/test/E2E/input/convergence_rare_event/10_000_MC_simulation.xlsx",
        "./availsim4core/test/E2E/input/convergence_rare_event/2oo4_system.xlsx",
        "",
        1,
        [
            Result(0.00102, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", tolerance=3)
        ]
    ]

    scenario_2oo4_QMC = [
        "./availsim4core/test/E2E/input/convergence_rare_event/10_000_QMC_simulation.xlsx",
        "./availsim4core/test/E2E/input/convergence_rare_event/2oo4_system.xlsx",
        "",
        1,
        [
            Result(0.0009, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", tolerance=3)
        ]
    ]

    scenario_2oo4_restart = [
        "./availsim4core/test/E2E/input/convergence_rare_event/2oo4_restart_simulation.xlsx",
        "./availsim4core/test/E2E/input/convergence_rare_event/2oo4_system.xlsx",
        "",
        1,
        [
            Result(0.00092, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", tolerance=3)
        ]
    ]

    scenario_3oo4_MC = [
        "./availsim4core/test/E2E/input/convergence_rare_event/10_000_MC_simulation.xlsx",
        "./availsim4core/test/E2E/input/convergence_rare_event/3oo4_system.xlsx",
        "",
        1,
        [
            Result(0.0008, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", tolerance=3)
        ]
    ]

    scenario_3oo4_QMC = [
        "./availsim4core/test/E2E/input/convergence_rare_event/10_000_QMC_simulation.xlsx",
        "./availsim4core/test/E2E/input/convergence_rare_event/3oo4_system.xlsx",
        "",
        1,
        [
            Result(0.0009, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", tolerance=3)
        ]
    ]

    scenario_3oo4_restart = [
        "./availsim4core/test/E2E/input/convergence_rare_event/3oo4_restart_simulation.xlsx",
        "./availsim4core/test/E2E/input/convergence_rare_event/3oo4_system.xlsx",
        "",
        1,
        [
            Result(0.00073, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", tolerance=3)
        ]
    ]

    param_scenario = [
        scenario_2oo4_MC,
        # scenario_2oo4_QMC,
        # scenario_2oo4_restart,
        scenario_3oo4_MC,
        # scenario_3oo4_QMC,
        # scenario_3oo4_restart,
    ]

    def test_runner(self):
        # randomize the order of the test execution to detect hidden dependencies
        # random.shuffle(self.param_scenario)
        for simulation_file, system_file, sensitivity_file, expected_number_file_result, expected_mean_result in self.param_scenario:
            with self.subTest():
                self._runner_E2E(simulation_file, system_file, sensitivity_file, expected_number_file_result,
                                 expected_mean_result)

    def _runner_E2E(self, simulation_file, system_file, sensitivity_file, expected_number_file_result,
                    expected_result_list):

        output_folder = "./availsim4core/test/E2E/output/convergence_rare_event/"

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
