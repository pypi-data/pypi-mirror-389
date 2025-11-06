# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import glob
import os
import random
import shutil
import unittest

from availsim4core import main
from availsim4core.test.E2E.E2E_utils import Result


class test_E2E_failure_on_demand(unittest.TestCase):
    """
    Failure modes are generally defined using MTTF and a specific distribution function (normal, exponential, Weibull)
    deciding time in the simulation when a failure occurs. Failure on demand is a special way in which failure modes
    operate - it occurs at a certain time decided with with a predefined probability. In this framework, it is simulated by failure modes with the `binomial`
    probability distribution. They have a possiblity of occurring at the beginning of each phase for which they are defined.

    For instance:
    Component A has a failure mode, which is decided by a binomial distribution with parameter 0.5. The applicable
    phase is only RAMP-DOWN.
    This means that each time the simulations enters the RAMP-DOWN phase, the failure of component A will be decided by
    drawing
    """

    ###
    expected_result_scenario_1 = [
        Result(11, "A_0_2", "FIRST_PHASE", "FAILED", "_MEAN_OCCURRENCES", tolerance=6),
        Result(11, "A_0_2", "SECOND_PHASE", "FAILED", "_MEAN_OCCURRENCES", tolerance=6),
        Result(11, "A_0_2", "SECOND_PHASE", "UNDER_REPAIR", "_MEAN_OCCURRENCES", tolerance=6),
    ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2"]:
        expected_result_scenario_1.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_1 = \
        ["./availsim4core/test/E2E/input/failure_on_demand/simulation.xlsx",
         "./availsim4core/test/E2E/input/failure_on_demand/pofod_first_phase__system.xlsx",
         None,
         1,
         expected_result_scenario_1]

    ###
    expected_result_scenario_2 = [
        Result(10, "A_0_2", "SECOND_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(10, "A_0_2", "FIRST_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(10, "A_0_2", "FIRST_PHASE", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
    ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2"]:
        expected_result_scenario_2.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_2 = \
        ["./availsim4core/test/E2E/input/failure_on_demand/simulation.xlsx",
         "./availsim4core/test/E2E/input/failure_on_demand/pofod_second_phase__system.xlsx",
         None,
         1,
         expected_result_scenario_2]

    ###
    # This test does not feature any phase names in the Failure Mode sheet. The behaviour in this respect has been
    # changed in 2.1 version: NONE or other default keywords cause AvailSim4 to use a default value - which, for this
    # column, is decided to be all phases defined in the system.
    expected_result_scenario_3 = [
        Result(101, "A_0_2", "FIRST_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(101, "A_0_2", "SECOND_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(51, "A_0_2", "SECOND_PHASE", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
    ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2"]:
        expected_result_scenario_3.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_3 = \
        ["./availsim4core/test/E2E/input/failure_on_demand/simulation.xlsx",
         "./availsim4core/test/E2E/input/failure_on_demand/pofod_no_phase__system.xlsx",
         None,
         1,
         expected_result_scenario_3]

    ###
    expected_result_scenario_4 = [
        Result(0, "A_0_2", "FIRST_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(0, "A_0_2", "SECOND_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(0, "A_0_2", "SECOND_PHASE", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
    ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2"]:
        expected_result_scenario_4.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_4 = \
        ["./availsim4core/test/E2E/input/failure_on_demand/simulation.xlsx",
         "./availsim4core/test/E2E/input/failure_on_demand/pofod_first_phase_no_failure__system.xlsx",
         None,
         1,
         expected_result_scenario_4]

    ###
    expected_result_scenario_5 = [
        Result(0, "A_0_2", "SECOND_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(0, "A_0_2", "FIRST_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(0, "A_0_2", "FIRST_PHASE", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
    ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2"]:
        expected_result_scenario_5.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_5 = \
        ["./availsim4core/test/E2E/input/failure_on_demand/simulation.xlsx",
         "./availsim4core/test/E2E/input/failure_on_demand/pofod_second_phase_no_failure__system.xlsx",
         None,
         1,
         expected_result_scenario_5]

    ###
    expected_result_scenario_6 = [
        Result(0, "A_0_2", "FIRST_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(0, "A_0_2", "SECOND_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(0, "A_0_2", "SECOND_PHASE", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
    ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2"]:
        expected_result_scenario_6.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_6 = \
        ["./availsim4core/test/E2E/input/failure_on_demand/simulation.xlsx",
         "./availsim4core/test/E2E/input/failure_on_demand/pofod_no_phase_no_failure__system.xlsx",
         None,
         1,
         expected_result_scenario_6]

    ###
    expected_result_scenario_7 = [
        Result(321, "A_0_2", "FIRST_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(321, "A_0_2", "SECOND_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(321, "A_0_2", "SECOND_PHASE", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
    ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2"]:
        expected_result_scenario_7.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_7 = \
        ["./availsim4core/test/E2E/input/failure_on_demand/simulation.xlsx",
         "./availsim4core/test/E2E/input/failure_on_demand/pofod_first_phase_some_failures__system.xlsx",
         None,
         1,
         expected_result_scenario_7]

    ###
    expected_result_scenario_8 = [
        Result(320, "A_0_2", "SECOND_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(320, "A_0_2", "FIRST_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(320, "A_0_2", "FIRST_PHASE", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
    ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2"]:
        expected_result_scenario_8.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_8 = \
        ["./availsim4core/test/E2E/input/failure_on_demand/simulation.xlsx",
         "./availsim4core/test/E2E/input/failure_on_demand/pofod_second_phase_some_failures__system.xlsx",
         None,
         1,
         expected_result_scenario_8]

    ###
    expected_result_scenario_9 = [
        Result(8, "A_0_2", "FIRST_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(8, "A_0_2", "SECOND_PHASE", "FAILED", "_MEAN_OCCURRENCES"),
        Result(4, "A_0_2", "SECOND_PHASE", "UNDER_REPAIR", "_MEAN_OCCURRENCES")
    ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2"]:
        expected_result_scenario_9.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_9 = \
        ["./availsim4core/test/E2E/input/failure_on_demand/simulation.xlsx",
         "./availsim4core/test/E2E/input/failure_on_demand/pofod_no_phase_some_failures__system.xlsx",
         None,
         1,
         expected_result_scenario_9]

    ###
    expected_result_scenario_10 = [
        Result(122, "MAIN_0_2", "OPERATION", "FAILED", "_MEAN_OCCURRENCES"),
        Result(122, "MAIN_0_2", "DEGRADED", "FAILED", "_MEAN_OCCURRENCES"),
        Result(122, "MAIN_0_2", "DEGRADED", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
        Result(58, "MAIN_0_2", "OPERATION", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
        Result(64, "MAIN_0_2", "SHUTDOWN", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
        Result(122, "KICK_0_3", "DEGRADED", "RUNNING", "_MEAN_OCCURRENCES"),
        Result(64, "KICK_0_3", "DEGRADED", "FAILED", "_MEAN_OCCURRENCES"),
        Result(64, "KICK_0_3", "SHUTDOWN", "FAILED", "_MEAN_OCCURRENCES"),
        Result(64, "KICK_0_3", "SHUTDOWN", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
    ]
    for component_name in ["Phase", "ROOT_0_1", "MAIN_0_2", "KICK_0_3"]:
        expected_result_scenario_10.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
    scenario_10 = \
        ["./availsim4core/test/E2E/input/failure_on_demand/simulation.xlsx",
         "./availsim4core/test/E2E/input/failure_on_demand/pofod_second_basic_in_other_phase__system.xlsx",
         None,
         1,
         expected_result_scenario_10]


    param_scenario = [
        # scenario_1,
        # scenario_2,
        # scenario_3,
        # scenario_4,
        # scenario_5,
        # scenario_6,
        # scenario_7,
        # scenario_8,
        scenario_9
        # scenario_10
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

        output_folder = "./availsim4core/test/E2E/output/failure_on_demand/"

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
