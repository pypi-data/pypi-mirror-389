# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest
from unittest.mock import patch

from availsim4core.src.context.context import Context
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.failure import FailureType, Failure
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw
from availsim4core.src.discrete_event_simulation.b_event_generator import BEventGenerator
from availsim4core.src.discrete_event_simulation.c_event_generator import CEventGenerator
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.detectable_failure_event import \
    DetectableFailureEvent
from availsim4core.src.discrete_event_simulation.event.b_event.phase_event.next_phase_event import NextPhaseEvent
from availsim4core.src.timeline.record_component import RecordComponent


class test_Basic(unittest.TestCase):

    def test__eq__(self):
        basic_1 = Basic(1, "test_compound_1", 0, [], None, [], [])
        basic_2 = Basic(1, "test_compound_1", 0, [], None, [], [])

        self.assertEqual(basic_1, basic_2)

    def test_to_set(self):
        basic = Basic(1, "dummyName", 0, None, [None, None], [], [])
        result = basic.to_set()
        self.assertEqual(result, set([basic]))

    def test_get_failure_events(self):
        # failures modes used to define a Basic
        phase_set = set()
        rca_set = set()
        first_failure_mode = FailureMode("first failure mode",
                                         ProbabilityLaw("dummy", 1.0, False),
                                         ProbabilityLaw("dummy", 2.0, False),
                                         Failure(FailureType.DETECTABLE),
                                         [],
                                         None,
                                         phase_set,
                                         None,
                                         'AFTER_REPAIR',
                                         [])

        basic = Basic(1, "dummyName", 0, [], first_failure_mode, [], [])
        context = Context(basic, PhaseManager(phase_set, set()), rca_set)

        # mocking the get_random_value inside the probability law
        # such mocking is necessary as without it, the random value returned by "get_random_value" can not be predicted
        # the test would always fail
        with patch.object(ProbabilityLaw, "get_random_value", return_value=10.):

            # populate list of B events
            b_events_set = BEventGenerator.generate_first_events(0, context)
            c_events_set = CEventGenerator.generate_first_events(0, context)

            b_events_from_c_events_set = set()
            for c_event in c_events_set:
                if c_event.is_condition_valid():
                    b_events_from_c_events_set.update(c_event.generate_b_events(0))
            b_events_set.update(b_events_from_c_events_set)

        # generating expected events
        import numpy as np
        phase_event = NextPhaseEvent(np.inf, context)
        first_failure_event = DetectableFailureEvent(10.,
                                                     context,
                                                     basic,
                                                     first_failure_mode)

        # testing the equality between result and expected results
        self.assertEqual(b_events_set, set([first_failure_event, phase_event]))

    def test_update_status(self):
        context = Context(None, None, None)
        basic = Basic(1, "test_basic_1", 0, [], None, [], [])
        status = Status.FAILED
        timestamp = 10
        phase = PhaseManager.NO_PHASE
        desc = "test"
        result = basic.update_status(status, timestamp, phase, desc, context)
        expected_result = [RecordComponent(basic, status, timestamp, phase, desc)]
        self.assertEqual(result, expected_result)
        self.assertEqual(basic.status, status)


if __name__ == '__main__':
    unittest.main()
