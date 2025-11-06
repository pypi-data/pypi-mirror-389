# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.sensitivity_analysis.exploration_strategy import Inner, Outer
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier import SystemModifier
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination import SystemModifierCombination
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination_inner_strategy import \
    SystemModifierCombinationInnerStrategy


class test_SystemModifierCombinationInnerStrategy(unittest.TestCase):

    def test_execute(self):
        exploration_strategy_list = [Outer("outer1", [1., 2.]),
                                     Inner("inner1", [3., 4.]),
                                     Inner("inner2", [5., 6.])]

        system_modifier_list_inner_1 = [SystemModifier("inner1", 3.)]
        system_modifier_list_inner_2 = [SystemModifier("inner1", 4.)]
        system_modifier_list_inner_3 = [SystemModifier("inner2", 5.)]
        system_modifier_list_inner_4 = [SystemModifier("inner2", 6.)]
        expected_results = [SystemModifierCombination(system_modifier_list_inner_1),
                            SystemModifierCombination(system_modifier_list_inner_2),
                            SystemModifierCombination(system_modifier_list_inner_3),
                            SystemModifierCombination(system_modifier_list_inner_4)]

        results = SystemModifierCombinationInnerStrategy.execute(exploration_strategy_list)

        self.assertEqual(expected_results, results)
