# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.children_logic.and_ import And
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.failure import Failure, FailureType
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.probability_law.deterministic_law import DeterministicLaw
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.blind_failure_event import \
    BlindFailureEvent
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.detectable_failure_event import \
    DetectableFailureEvent
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event import failure_event_factory


class test_FailureEventFactory(unittest.TestCase):

    def test_build_detectable(self):
        DETERMINISTIC_VALUE = 1
        context = Context(None, [], set())
        failure_mode_1 = FailureMode("test_run",
                                     DeterministicLaw([DETERMINISTIC_VALUE]),
                                     DeterministicLaw([DETERMINISTIC_VALUE]),
                                     Failure(FailureType.DETECTABLE),
                                     [],
                                     None,
                                     [],
                                     None,
                                     'NEVER',
                                     [])

        root_component = Compound(1, "ROOT", 0, [], And(), [])

        ABSOLUTE_SIMULATION_TIME = 5
        result = failure_event_factory.build(DETERMINISTIC_VALUE + ABSOLUTE_SIMULATION_TIME,
                                           context, root_component, failure_mode_1)

        expected_result = DetectableFailureEvent(DETERMINISTIC_VALUE + ABSOLUTE_SIMULATION_TIME,
                                                 context,
                                                 root_component,
                                                 failure_mode_1)

        self.assertEqual(result, expected_result)

    def test_build_blind(self):
        DETERMINISTIC_VALUE = 1
        context = Context(None, [], set())
        failure_mode_1 = FailureMode("test_run",
                                     DeterministicLaw([DETERMINISTIC_VALUE]),
                                     DeterministicLaw([DETERMINISTIC_VALUE]),
                                     Failure(FailureType.BLIND),
                                     [],
                                     None,
                                     [],
                                     None,
                                     'NEVER',
                                     [])

        root_component = Compound(1, "ROOT", 0, [], And(), [])

        ABSOLUTE_SIMULATION_TIME = 5
        result = failure_event_factory.build(DETERMINISTIC_VALUE + ABSOLUTE_SIMULATION_TIME,
                                           context, root_component, failure_mode_1)

        expected_result = BlindFailureEvent(DETERMINISTIC_VALUE + ABSOLUTE_SIMULATION_TIME,
                                            context,
                                            root_component,
                                            failure_mode_1)

        self.assertEqual(result, expected_result)
