# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest
from unittest.mock import patch

from availsim4core.src.context.context import Context
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.children_logic.and_ import And
from availsim4core.src.context.system.children_logic.children_logic import ChildrenLogic
from availsim4core.src.context.system.children_logic.oo import Oo
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.failure import Failure, FailureType
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw
from availsim4core.src.discrete_event_simulation.b_event_generator import BEventGenerator
from availsim4core.src.discrete_event_simulation.c_event_generator import CEventGenerator
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.detectable_failure_event import \
    DetectableFailureEvent
from availsim4core.src.discrete_event_simulation.event.b_event.phase_event.next_phase_event import NextPhaseEvent


class test_Compound(unittest.TestCase):

    def test_to_set(self):
        compound = Compound(1, "test_compound_1", 1, [], ChildrenLogic(), [])

        basic_1 = Basic(2, "test_basic_1", 0, [compound], None, [], [])
        basic_2 = Basic(3, "test_basic_2", 0, [compound], None, [], [])

        component_list = [basic_1, basic_2]
        compound.add_children_list(component_list)

        result = compound.to_set()
        self.assertEqual(result, set([compound, basic_1, basic_2]))

    def test_get_initial_failure_events(self):
        phase_set = set()
        rca_set = set()
        # failures modes used to define a {Basic}
        failure_mode_1 = FailureMode("test_failure_mode_1",
                                     ProbabilityLaw("dummy", 1.0, False),
                                     ProbabilityLaw("dummy", 2.0, False),
                                     Failure(FailureType.DETECTABLE),
                                     phase_set,
                                     None,
                                     phase_set,
                                     None,
                                     'AFTER_REPAIR',
                                     phase_set)
        failure_mode_2 = FailureMode("test_failure_mode_2",
                                     ProbabilityLaw("dummy", 3.0, False),
                                     ProbabilityLaw("dummy", 4.0, False),
                                     Failure(FailureType.DETECTABLE),
                                     phase_set,
                                     None,
                                     phase_set,
                                     None,
                                     'AFTER_REPAIR',
                                     phase_set)

        basic_1 = Basic(1, "test_basic_1", 0, [], failure_mode_1, [], [])
        basic_2 = Basic(2, "test_basic_2", 0, [], failure_mode_2, [], [])

        component_list = [basic_1, basic_2]
        compound = Compound(3, "test_compound_1", 1, [], ChildrenLogic(), [])
        compound.add_children_list(component_list)

        context = Context(compound, PhaseManager(phase_set, set()), rca_set)

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
        failure_event_1 = DetectableFailureEvent(10.,
                                                 context,
                                                 basic_1,
                                                 failure_mode_1)
        failure_event_2 = DetectableFailureEvent(10.,
                                                 context,
                                                 basic_2,
                                                 failure_mode_2)

        # testing the equality between result and expected results
        self.assertEqual(b_events_set, set([failure_event_1, failure_event_2, phase_event]))

    def test_get_initial_failure_events__with_absolute_time_not_0(self):
        ABSOLUTE_TIME = 5
        RANDOM_VALUE = 10.
        phase_set = set()
        rca_set = set()
        # failures modes used to define a Basic
        failure_mode_1 = FailureMode("test_failure_mode_1",
                                     ProbabilityLaw("dummy", 1.0, False),
                                     ProbabilityLaw("dummy", 2.0, False),
                                     Failure(FailureType.DETECTABLE),
                                     phase_set,
                                     None,
                                     phase_set,
                                     None,
                                     'AFTER_REPAIR',
                                     phase_set)
        failure_mode_2 = FailureMode("test_failure_mode_2",
                                     ProbabilityLaw("dummy", 3.0, False),
                                     ProbabilityLaw("dummy", 4.0, False),
                                     Failure(FailureType.DETECTABLE),
                                     phase_set,
                                     None,
                                     phase_set,
                                     None,
                                     'AFTER_REPAIR',
                                     phase_set)

        basic_1 = Basic(1, "test_basic_1", 0, [], failure_mode_1, [], [])
        basic_2 = Basic(2, "test_basic_2", 0, [], failure_mode_2, [], [])

        component_list = [basic_1, basic_2]
        compound = Compound(3, "test_compound_1", 1, [], ChildrenLogic(), [])
        compound.add_children_list(component_list)

        context = Context(compound, PhaseManager(phase_set, set()), rca_set)

        # mocking the get_random_value inside the probability law
        # such mocking is necessary as without it, the random value returned by "get_random_value" can not be predicted
        # the test would always fail
        with patch.object(ProbabilityLaw, "get_random_value", return_value=RANDOM_VALUE):

            # populate list of B events
            b_events_set = BEventGenerator.generate_first_events(ABSOLUTE_TIME, context)
            c_events_set = CEventGenerator.generate_first_events(ABSOLUTE_TIME, context)

            b_events_from_c_events_set = set()
            for c_event in c_events_set:
                if c_event.is_condition_valid():
                    b_events_from_c_events_set.update(c_event.generate_b_events(ABSOLUTE_TIME))
            b_events_set.update(b_events_from_c_events_set)

        # generating expected events
        import numpy as np
        phase_event = NextPhaseEvent(np.inf, context)
        failure_event_1 = DetectableFailureEvent(RANDOM_VALUE + ABSOLUTE_TIME,
                                                 context,
                                                 basic_1,
                                                 failure_mode_1)
        failure_event_2 = DetectableFailureEvent(RANDOM_VALUE + ABSOLUTE_TIME,
                                                 context,
                                                 basic_2,
                                                 failure_mode_2)

        # testing the equality between result and expected results
        expected_result = set([failure_event_1, failure_event_2, phase_event])
        self.assertEqual(b_events_set, expected_result)

    def test_update_status__children_running(self):
        compound = Compound(1, "test_update_status", 0, [], And(), [])
        basic_1 = Basic(2, "test_basic_1", 1, [compound], None, [], [])
        basic_2 = Basic(3, "test_basic_2", 2, [compound], None, [], [])
        component_list = [basic_1, basic_2]
        compound.add_children_list(component_list)

        context = Context(None, None, None)

        compound.update_status(10, PhaseManager.NO_PHASE, "test_desc",context)

        self.assertEqual(compound.status, Status.RUNNING)

    def test_update_status__running(self):
        compound = Compound(1, "test_update_status", 0, [], And(), [])
        basic_1 = Basic(2, "test_basic_1", 1, [compound], None, [], [])
        basic_2 = Basic(3, "test_basic_2", 2, [compound], None, [], [])
        component_list = [basic_1, basic_2]
        compound.add_children_list(component_list)
        basic_2.status = Status.FAILED

        context = Context(None,None,None)

        compound.update_status(10, PhaseManager.NO_PHASE, "test_desc",context)

        self.assertEqual(compound.status, Status.FAILED)

    def test_evaluate_status_and_running(self):
        compound = Compound(1, "test_compound_1", 0, [], And(), [])

        basic_1 = Basic(2, "test_basic_1", 1, [compound], None, [], [])
        basic_2 = Basic(3, "test_basic_2", 2, [compound], None, [], [])

        component_list = [basic_1, basic_2]
        compound.add_children_list(component_list)

        context = Context(None,None,None)
        result = compound.evaluate_status(context)

        self.assertEqual(result, Status.RUNNING)

    def test_evaluate_status_and_failed(self):
        compound = Compound(1, "test_compound_1", 0, [], And(), [])

        basic_1 = Basic(2, "test_basic_1", 1, [compound], None, [], [])
        basic_2 = Basic(3, "test_basic_2", 2, [compound], None, [], [])
        basic_1.status = Status.FAILED
        basic_2.status = Status.FAILED

        component_list = [basic_1, basic_2]
        compound.add_children_list(component_list)

        context = Context(None,None,None)
        result = compound.evaluate_status(context)

        self.assertEqual(result, Status.FAILED)

    def test_evaluate_status_1oo2_running(self):
        compound = Compound(1, "test_compound_1", 0, [], Oo(1,2), [])

        basic_1 = Basic(2, "test_basic_1", 1, [compound], None, [], [])
        basic_2 = Basic(3, "test_basic_2", 2, [compound], None, [], [])
        basic_1.status = Status.FAILED
        basic_2.status = Status.RUNNING

        component_list = [basic_1, basic_2]
        compound.add_children_list(component_list)

        context = Context(None,None,None)
        result = compound.evaluate_status(context)

        self.assertEqual(result, Status.DEGRADED)


if __name__ == '__main__':
    unittest.main()
