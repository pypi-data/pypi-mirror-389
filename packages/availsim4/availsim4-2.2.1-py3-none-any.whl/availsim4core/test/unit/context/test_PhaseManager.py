# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.probability_law.deterministic_law import DeterministicLaw
from availsim4core.src.timeline.record_phase import RecordPhase


class test_PhaseManager(unittest.TestCase):

    def test__get_first_phase(self):
        phase_first = Phase("phase_test", DeterministicLaw(10), True)
        phase_second = Phase("phase_test", DeterministicLaw(10), False)
        phase_first.set_next_phase(phase_second)
        phase_second.set_next_phase(phase_first)
        phase_set = {phase_first, phase_second}

        phase_manager = PhaseManager(phase_set, set())
        result = phase_manager._get_first_phase()

        expected_result = phase_first
        self.assertEqual(expected_result, result)

    def test__get_first_phase__none_phase(self):
        phase_set = set()

        phase_manager = PhaseManager(phase_set, set())
        result = phase_manager._get_first_phase()

        expected_result = PhaseManager.NO_PHASE

        self.assertEqual(expected_result, result)

    def test_find_phase(self):
        phase_first = Phase("phase_test_first", DeterministicLaw(10), True)
        phase_second = Phase("phase_test_second", DeterministicLaw(10), False)
        phase_first.set_next_phase(phase_second)
        phase_second.set_next_phase(phase_first)
        phase_set = {phase_first, phase_second}

        phase_manager = PhaseManager(phase_set, set())
        result = phase_manager._find_phase("phase_test_first")
        expected_result = phase_first

        self.assertEqual(result, expected_result)

    def test_find_phase_no_phase(self):
        phase_set = set()
        phase_manager = PhaseManager(phase_set, set())

        result = phase_manager._find_phase("not_found_phase")
        expected_result = phase_manager.NO_PHASE

        self.assertEqual(expected_result, result)

    def test_set_next_default_phase__get_first(self):
        phase_first = Phase("phase_test_first", DeterministicLaw(10), True)
        phase_second = Phase("phase_test_second", DeterministicLaw(10), False)
        phase_first.set_next_phase(phase_second)
        phase_second.set_next_phase(phase_first)
        phase_set = {phase_first, phase_second}

        phase_manager = PhaseManager(phase_set, set())

        expected_result_current_phase = phase_first

        self.assertEqual(expected_result_current_phase, phase_manager.current_phase)

    def test_set_next_default_phase__get_second_phase(self):
        phase_first = Phase("phase_test_first", DeterministicLaw(10), True)
        phase_second = Phase("phase_test_second", DeterministicLaw(10), False)
        phase_first.set_next_phase(phase_second)
        phase_second.set_next_phase(phase_first)
        phase_set = {phase_first, phase_second}

        phase_manager = PhaseManager(phase_set, set())

        result = phase_manager.go_to_phase(0,phase_manager.current_phase.next,PhaseManager.DEFAULT_PHASE_DESCRIPTION)

        expected_result = phase_second

        expected_result_phase_record = RecordPhase(phase_second,
                                                   0,
                                                   PhaseManager.DEFAULT_PHASE_DESCRIPTION)

        self.assertEqual(expected_result, phase_manager.current_phase)
        self.assertEqual(expected_result_phase_record, result)

    def test_set_next_default_phase_if_failure(self):
        phase_first = Phase("phase_test_first", DeterministicLaw(10), True)
        phase_second = Phase("phase_test_second", DeterministicLaw(10), False)
        phase_first.set_next_phase(PhaseManager.NO_PHASE)
        phase_second.set_next_phase(PhaseManager.NO_PHASE)
        phase_first.set_next_phase_if_failure(phase_second)
        phase_second.set_next_phase_if_failure(phase_first)
        phase_set = {phase_first, phase_second}

        phase_manager = PhaseManager(phase_set, set())
        result = phase_manager.go_to_phase(0,
                                           phase_second,
                                           PhaseManager.DEFAULT_PHASE_IF_FAILURE_DESCRIPTION)

        expected_result = phase_second

        expected_result_phase_record = RecordPhase(phase_second,
                                                   0,
                                                   PhaseManager.DEFAULT_PHASE_IF_FAILURE_DESCRIPTION)

        self.assertEqual(expected_result, phase_manager.current_phase)
        self.assertEqual(expected_result_phase_record, result)


if __name__ == '__main__':
    unittest.main()
