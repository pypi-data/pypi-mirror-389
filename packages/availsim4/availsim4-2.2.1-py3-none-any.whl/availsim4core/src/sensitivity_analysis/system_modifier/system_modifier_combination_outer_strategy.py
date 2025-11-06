# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import itertools

from availsim4core.src.sensitivity_analysis.exploration_strategy import Outer
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier import SystemModifier
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination import SystemModifierCombination
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination_strategy import \
    SystemModifierCombinationStrategy


class SystemModifierCombinationOuterStrategy(SystemModifierCombinationStrategy):
    """
       Strategy to apply the Outer logic.

    :eg.
       Default analysis with
           - A:0, B:0, C:0
       Given:
           - Outer(A, 1)
           - Outer(A, 2)
           - Outer(C, 3)
           - Outer(C, 4)

       It results in 4 analysis :
           - A:1, B:0, C:3
           - A:2, B:0, C:3
           - A:1, B:0, C:4
           - A:2, B:0, C:4
    """

    @classmethod
    def execute(cls, exploration_strategy_list):
        """
        Given a list of {ExplorationStrategy} it returns a list of corresponding {SystemModifierCombination}.
        :param exploration_strategy_list the list from which the Inner strategy will be extracted and applied to get
        the corresponding combination
        :returns list of {SystemModifierCombination} corresponding to the Outer logic.
        """
        outer_exploration_strategy_list = cls.filter_exploration(exploration_strategy_list,
                                                                 Outer)
        outer_combination_list = []
        for values_tuple in itertools.product(*outer_exploration_strategy_list):  # Cartesian product
            system_modifier_list = []
            for idx, value in enumerate(values_tuple):
                system_modifier_list.append(
                    SystemModifier(outer_exploration_strategy_list[idx].parameter_name, value))
            if system_modifier_list:
                outer_combination_list.append(SystemModifierCombination(system_modifier_list))
        return outer_combination_list
