# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import os
import random
import shutil
import time
import unittest

import pandas
from memory_profiler import memory_usage

from availsim4core import main


class test_Benchmark(unittest.TestCase):
    """
    Ensemble of tests used to monitored the computation time of the code
    Unfortunately the CI of git.cern.ch is not always using the same hardware to compute the simulations so a large
    margin is used...
    """

    #  set 1st (0: x) value to limit the time in seconds
    #  set 2nd (1: x) value to limit the memory usage in MiB

    expected_result_scenario_0 = {0: 30,  # on CI it is slower ...
                                  1: 200}
    scenario_0_BM11 = \
        ["./availsim4core/test/E2E/input/benchmark/BM_simulation.xlsx",
         "./availsim4core/test/E2E/input/benchmark/BM11_system.xlsx",
         None,
         1,
         expected_result_scenario_0]

    expected_result_scenario_1 = {0: 50,
                                  1: 200}
    scenario_1_BM100 = \
        ["./availsim4core/test/E2E/input/benchmark/BM_simulation_3.xlsx",
         "./availsim4core/test/E2E/input/benchmark/BM100_system.xlsx",
         None,
         1,
         expected_result_scenario_1]

    param_scenario = [
        scenario_0_BM11,
        scenario_1_BM100
    ]

    def test_runner(self):
        # randomize the order of the test execution to detect hidden dependencies
        random.shuffle(self.param_scenario)
        for simulation_file, system_file, sensitivity_file, expected_number_file_result, expected_mean_result in self.param_scenario:
            with self.subTest():
                self._runner_E2E(simulation_file,
                                 system_file,
                                 sensitivity_file,
                                 expected_number_file_result,
                                 expected_mean_result)

    def _runner_E2E(self, simulation_file, system_file, sensitivity_file, expected_number_file_result,
                    expected_mean_result):

        output_folder = "./availsim4core/test/E2E/output/benchmark/"

        # Clean folder
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)

        # Run the main process
        start_time = time.time()
        main.start(simulation_file, system_file, output_folder, sensitivity_file)
        execution_time = time.time() - start_time
        print(f"bench Execution time = {execution_time}")
        mem_usage = memory_usage(-1, 1, 1)
        memo_element = mem_usage[0]
        profiling = {"execution_time [s]": {0: execution_time},
                     "memory_usage [MiB]": {0: memo_element}}
        profiling_dataframe = pandas.DataFrame(profiling)
        self.assertLessEqual(profiling_dataframe["execution_time [s]"][0], expected_mean_result[0])
        self.assertLessEqual(profiling_dataframe["memory_usage [MiB]"][0], expected_mean_result[1])


if __name__ == '__main__':
    unittest.main()
