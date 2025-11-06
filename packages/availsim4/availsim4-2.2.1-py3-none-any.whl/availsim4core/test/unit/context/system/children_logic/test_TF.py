# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for a class testing "Tolerated Fault" children logic
"""

import unittest

from typing import List
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.children_logic.children_logic import ChildrenLogic
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.children_logic import children_logic_factory
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.failure import Failure, FailureType
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw
from availsim4core.src.context.system.inspection import Inspection
from availsim4core.src.context.context import Context


# TODO: add tests on the status UNDER_REPAIR, BLIND_FAILED, etc

class test_TF(unittest.TestCase):

    context = Context(None, None, None)
    # number_of_running_basic, number_of_failed_basic, number_of_running_compound, number_of_failed_compound
    scenario_1 = [8, 0, 0, 0, "2TF", context, Status.RUNNING]
    scenario_2 = [6, 2, 0, 0, "2TF", context, Status.DEGRADED]
    scenario_3 = [4, 4, 0, 0, "2TF", context, Status.FAILED]
    scenario_4 = [0, 0, 8, 0, "2TF", context, Status.RUNNING]
    scenario_5 = [0, 0, 6, 2, "2TF", context, Status.DEGRADED]
    scenario_6 = [0, 0, 4, 4, "2TF", context, Status.FAILED]
    scenario_7 = [4, 0, 4, 0, "2TF", context, Status.RUNNING]
    scenario_8 = [3, 1, 4, 0, "2TF", context, Status.DEGRADED]
    scenario_9 = [2, 2, 2, 2, "2TF", context, Status.FAILED]
    param_scenario = [scenario_1, scenario_2, scenario_3,
                      scenario_4, scenario_5, scenario_6,
                      scenario_7, scenario_8, scenario_9]

    def _evaluate_generic(self,
                          number_of_running_basic: int,
                          number_of_failed_basic: int,
                          number_of_running_compound: int,
                          number_of_failed_compound: int,
                          children_logic_str: str,
                          context: Context,
                          expected_result: Status):

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

        logic = children_logic_factory.build(children_logic_str, None)
        result = logic.evaluate(list_of_component, context)

        self.assertEqual(result, expected_result)

    def test_runner(self):
        for number_of_running_basic, number_of_failed_basic, \
            number_of_running_compound, number_of_failed_compound, \
            logic, context, expected_result in self.param_scenario:
            with self.subTest():
                self._evaluate_generic(number_of_running_basic,
                                       number_of_failed_basic,
                                       number_of_running_compound,
                                       number_of_failed_compound,
                                       logic,
                                       context,
                                       expected_result)


if __name__ == '__main__':
    unittest.main()
