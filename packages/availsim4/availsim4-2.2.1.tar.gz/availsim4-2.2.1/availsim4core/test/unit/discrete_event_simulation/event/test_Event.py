# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import copy
import unittest

from availsim4core.src.context.context import Context
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.children_logic.and_ import And
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.failure import Failure, FailureType
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.inspection import Inspection
from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.detectable_failure_event import \
    DetectableFailureEvent
from availsim4core.src.discrete_event_simulation.event.b_event.inspection_event.start_inspection_event import \
    StartInspectionEvent


class test_Event(unittest.TestCase):

    def test__clean_event_collection(self):
        context = Context(None, [], set())
        root_component = Compound(1, "ROOT", 0, [], And(), [])
        _basic = Basic(2, "BASIC", 0, [root_component], [], [], [])
        _basic2 = Basic(3, "BASIC", 0, [root_component], [], [], [])

        NO_PHASE = PhaseManager.NO_PHASE

        expected_inspection = Inspection("inspection_test", 1, 2)

        failure_mode = FailureMode("TEST_FAILURE",
                                   ProbabilityLaw("", 0, False),
                                   ProbabilityLaw("", 0, False),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   expected_inspection,
                                   [],
                                   NO_PHASE,
                                   'AFTER_FAILURE',
                                   []
                                   )

        event_basic_1 = StartInspectionEvent(0, context, _basic, failure_mode)
        event_basic_2 = DetectableFailureEvent(1, context, _basic, copy.deepcopy(failure_mode))
        event_basic_3 = DetectableFailureEvent(1, context, _basic2, copy.deepcopy(failure_mode))

        event_set = {event_basic_1, event_basic_2, event_basic_3}

        result, event_removed_result = event_basic_1.update_b_event_collection(
            event_set,
            event_basic_1._b_events_to_be_cleaned())

        expected_result = {event_basic_1, event_basic_3}
        expected_removed = {event_basic_2}
        self.assertEqual(result, expected_result)
        self.assertEqual(event_removed_result, expected_removed)

    def test__clean_event_collection_not_changed(self):
        context = Context(None, [], set())
        root_component = Compound(1, "ROOT", 0, [], And(), [])
        _basic = Basic(2, "BASIC", 0, [root_component], [], [], [])
        _basic2 = Basic(3, "BASIC", 0, [root_component], [], [], [])

        NO_PHASE = PhaseManager.NO_PHASE

        expected_inspection = Inspection("inspection_test", 1, 2)

        failure_mode = FailureMode("TEST_FAILURE",
                                   ProbabilityLaw("", 0, False),
                                   ProbabilityLaw("", 0, False),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   expected_inspection,
                                   [],
                                   NO_PHASE,
                                   'AFTER_FAILURE',
                                   []
                                   )

        event_basic_1 = StartInspectionEvent(0, context, _basic, failure_mode)
        event_basic_2 = DetectableFailureEvent(0, context, _basic2, copy.deepcopy(failure_mode))

        event_set = {event_basic_1, event_basic_2}

        result, event_removed_result = event_basic_1.update_b_event_collection(
            event_set,
            event_basic_1._b_events_to_be_cleaned())

        expected_result = event_set
        self.assertEqual(result, expected_result)
        self.assertEqual(event_removed_result, set())

    # TODO with the mru, inspection, blind, etc ... all kind of events Bevents and Cevents.
