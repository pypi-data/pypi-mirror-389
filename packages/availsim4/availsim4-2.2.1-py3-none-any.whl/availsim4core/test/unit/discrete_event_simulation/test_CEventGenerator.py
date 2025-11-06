# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.context import Context
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.children_logic.and_ import And
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.minimal_replaceable_unit import MinimalReplaceableUnit
from availsim4core.src.context.system.probability_law.deterministic_law import DeterministicLaw
from availsim4core.src.discrete_event_simulation.c_event_generator import CEventGenerator
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.repair_event.minimal_replaceable_unit_order_repair_event import \
    MinimalReplaceableUnitOrderRepairEvent


class test_CEventGenerator(unittest.TestCase):

    def test_get_initial_c_events_basic_mru(self):
        mru_1 = MinimalReplaceableUnit("test_get_initial_c_events_basic_mru",
                                       DeterministicLaw(0),
                                       "IMMEDIATE",
                                       Status.FAILED,
                                       "ROOT")

        root_component = Compound(1, "ROOT", 0, [], And(), [])
        _basic_1 = Basic(2, "BASIC1", 0, [root_component], None, [mru_1], [mru_1])

        root_component.add_children_list([_basic_1])
        context = Context(root_component, PhaseManager(set(),set()), set())
        result = CEventGenerator.get_c_events_for_mrus(context,
                                                       context.root_component)

        mru_event1 = MinimalReplaceableUnitOrderRepairEvent(CEventPriority.MRU_ORDER_REPAIR_EVENT, context, _basic_1, mru_1)
        expected_results = set([mru_event1])

        self.assertEqual(result, expected_results)

    def test_get_initial_c_events_compound_multiple_mru(self):
        mru_1 = MinimalReplaceableUnit("test_get_initial_c_events_basic_mru_1",
                                       DeterministicLaw(0),
                                       "IMMEDIATE",
                                       Status.FAILED,
                                       "ROOT")

        mru_2 = MinimalReplaceableUnit("test_get_initial_c_events_basic_mru_2",
                                       DeterministicLaw(0),
                                       "IMMEDIATE",
                                       Status.FAILED,
                                       "ROOT")

        root_component = Compound(1, "ROOT", 0, [], And(), [])
        _compound_1 = Compound(2, "COMPOUND1", 0, [root_component], And(), [mru_1, mru_2])
        _basic_1 = Basic(3, "BASIC1", 0, [_compound_1], None, [], [mru_1])
        _basic_2 = Basic(4, "BASIC2", 0, [_compound_1], None, [], [mru_1])

        root_component.add_children_list([_compound_1])
        _compound_1.add_children_list([_basic_1, _basic_2])

        context = Context(root_component, PhaseManager(set(),set()), set())
        result = CEventGenerator.get_c_events_for_mrus(context,
                                                       context.root_component)
        mru_event1 = MinimalReplaceableUnitOrderRepairEvent(CEventPriority.MRU_ORDER_REPAIR_EVENT, context, _compound_1, mru_1)
        mru_event2 = MinimalReplaceableUnitOrderRepairEvent(CEventPriority.MRU_ORDER_REPAIR_EVENT, context, _compound_1, mru_2)
        expected_results = set([mru_event1, mru_event2])

        self.assertEqual(result, expected_results)
