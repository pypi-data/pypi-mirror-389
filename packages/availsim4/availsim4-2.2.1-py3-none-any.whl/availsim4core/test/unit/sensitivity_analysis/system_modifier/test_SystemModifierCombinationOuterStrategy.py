# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.sensitivity_analysis.exploration_strategy import Outer, Inner
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier import SystemModifier
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination import SystemModifierCombination
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination_outer_strategy import \
    SystemModifierCombinationOuterStrategy


class test_SystemModifierCombinationOuterStrategy(unittest.TestCase):

    def test_execute(self):
        exploration_strategy_list = [Outer("outer1", [1., 2.]),
                                     Outer("outer2", [3., 4.]),
                                     Inner("inner1", [5., 6.])]

        system_modifier_list_outer_1 = [SystemModifier("outer1", 1.), SystemModifier("outer2", 3.)]
        system_modifier_list_outer_2 = [SystemModifier("outer1", 1.), SystemModifier("outer2", 4.)]
        system_modifier_list_outer_3 = [SystemModifier("outer1", 2.), SystemModifier("outer2", 3.)]
        system_modifier_list_outer_4 = [SystemModifier("outer1", 2.), SystemModifier("outer2", 4.)]

        expected_results = [SystemModifierCombination(system_modifier_list_outer_1),
                            SystemModifierCombination(system_modifier_list_outer_2),
                            SystemModifierCombination(system_modifier_list_outer_3),
                            SystemModifierCombination(system_modifier_list_outer_4)]

        results = SystemModifierCombinationOuterStrategy.execute(exploration_strategy_list)

        self.assertEqual(expected_results, results)
