# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.context import Context
from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.children_logic.children_logic import ChildrenLogic
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.probability_law.deterministic_law import DeterministicLaw
from availsim4core.src.timeline.record_component import RecordComponent
from availsim4core.src.timeline.record_generator import RecordGenerator
from availsim4core.src.timeline.record_phase import RecordPhase


class test_RecordGenerator(unittest.TestCase):

    def test_get_initial_records(self):
        phase_set = {PhaseManager.NO_PHASE}
        rca_set = set()

        basic_1 = Basic(1, "test_basic_1", 0, [], [], [], [])
        basic_2 = Basic(2, "test_basic_2", 0, [], [], [], [])

        component_list = [basic_1, basic_2]
        compound = Compound(3, "test_compound_1", 1, [], ChildrenLogic(), [])
        compound.add_children_list(component_list)

        context = Context(compound, PhaseManager(phase_set, set()), rca_set)

        result = RecordGenerator.get_initial_records(0, context)

        expected_record_list = [RecordPhase(PhaseManager.NO_PHASE,
                                            0, RecordGenerator.DESCRIPTION_INIT),
                                RecordComponent(basic_1,
                                                Status.RUNNING,
                                                0,
                                                PhaseManager.NO_PHASE,
                                                RecordGenerator.DESCRIPTION_INIT),
                                RecordComponent(basic_2,
                                                Status.RUNNING,
                                                0,
                                                PhaseManager.NO_PHASE,
                                                RecordGenerator.DESCRIPTION_INIT),
                                RecordComponent(compound,
                                                Status.RUNNING,
                                                0,
                                                PhaseManager.NO_PHASE,
                                                RecordGenerator.DESCRIPTION_INIT)
                                ]
        self.assertEqual(result, expected_record_list)

    def test_get_initial_records__phases(self):
        phase_first = Phase("phase_test", DeterministicLaw(10), True)
        phase_second = Phase("phase_second", DeterministicLaw(10), False)
        phase_first.set_next_phase(phase_second)
        phase_second.set_next_phase(phase_first)
        phase_set = {phase_first, phase_second}

        compound = Compound(3, "test_compound_1", 1, [], ChildrenLogic(), [])

        context = Context(compound, PhaseManager(phase_set, set()), set())

        result = RecordGenerator.get_initial_records(0, context)

        expected_record_list = [RecordPhase(phase_first,
                                            0, RecordGenerator.DESCRIPTION_INIT),
                                RecordComponent(compound,
                                                Status.RUNNING,
                                                0,
                                                phase_first,
                                                RecordGenerator.DESCRIPTION_INIT)
                                ]
        self.assertEqual(result, expected_record_list)
