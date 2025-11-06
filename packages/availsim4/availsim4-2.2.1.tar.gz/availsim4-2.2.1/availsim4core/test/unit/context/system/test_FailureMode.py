# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.failure import FailureType, Failure
from availsim4core.src.context.system.failure_mode import FailureMode, FailureModeError
from availsim4core.src.context.system.inspection import Inspection
from availsim4core.src.context.system.probability_law.deterministic_law import DeterministicLaw
from availsim4core.src.context.system.probability_law.exponential_law import ExponentialLaw
from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw


class test_FailureFactory(unittest.TestCase):

    def setUp(self) -> None:
        self.failure_mode_name = "TEST_FAILURE"
        self.failure_distribution_name = "EXP"
        self.failure_distribution_params = [10.0]
        self.repair_distribution_name = "FIX"
        self.repair_distribution_params = [20.0]
        self.failure_type_name = "BLIND"
        self.held_before_repair_in_phases = []
        self.inspection_name = "INSPECTION1"
        self.phases_names = ["OPERATION", "FAULT"]
        self.held_after_repair_in_phases = ["HELD_FOREVER"]
        self.phase_change_trigger = ""
        self.next_phase_name_if_failure = ""
        self.comments = "Test comment"

        self.global_phase_list = [Phase("OPERATION", ProbabilityLaw("fix", 10, False), True, "Phase comment"),
                             Phase("FAULT", ProbabilityLaw("fix", 15, False), True, "Phase comment")]
        self.global_inspection_list = [Inspection("INSPECTION1", 100, 10, "Inspection comment")]

    def test_failure_mode_exception(self):
        """
        This test check that AvailSim4 will detect the combination of type_of_failure = "BLIND" and
        phase_change_timing = "AFTER_REPAIR"
        """
        with self.assertRaises(FailureModeError) as context:

            NO_PHASE = PhaseManager.NO_PHASE

            expected_inspection = Inspection("inspection_test", 1, 2)

            FailureMode("TEST_FAILURE",
                        ProbabilityLaw("", 0, False),
                        ProbabilityLaw("", 0, False),
                        Failure(FailureType.BLIND),
                        "[]",
                        expected_inspection,
                        [],
                        NO_PHASE,
                        'AFTER_REPAIR',
                        []
                    )

        self.assertTrue("Wrong combination of type_of_failure" in str(context.exception))

    def test_build_with_defaults(self):
        """
        This test checks whether the FailureMode built using the method `.build()` with acceptable and simple parameters
        results in a correctly-initialized object.
        """
        failure_mode = FailureMode.build(self.failure_mode_name, self.failure_distribution_name,
                                         self.failure_distribution_params, self.repair_distribution_name,
                                         self.repair_distribution_params, self.failure_type_name,
                                         [], "", [], [], "", "", "", self.global_inspection_list,
                                         self.global_phase_list)

        # Empty held_before_repair_phase_set parameter should populate the field with all phases
        self.assertEqual(failure_mode.held_before_repair_phase_set, set(self.global_phase_list))

        # Empty inspection parameter is equivalent to "None" keyword
        self.assertEqual(failure_mode.inspection, None)

        # Empty phase set should make all phases defined in the system applicable
        self.assertEqual(failure_mode.phase_set, set(self.global_phase_list))

        # Empty held_after_repair_phase_set parameter should
        self.assertEqual(failure_mode.held_after_repair_phase_set, set(self.global_phase_list))

        # Empty phase change trigger parameter
        self.assertEqual(failure_mode.phase_change_trigger, "NEVER")

    def test_build_standard(self):
        """
        This test checks if the default values are handled the way they are expected.
        """
        failure_mode = FailureMode.build(self.failure_mode_name, self.failure_distribution_name,
                                         self.failure_distribution_params, self.repair_distribution_name,
                                         self.repair_distribution_params, self.failure_type_name,
                                         self.held_before_repair_in_phases, self.inspection_name, self.phases_names,
                                         self.held_after_repair_in_phases, self.phase_change_trigger,
                                         self.next_phase_name_if_failure, self.comments, self.global_inspection_list,
                                         self.global_phase_list)

        self.assertEqual(failure_mode.name, self.failure_mode_name)
        self.assertEqual(failure_mode.failure_law, ExponentialLaw(self.failure_distribution_params))
        self.assertEqual(failure_mode.repair_law, DeterministicLaw(self.repair_distribution_params))
        self.assertEqual(failure_mode.failure, Failure(FailureType.BLIND))
        self.assertEqual(failure_mode.held_before_repair_phase_set, set(self.global_phase_list))
        self.assertEqual(failure_mode.inspection, self.global_inspection_list[0])
        self.assertEqual(failure_mode.phase_set, set(self.global_phase_list))
        self.assertEqual(failure_mode.held_after_repair_phase_set, set([PhaseManager.HELD_FOREVER]))
