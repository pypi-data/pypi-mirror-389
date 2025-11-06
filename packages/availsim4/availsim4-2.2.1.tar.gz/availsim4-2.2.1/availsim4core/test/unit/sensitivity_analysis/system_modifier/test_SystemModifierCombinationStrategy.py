# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.sensitivity_analysis.exploration_strategy import Inner, Outer
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination_strategy import \
    SystemModifierCombinationStrategy


class test_SystemModifierCombinationStrategy(unittest.TestCase):

    def test_filter_exploration__inner(self):
        exploration_strategy_list = [Inner("inner", 0),
                                     Outer("outer", 1)]

        expected_result = [Inner("inner", 0)]

        result = SystemModifierCombinationStrategy.filter_exploration(exploration_strategy_list, Inner)

        self.assertEqual(expected_result, result)

    def test_filter_exploration__outer(self):
        exploration_strategy_list = [Inner("inner", 0),
                                     Outer("outer", 1)]

        expected_result = [Outer("outer", 1)]

        result = SystemModifierCombinationStrategy.filter_exploration(exploration_strategy_list, Outer)

        self.assertEqual(expected_result, result)
