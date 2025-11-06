# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.sensitivity_analysis.exploration_strategy import Inner, Outer
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier import SystemModifier
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination import SystemModifierCombination
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination_strategy_director import \
    SystemModifierCombinationStrategyDirector


class test_SystemModifierCombinationStrategyDirector(unittest.TestCase):

    def test_execute__outer_inner(self):
        system_modifier_list_outer_1 = [SystemModifier("inner", 5.), SystemModifier("outer1", 1.), SystemModifier("outer2", 3.)]
        system_modifier_list_outer_2 = [SystemModifier("inner", 5.), SystemModifier("outer1", 1.), SystemModifier("outer2", 4.)]
        system_modifier_list_outer_3 = [SystemModifier("inner", 5.), SystemModifier("outer1", 2.), SystemModifier("outer2", 3.)]
        system_modifier_list_outer_4 = [SystemModifier("inner", 5.), SystemModifier("outer1", 2.), SystemModifier("outer2", 4.)]

        expected_combination_result = [SystemModifierCombination(system_modifier_list_outer_1),
                                       SystemModifierCombination(system_modifier_list_outer_2),
                                       SystemModifierCombination(system_modifier_list_outer_3),
                                       SystemModifierCombination(system_modifier_list_outer_4)]

        exploration_strategy_list = [Outer("outer1", [1., 2.]),
                                     Outer("outer2", [3., 4.]),
                                     Inner("inner", [5.])]

        result = SystemModifierCombinationStrategyDirector.execute(exploration_strategy_list)

        self.assertEqual(expected_combination_result, result)
