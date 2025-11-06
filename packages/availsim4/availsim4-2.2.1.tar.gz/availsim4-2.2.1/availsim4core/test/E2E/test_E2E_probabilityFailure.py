# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import glob
import os
import shutil
import unittest

from availsim4core import main
from availsim4core.test.E2E.E2E_utils import Result


class test_probabilityFailure(unittest.TestCase):
    """
    class used to recover analytical results: the probability of failure of simple systems after a given time,
    following an exponential distribution law of failure.
    """

    expected_result_scenario_1 = [
        Result(0.62, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", tolerance=3)
    ]
    scenario_1_without_sensitivity_analysis_1000simulations = \
        ["./availsim4core/test/E2E/input/convergence/N1000_simulation.xlsx",
         "./availsim4core/test/E2E/input/convergence/convergence_test_system.xlsx",
         None,
         1,
         expected_result_scenario_1]

    # the theoretical values for the following test are (1 - exp(-1/MTTF))**N
    #  0 :  0.6321205588285577
    #  1 :  0.3934693402873666
    #  2 :  0.8646647167633873
    #  3 :  0.8646647167633873
    #  4 :  0.6321205588285577
    #  5 :  0.9816843611112658
    #  6 :  0.950212931632136
    #  7 :  0.7768698398515702
    #  8 :  0.9975212478233336
    #  9 :  0.9816843611112658
    #  10 :  0.8646647167633873
    #  11 :  0.9996645373720975
    #  12 :  0.9932620530009145
    #  13 :  0.9179150013761012
    #  14 :  0.9999546000702375

    # results are hardcoded based on a 1000 simulation run.
    expected_result_scenario_2 = [
        Result(0.62, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=0, tolerance=2),
        Result(0.396, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=1, tolerance=2),
        Result(0.852, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=2, tolerance=2),
        Result(0.870, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=3, tolerance=2),
        Result(0.644, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=4, tolerance=2),
        Result(0.981, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=5, tolerance=2),
        Result(0.943, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=6, tolerance=2),
        Result(0.767, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=7, tolerance=2),
        Result(0.996, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=8, tolerance=2),
        Result(0.981, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=9, tolerance=2),
        Result(0.855, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=10, tolerance=2),
        Result(0.999, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=11, tolerance=2),
        Result(0.993, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=12, tolerance=2),
        Result(0.923, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=13, tolerance=2),
        Result(0.999, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=14, tolerance=2),
    ]
    scenario_2_with_sensitivity_analysis_1000simulations = \
        ["./availsim4core/test/E2E/input/convergence/N1000_simulation.xlsx",
         "./availsim4core/test/E2E/input/convergence/convergence_test_system.xlsx",
         "./availsim4core/test/E2E/input/convergence/convergence_test_sensitivityAnalysis.xlsx",
         15, expected_result_scenario_2]

    # results are hardcoded based on a 10000 simulations run.

    expected_result_scenario_3 = [
        Result(0.6261, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=0, tolerance=3),
        Result(0.3896, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=1, tolerance=3),
        Result(0.8650, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=2, tolerance=3),
        Result(0.8629, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=3, tolerance=3),
        Result(0.6284, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=4, tolerance=3),
        Result(0.9818, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=5, tolerance=3),
        Result(0.9489, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=6, tolerance=3),
        Result(0.7771, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=7, tolerance=3),
        Result(0.9967, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=8, tolerance=3),
        Result(0.9816, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=9, tolerance=3),
        Result(0.8658, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=10, tolerance=3),
        Result(0.9995, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=11, tolerance=3),
        Result(0.9930, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=12, tolerance=3),
        Result(0.9158, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=13, tolerance=3),
        Result(0.9999, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=14, tolerance=3),
    ]
    scenario_3_with_sensitivity_analysis_10000simulations = \
        ["./availsim4core/test/E2E/input/convergence/N10000_simulation.xlsx",
         "./availsim4core/test/E2E/input/convergence/convergence_test_system.xlsx",
         "./availsim4core/test/E2E/input/convergence/convergence_test_sensitivityAnalysis.xlsx",
         15, expected_result_scenario_3]

    # results are hardcoded based on a 100000 simulation run.
    expected_result_scenario_4 = [
        Result(0.63013, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=0, tolerance=5),
        Result(0.39196, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=1, tolerance=5),
        Result(0.86527, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=2, tolerance=5),
        Result(0.86316, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=3, tolerance=5),
        Result(0.63064, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=4, tolerance=5),
        Result(0.98191, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=5, tolerance=5),
        Result(0.95039, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=6, tolerance=5),
        Result(0.77644, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=7, tolerance=5),
        Result(0.99728, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=8, tolerance=5),
        Result(0.98176, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=9, tolerance=5),
        Result(0.86445, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=10, tolerance=5),
        Result(0.99963, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=11, tolerance=5),
        Result(0.99335, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=12, tolerance=5),
        Result(0.91651, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=13, tolerance=5),
        Result(0.99995, "DUMB_0_1", "NONE", "BLIND_FAILED", "_MEAN_OCCURRENCES", file_number=14, tolerance=5),
    ]
    scenario_4_with_sensitivity_analysis_100000simulations = \
        ["./availsim4core/test/E2E/input/convergence/N100000_simulation.xlsx",
         "./availsim4core/test/E2E/input/convergence/convergence_test_system.xlsx",
         "./availsim4core/test/E2E/input/convergence/convergence_test_sensitivityAnalysis.xlsx",
         15, expected_result_scenario_4]

    param_scenario = [
        scenario_1_without_sensitivity_analysis_1000simulations,
        scenario_2_with_sensitivity_analysis_1000simulations,
        # scenario_3_with_sensitivity_analysis_10000simulations,
        # scenario_4_with_sensitivity_analysis_100000simulations
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

        output_folder = "./availsim4core/test/E2E/output/convergence/"

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
