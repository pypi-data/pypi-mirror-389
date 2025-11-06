# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import glob
import os
import random
import shutil
import unittest

from availsim4core import main
from availsim4core.test.E2E.E2E_utils import Result


class test_E2E_phases(unittest.TestCase):
    # no phase ==> already done by all other tests without phase
    # test with phases are for now done with AND logic only, that feature is customized for the LHC model

    ###
    # one failure occurs after a given deterministic time which is smaller than the duration of the simulation but still
    # the failure never occurs because the system does not spend enough time in that phase
    SIMULATION_FILEPATH = "./availsim4core/test/E2E/input/phases/simulation.xlsx"


    expected_result_scenario_1 = [Result(11, "A2_0_11", "A", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(0, "A2_0_11", "A", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(11, "Phase", "A", "_", "_MEAN_OCCURRENCES")]
    for component_name in ["Phase", "D_0_1", "C1_0_2", "B1_0_3", "B2_0_4", "C2_0_5", "B3_0_6", "B3_1_7", "B4_0_8",
                           "A1_0_9", "A1_1_10", "A2_0_11", "C3_0_12"]:
        expected_result_scenario_1.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_1 = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/no_sufficient_time_in_faulty_phase_system.xlsx",
         None,
         1,
         expected_result_scenario_1]

    ###
    # ten failures occur in a given phase
    expected_result_scenario_2 = [Result(10, "A2_0_11", "A", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(11, "Phase", "A", "_", "_MEAN_OCCURRENCES")]
    for component_name in ["Phase", "D_0_1", "C1_0_2", "B1_0_3", "B2_0_4", "C2_0_5", "B3_0_6", "B3_1_7", "B4_0_8",
                           "A1_0_9", "A1_1_10", "A2_0_11", "C3_0_12"]:
        expected_result_scenario_2.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_2 = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/sufficient_time_in_faulty_phase_system.xlsx",
         None,
         1,
         expected_result_scenario_2]

    ###
    # 100 failures occur in a given phase, same input as scenario_2 but when a failure occurs in phase A,
    # the system go back to phase A
    expected_result_scenario_2b = [Result(100, "A2_0_11", "A", "FAILED", "_MEAN_OCCURRENCES"),
                                   Result(101, "Phase", "A", "_", "_MEAN_OCCURRENCES")]
    for component_name in ["Phase", "D_0_1", "C1_0_2", "B1_0_3", "B2_0_4", "C2_0_5", "B3_0_6", "B3_1_7", "B4_0_8",
                           "A1_0_9", "A1_1_10", "A2_0_11", "C3_0_12"]:
        expected_result_scenario_2b.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_2b = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/sufficient_time_in_faulty_phase_v2_system.xlsx",
         None,
         1,
         expected_result_scenario_2b]

    ###
    # the system is never passing in the phase where a failure could occur
    expected_result_scenario_3 = [Result(11, "A2_0_11", "B", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(0, "Phase", "A", "_", "_MEAN_OCCURRENCES"),
                                  Result(11, "Phase", "B", "_", "_MEAN_OCCURRENCES")]
    for component_name in ["Phase", "D_0_1", "C1_0_2", "B1_0_3", "B2_0_4", "C2_0_5", "B3_0_6", "B3_1_7", "B4_0_8",
                           "A1_0_9", "A1_1_10", "A2_0_11", "C3_0_12"]:
        expected_result_scenario_3.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_3 = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/never_passing_in_faulty_phase_system.xlsx",
         None,
         1,
         expected_result_scenario_3]

    ###
    # system is passing only once in the phase where a failure occurs
    expected_result_scenario_4 = [Result(1, "A2_0_11", "A", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(1, "Phase", "A", "_", "_MEAN_OCCURRENCES")]
    for component_name in ["Phase", "D_0_1", "C1_0_2", "B1_0_3", "B2_0_4", "C2_0_5", "B3_0_6", "B3_1_7", "B4_0_8",
                           "A1_0_9", "A1_1_10", "A2_0_11", "C3_0_12"]:
        expected_result_scenario_4.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_4 = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/passing_once_in_faulty_phase_system.xlsx",
         None,
         1,
         expected_result_scenario_4]

    ###
    # no phase, 50 failures
    expected_result_scenario_5 = [Result(50, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(50, "B_0_11", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(50, "ROOT_0_1", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(50, "B_0_11", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(51, "ROOT_0_1", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(51, "B_0_11", "*", "RUNNING", "_MEAN_OCCURRENCES")
                                  ]

    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9",
                           "E_0_10","B_0_11", "C_0_12"]:
        expected_result_scenario_5.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))

    for component_name in ["A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8","D_0_9",
                               "E_0_10", "C_0_12"]:
        expected_result_scenario_5.append(Result(1, component_name, "*", "RUNNING", "_MEAN_OCCURRENCES"))

    scenario_5 = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version1_no_phase_system.xlsx",
         None,
         1,
         expected_result_scenario_5]

    ###
    # scenario using phases but the unique failure is present in each phase, should be equivalent to scenario 5
    expected_result_scenario_6 = [Result(50, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(50, "B_0_11", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(50, "ROOT_0_1", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(50, "B_0_11", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  #Result(126, "ROOT_0_1", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  #Result(126, "B_0_11", "*", "RUNNING", "_MEAN_OCCURRENCES")
                                  ]
    # 126 instead of 51 like in scenario 5 because of the many times the system enters new phases
    # the 126 is not deterministic TODO: DETERMINISTIC CHECK
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9",
                           "E_0_10","B_0_11", "C_0_12"]:
        expected_result_scenario_6.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    #for component_name in ["A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8","D_0_9",
    #                           "E_0_10", "C_0_12"]:
    #    expected_result_scenario_6.append(Result(100, component_name, "*", "RUNNING", "_MEAN_OCCURRENCES"))
    # TODO: DETERMINISTIC CHECK

    scenario_6 = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version2_failure_in_each_phase_system.xlsx",
         None,
         1,
         expected_result_scenario_6]

    ###
    # scenario using phases but the unique failure is present in each phase, should be equivalent to scenario 5 and 6
    # but with a different transition of phase when a failure occurs
    expected_result_scenario_6b = [Result(50, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(50, "B_0_11", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(50, "ROOT_0_1", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(50, "B_0_11", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  # Result(126, "ROOT_0_1", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  # Result(126, "B_0_11", "*", "RUNNING", "_MEAN_OCCURRENCES")
                                  ]
    # 126 instead of 51 like in scenario 5 because of the many times the system enters new phases
    # also, 126 is not deterministic TODO: DETERMINISTIC CHECK
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9",
                           "E_0_10", "B_0_11", "C_0_12"]:
        expected_result_scenario_6b.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    #for component_name in ["A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8","D_0_9",
    #                           "E_0_10", "C_0_12"]:
    #    expected_result_scenario_6.append(Result(100, component_name, "*", "RUNNING", "_MEAN_OCCURRENCES"))
    # TODO: DETERMINISTIC CHECK
    scenario_6b = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version2_failure_in_each_phase_v2_system.xlsx",
         None,
         1,
         expected_result_scenario_6b]

    ###
    # scenario using phases but the unique failure is present in each phase, should be equivalent to scenario 5 and 6 and 6b
    # but with a different transition of phase when a failure occurs
    expected_result_scenario_6c = [Result(50, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(50, "B_0_11", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(50, "ROOT_0_1", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(50, "B_0_11", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  # Result(126, "ROOT_0_1", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  # Result(126, "B_0_11", "*", "RUNNING", "_MEAN_OCCURRENCES")
                                  ]
    # 126 instead of 51 like in scenario 5 because of the many times the system enters new phases
    # also, 126 is not deterministic TODO: DETERMINISTIC CHECK
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9",
                           "E_0_10", "B_0_11", "C_0_12"]:
        expected_result_scenario_6c.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    #for component_name in ["A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8","D_0_9",
    #                           "E_0_10", "C_0_12"]:
    #    expected_result_scenario_6c.append(Result(100, component_name, "*", "RUNNING", "_MEAN_OCCURRENCES"))
    # TODO: DETERMINISTIC CHECK
    scenario_6c = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version2_failure_in_each_phase_v3_system.xlsx",
         None,
         1,
         expected_result_scenario_6c]

    ###
    # scenario using phases but the unique failure is present in each phase using 2 different failure modes in 2 different basics,
    # should be equivalent to scenario 5
    expected_result_scenario_7 = [Result(50, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(26, "BFM12_0_11", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(24, "BFM34_0_12", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(50, "ROOT_0_1", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(26, "BFM12_0_11", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(24, "BFM34_0_12", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES")]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9",
                           "E_0_10", "BFM12_0_11", "BFM34_0_12", "C_0_13"]:
        expected_result_scenario_7.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_7 = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version3_failure_in_each_phase_2_failure_modes_system.xlsx",
         None,
         1,
         expected_result_scenario_7]

    ###
    # scenario using phases but the unique failure is present in each phase using 2 different failure mode, should be equivalent to scenario 5
    # and scenario 7 but with a different transition scheme when a fault occurs
    expected_result_scenario_7b = [Result(50, "ROOT_0_1", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                   Result(25, "BFM12_0_11", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                   Result(25, "BFM34_0_12", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(50, "ROOT_0_1", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(25, "BFM12_0_11", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(25, "BFM34_0_12", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES")]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9",
                           "E_0_10", "BFM12_0_11", "BFM34_0_12", "C_0_13"]:
        expected_result_scenario_7b.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_7b = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version3_failure_in_each_phase_2_failure_modes_v2_system.xlsx",
         None,
         1,
         expected_result_scenario_7b]

    # TODO: in scenario_7 and scenario_7b, the durations of the phase are multiples of the timetofail+timetorepair
    # to avoid any complication, it should be changed for the test to be even more general

    ###
    expected_result_scenario_8 = [Result(3, "B_0_11", "*", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(1, "Phase", "P1", "_", "_MEAN_OCCURRENCES"),
                                  Result(2, "Phase", "P2", "_", "_MEAN_OCCURRENCES"),
                                  Result(2, "Phase", "P3", "_", "_MEAN_OCCURRENCES")]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9",
                           "E_0_10",
                           "B_0_11", "C_0_12"]:
        expected_result_scenario_8.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    scenario_8 = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/failure_in_each_Phase_but_change_phase_before_failure_system.xlsx",
         None,
         1,
         expected_result_scenario_8]

    ###
    # the system never fails but is passing in different phases
    expected_result_scenario_9 = [Result(15, "Phase", "P1", "*", "_MEAN_OCCURRENCES"),
                                  Result(15, "Phase", "P2", "*", "_MEAN_OCCURRENCES"),
                                  Result(14, "Phase", "P3", "*", "_MEAN_OCCURRENCES"),
                                  Result(14, "Phase", "P4", "*", "_MEAN_OCCURRENCES")]
    for component_name in ["Phase",
                           "ROOT_0_1", "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9", "E_0_10",
                           "B_0_11", "C_0_12"]:
        expected_result_scenario_9.append(Result(100, component_name, "*", "*", "_MEAN_DURATION", tolerance=6))
        dict_of_phase_duration = {
            "P1": 15,
            "P2": 28.86,
            "P3": 56,
            "P4": 0.14
        }
        for phase, value in dict_of_phase_duration.items():
            expected_result_scenario_9.append(Result(value, component_name, phase, "*", "_MEAN_DURATION", tolerance=6))
    scenario_9 = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version4_phases_but_no_failures_system.xlsx",
         None,
         1,
         expected_result_scenario_9]

    ###
    # a failure force the system into a specific phase
    expected_result_scenario_10 = [
        Result(10, "Phase", "P1", "*", "_MEAN_OCCURRENCES"),
        Result(10, "Phase", "P2", "*", "_MEAN_OCCURRENCES"),
        Result(10, "Phase", "P3", "*", "_MEAN_OCCURRENCES"),
        Result(6, "Phase", "P4", "*", "_MEAN_OCCURRENCES"),
        Result(3, "Phase", "CYCLING", "*", "_MEAN_OCCURRENCES"),
        Result(10, "Phase", "P1", "*", "_MEAN_DURATION", tolerance=6),
        Result(20, "Phase", "P2", "*", "_MEAN_DURATION", tolerance=6),
        Result(39.94, "Phase", "P3", "*", "_MEAN_DURATION", tolerance=6),
        Result(0.06, "Phase", "P4", "*", "_MEAN_DURATION", tolerance=6),
        Result(30, "Phase", "CYCLING", "*", "_MEAN_DURATION", tolerance=6),
    ]
    scenario_10 = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version5_phase_specific_to_failure_mode_system.xlsx",
         None,
         1,
         expected_result_scenario_10]


    ###
    # a failure forces the system into a specific phase
    # but another fault starts before the "failure needing a specific phase"
    # and that failure is repaired before the "failure needing a specific phase"
    expected_result_scenario_10b = [
        Result(10, "Phase", "P1", "*", "_MEAN_OCCURRENCES"),
        Result(10, "Phase", "P2", "*", "_MEAN_OCCURRENCES"),
        Result(10, "Phase", "P3", "*", "_MEAN_OCCURRENCES"),
        Result(6, "Phase", "P4", "*", "_MEAN_OCCURRENCES"),
        Result(3, "Phase", "CYCLING", "*", "_MEAN_OCCURRENCES"),
        Result(10, "Phase", "P1", "*", "_MEAN_DURATION", tolerance=6),
        Result(20, "Phase", "P2", "*", "_MEAN_DURATION", tolerance=6),
        Result(39.94, "Phase", "P3", "*", "_MEAN_DURATION", tolerance=6),
        Result(0.06, "Phase", "P4", "*", "_MEAN_DURATION", tolerance=6),
        Result(30, "Phase", "CYCLING", "*", "_MEAN_DURATION", tolerance=6),
    ]
    scenario_10b = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version5_phaseSpecificToFailureMode_parallelFault1_system.xlsx",
         None,
         1,
         expected_result_scenario_10b]

    ###
    # a failure forces the system into a specific phase
    # but another fault starts before the "failure needing a specific phase"
    # and that failure is repaired after the "failure needing a specific phase"
    # (this only applies to the first occurrences of those failures, because after this occurrence
    # everything gets out of sync as ttf+ttr = 12.5 for the failure needing a specific phase while
    # it's 12.5001 for the other failure)
    expected_result_scenario_10c = [
        Result(14, "Phase", "P1", "*", "_MEAN_OCCURRENCES"),
        Result(14, "Phase", "P2", "*", "_MEAN_OCCURRENCES"),
        Result(14, "Phase", "P3", "*", "_MEAN_OCCURRENCES"),
        Result(13, "Phase", "P4", "*", "_MEAN_OCCURRENCES"),
        Result(0, "Phase", "CYCLING", "*", "_MEAN_OCCURRENCES"),
        Result(14, "Phase", "P1", "*", "_MEAN_DURATION", tolerance=6),
        Result(28, "Phase", "P2", "*", "_MEAN_DURATION", tolerance=6),
        Result(57.87, "Phase", "P3", "*", "_MEAN_DURATION", tolerance=6),
        Result(0.13, "Phase", "P4", "*", "_MEAN_DURATION", tolerance=6),
        Result(0, "Phase", "CYCLING", "*", "_MEAN_DURATION", tolerance=6),
    ]
    scenario_10c = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version5_phaseSpecificToFailureMode_parallelFault2_system.xlsx",
         None,
         1,
         expected_result_scenario_10c]

    ###
    # a failure forces the system into a specific phase
    # but another fault starts after the "failure needing a specific phase"
    # and that failure is repaired before the "failure needing a specific phase"
    expected_result_scenario_10d = [
        Result(10, "Phase", "P1", "*", "_MEAN_OCCURRENCES"),
        Result(10, "Phase", "P2", "*", "_MEAN_OCCURRENCES"),
        Result(10, "Phase", "P3", "*", "_MEAN_OCCURRENCES"),
        Result(6, "Phase", "P4", "*", "_MEAN_OCCURRENCES"),
        Result(3, "Phase", "CYCLING", "*", "_MEAN_OCCURRENCES"),
        Result(10, "Phase", "P1", "*", "_MEAN_DURATION", tolerance=6),
        Result(20, "Phase", "P2", "*", "_MEAN_DURATION", tolerance=6),
        Result(39.94, "Phase", "P3", "*", "_MEAN_DURATION", tolerance=6),
        Result(0.06, "Phase", "P4", "*", "_MEAN_DURATION", tolerance=6),
        Result(30, "Phase", "CYCLING", "*", "_MEAN_DURATION", tolerance=6),
    ]
    scenario_10d = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version5_phaseSpecificToFailureMode_parallelFault3_system.xlsx",
         None,
         1,
         expected_result_scenario_10d]

    ###
    # a failure forces the system into a specific phase
    # but another fault starts before the "failure needing a specific phase"
    # and that failure is repaired before the "failure needing a specific phase"
    expected_result_scenario_10e = [
        Result(10, "Phase", "P1", "*", "_MEAN_OCCURRENCES"),
        Result(10, "Phase", "P2", "*", "_MEAN_OCCURRENCES"),
        Result(10, "Phase", "P3", "*", "_MEAN_OCCURRENCES"),
        Result(6, "Phase", "P4", "*", "_MEAN_OCCURRENCES"),
        Result(3, "Phase", "CYCLING", "*", "_MEAN_OCCURRENCES"),
        Result(10, "Phase", "P1", "*", "_MEAN_DURATION", tolerance=6),
        Result(20, "Phase", "P2", "*", "_MEAN_DURATION", tolerance=6),
        Result(39.94, "Phase", "P3", "*", "_MEAN_DURATION", tolerance=6),
        Result(0.06, "Phase", "P4", "*", "_MEAN_DURATION", tolerance=6),
        Result(30, "Phase", "CYCLING", "*", "_MEAN_DURATION", tolerance=6),
    ]
    scenario_10e = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version5_phaseSpecificToFailureMode_parallelFault4_system.xlsx",
         None,
         1,
         expected_result_scenario_10e]

    ###
    # testing the option to change phase after a repair or after a failure
    # baseline = after a repair
    # in this simulation, the repair is too long to finish, the phase never changes
    expected_result_scenario_11a = [
        Result(1, "Phase", "P1", "*", "_MEAN_OCCURRENCES"),
        Result(0, "Phase", "P2", "*", "_MEAN_OCCURRENCES"),
        Result(100, "Phase", "P1", "*", "_MEAN_DURATION", tolerance=6),
        Result(0, "Phase", "P2", "*", "_MEAN_DURATION", tolerance=6),
    ]
    scenario_11a = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/option_on_timing__after_repair__system.xlsx",
         None,
         1,
         expected_result_scenario_11a]

    ###
    # testing the option to change phase after a repair or after a failure
    # new possibility = after a failure
    # in this simulation, the repair is too long to finish, still the phase changes after the failure
    expected_result_scenario_11b = [
        Result(1, "Phase", "P1", "*", "_MEAN_OCCURRENCES"),
        Result(1, "Phase", "P2", "*", "_MEAN_OCCURRENCES"),
        Result(50, "Phase", "P1", "*", "_MEAN_DURATION", tolerance=6),
        Result(50, "Phase", "P2", "*", "_MEAN_DURATION", tolerance=6),
    ]
    scenario_11b = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/option_on_timing__after_failure__system.xlsx",
         None,
         1,
         expected_result_scenario_11b]

    ###
    # testing the option to change phase after a repair or after a failure
    # baseline = after a repair
    # in this simulation, the repair is not too long to finish, the phase changes
    expected_result_scenario_11c = [
        Result(1, "Phase", "P1", "*", "_MEAN_OCCURRENCES"),
        Result(1, "Phase", "P2", "*", "_MEAN_OCCURRENCES"),
        Result(80, "Phase", "P1", "*", "_MEAN_DURATION", tolerance=6),
        Result(20, "Phase", "P2", "*", "_MEAN_DURATION", tolerance=6),
    ]
    scenario_11c = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/option_on_timing_v2__after_repair__system.xlsx",
         None,
         1,
         expected_result_scenario_11c]

    ###
    # testing the option to change phase after a repair or after a failure
    # new = never
    # in this simulation, the repair is not too long to finish but the phase never changes
    expected_result_scenario_11d = [
        Result(1, "Phase", "P1", "*", "_MEAN_OCCURRENCES"),
        Result(0, "Phase", "P2", "*", "_MEAN_OCCURRENCES"),
        Result(100, "Phase", "P1", "*", "_MEAN_DURATION", tolerance=6),
        Result(0, "Phase", "P2", "*", "_MEAN_DURATION", tolerance=6),
    ]
    scenario_11d = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/option_on_timing_v2__never__system.xlsx",
         None,
         1,
         expected_result_scenario_11d]

    ###
    # Test checking if postponing an event is done correctly.
    # One failure mode is define in the system, this failure mode is only valid in one of the two phases,
    # thus the failure it generates has to be postponed.
    expected_result_scenario_12_v1 = [Result(1, "ROOT_0_1", "P1", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(1, "B_0_11", "P1", "FAILED", "_MEAN_OCCURRENCES"),
                                  #Result(2, "ROOT_0_1", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"), # TODO: check deterministic
                                  #Result(2, "B_0_11", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(3, "ROOT_0_1", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(3, "B_0_11", "*", "RUNNING", "_MEAN_OCCURRENCES")
                                  ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9",
                           "E_0_10","B_0_11", "C_0_12"]:
        expected_result_scenario_12_v1.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    for component_name in ["A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8","D_0_9",
                               "E_0_10", "C_0_12"]:
        expected_result_scenario_12_v1.append(Result(3, component_name, "*", "RUNNING", "_MEAN_OCCURRENCES"))
    scenario_12_v1 = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version4_check_postpone_v1_system.xlsx",
         None,
         1,
         expected_result_scenario_12_v1]

    ###
    # Test checking if postponing an event is done correctly.
    # One failure mode is defined in the system, this failure mode is valid in both of the two phases
    expected_result_scenario_12_v2 = [Result(2, "ROOT_0_1", "P1", "FAILED", "_MEAN_OCCURRENCES"),
                                  Result(2, "B_0_11", "P1", "FAILED", "_MEAN_OCCURRENCES"),
                                  #Result(2, "ROOT_0_1", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"), # TODO: check deterministic
                                  #Result(2, "B_0_11", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                  Result(4, "ROOT_0_1", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                  Result(4, "B_0_11", "*", "RUNNING", "_MEAN_OCCURRENCES")
                                  ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9",
                           "E_0_10","B_0_11", "C_0_12"]:
        expected_result_scenario_12_v2.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    for component_name in ["A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8","D_0_9",
                               "E_0_10", "C_0_12"]:
        expected_result_scenario_12_v2.append(Result(4, component_name, "*", "RUNNING", "_MEAN_OCCURRENCES"))
    scenario_12_v2 = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version4_check_postpone_v2_system.xlsx",
         None,
         1,
         expected_result_scenario_12_v2]

    ###
    # Test checking if postponing an event is done correctly.
    # One failure mode is defined in the system, this failure mode is valid in both of the two phases
    expected_result_scenario_12_v3 = [Result(2, "ROOT_0_1", "P1", "FAILED", "_MEAN_OCCURRENCES"),
                                      Result(2, "B_0_11", "P1", "FAILED", "_MEAN_OCCURRENCES"),
                                      # Result(2, "ROOT_0_1", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"), # TODO: check deterministic
                                      # Result(2, "B_0_11", "*", "UNDER_REPAIR", "_MEAN_OCCURRENCES"),
                                      Result(4, "ROOT_0_1", "*", "RUNNING", "_MEAN_OCCURRENCES"),
                                      Result(4, "B_0_11", "*", "RUNNING", "_MEAN_OCCURRENCES")
                                      ]
    for component_name in ["Phase", "ROOT_0_1", "A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9",
                           "E_0_10", "B_0_11", "C_0_12"]:
        expected_result_scenario_12_v3.append(Result(100, component_name, "*", "*", "_MEAN_DURATION"))
    for component_name in ["A_0_2", "D_0_3", "E_0_4", "A_1_5", "D_0_6", "E_0_7", "A_2_8", "D_0_9",
                           "E_0_10", "C_0_12"]:
        expected_result_scenario_12_v3.append(Result(4, component_name, "*", "RUNNING", "_MEAN_OCCURRENCES"))
    scenario_12_v3 = \
        [SIMULATION_FILEPATH,
         "./availsim4core/test/E2E/input/phases/version4_check_postpone_v3_system.xlsx",
         None,
         1,
         expected_result_scenario_12_v3]

    param_scenario = [
        scenario_1,
        scenario_2,
        scenario_2b,
        scenario_3,
        scenario_4,
        scenario_5,
        scenario_6,
        scenario_6b,
        scenario_6c,
        scenario_7,
        scenario_7b,
        scenario_8,
        scenario_9,
        scenario_10,
        scenario_10b,
        scenario_10c,
        scenario_10d,
        scenario_10e,
        scenario_11a,
        scenario_11b,
        scenario_11c,
        scenario_11d,
        scenario_12_v1,
        scenario_12_v2,
        scenario_12_v3,
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

        output_folder = "./availsim4core/test/E2E/output/phases/"

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
