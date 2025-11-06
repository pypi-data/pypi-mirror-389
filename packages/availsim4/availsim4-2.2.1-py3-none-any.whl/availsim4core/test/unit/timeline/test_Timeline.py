# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.children_logic.children_logic import ChildrenLogic
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.timeline.record_component import RecordComponent
from availsim4core.src.timeline.record_generator import RecordGenerator
from availsim4core.src.timeline.record_phase import RecordPhase
from availsim4core.src.timeline.timeline import Timeline


class test_Timeline(unittest.TestCase):

    def test_extract_record_from_types(self):
        basic_1 = Basic(1, "test_basic_1", 0, [], [], [], [])
        basic_2 = Basic(2, "test_basic_2", 0, [], [], [], [])

        component_list = [basic_1, basic_2]
        compound = Compound(3, "test_compound_1", 1, [], ChildrenLogic(), [])
        compound.add_children_list(component_list)

        record_phase = RecordPhase(PhaseManager.NO_PHASE,
                                   0, RecordGenerator.DESCRIPTION_INIT)

        record_list = [record_phase,
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

        timeline = Timeline()
        timeline.record_list = record_list
        result = timeline.extract_record_from_types(RecordPhase)
        expected_result = [record_phase]

        self.assertEqual(result, expected_result)
