# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from typing import List
from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.children_logic.children_logic import ChildrenLogic
from availsim4core.src.context.system.children_logic.oo import Oo
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.failure import Failure, FailureType
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.inspection import Inspection
from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw
from availsim4core.src.context.context import Context


# TODO: add tests on the status UNDER_REPAIR, BLIND_FAILED, etc

class test_OO(unittest.TestCase):

    context = Context(None, None, None)
    # number_of_running_basic, number_of_failed_basic, number_of_running_compound, number_of_failed_compound
    scenario_1 = [8, 0, 0, 0, context, Status.RUNNING, 6, 8]
    scenario_2 = [6, 2, 0, 0, context, Status.DEGRADED, 6, 8]
    scenario_3 = [4, 4, 0, 0, context, Status.FAILED, 6, 8]
    scenario_4 = [0, 0, 8, 0, context, Status.RUNNING, 6, 8]
    scenario_5 = [0, 0, 6, 2, context, Status.DEGRADED, 6, 8]
    scenario_6 = [0, 0, 4, 4, context, Status.FAILED, 6, 8]
    scenario_7 = [4, 0, 4, 0, context, Status.RUNNING, 6, 8]
    scenario_8 = [3, 1, 4, 0, context, Status.DEGRADED, 6, 8]
    scenario_9 = [2, 2, 2, 2, context, Status.FAILED, 6, 8]
    param_scenario = [scenario_1, scenario_2, scenario_3,
                      scenario_4, scenario_5, scenario_6,
                      scenario_7, scenario_8, scenario_9]

    def _evaluate_generic(self,
                          number_of_running_basic: int,
                          number_of_failed_basic: int,
                          number_of_running_compound: int,
                          number_of_failed_compound: int,
                          context: Context,
                          expected_result: Status,
                          minimum_number_of_required_component: int,
                          total_number_of_component: int):

        list_of_component: List[Component] = []
        NO_PHASE = PhaseManager.NO_PHASE
        expected_inspection = Inspection("inspection_test", 1, 2)

        dummy_fm = FailureMode("TEST_FAILURE",
                                     ProbabilityLaw("", [0], False),
                                     ProbabilityLaw("", [0], False),
                                     Failure(FailureType.DETECTABLE),
                                     {NO_PHASE},
                                     expected_inspection,
                                     {NO_PHASE},
                                     NO_PHASE,
                                     'AFTER_REPAIR',
                                     {NO_PHASE})

        for _ in range(number_of_running_basic):
            basic = Basic(0, "dummyName", 0, [], dummy_fm, [], [])
            list_of_component.append(basic)

        for _ in range(number_of_failed_basic):
            basic = Basic(0, "dummyName", 0, [], dummy_fm, [], [])
            basic.status = Status.FAILED
            list_of_component.append(basic)

        for _ in range(number_of_running_compound):
            compound = Compound(0, "test_compound_1", 1, [], ChildrenLogic(), [])
            list_of_component.append(compound)

        for _ in range(number_of_failed_compound):
            compound = Compound(0, "test_compound_1", 1, [], ChildrenLogic(), [])
            compound.status = Status.FAILED
            list_of_component.append(compound)

        oo = Oo(minimum_number_of_required_component, total_number_of_component)
        result = oo.evaluate(list_of_component, context)

        self.assertEqual(result, expected_result)

    def test_runner(self):
        for number_of_running_basic, \
            number_of_failed_basic, \
            number_of_running_compound, \
            number_of_failed_compound, \
            context, \
            expected_result, \
            minimum_number_of_required_component, \
            total_number_of_component in self.param_scenario:
            with self.subTest():
                self._evaluate_generic(number_of_running_basic,
                                       number_of_failed_basic,
                                       number_of_running_compound,
                                       number_of_failed_compound,
                                       context,
                                       expected_result,
                                       minimum_number_of_required_component,
                                       total_number_of_component)


if __name__ == '__main__':
    unittest.main()
