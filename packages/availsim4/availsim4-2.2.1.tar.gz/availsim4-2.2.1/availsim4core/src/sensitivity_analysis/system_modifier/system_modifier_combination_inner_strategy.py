# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.sensitivity_analysis.exploration_strategy import Inner
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier import SystemModifier
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination import SystemModifierCombination
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination_strategy import \
    SystemModifierCombinationStrategy


class SystemModifierCombinationInnerStrategy(SystemModifierCombinationStrategy):
    """
    Strategy to apply the Inner logic.

    :eg.
        Default analysis with
            - A:0, B:0, C:0
        Given:
            - Inner(A; 1)
            - Inner(B; 2,3,4)
            - Inner(C; 10)

        It results in 5 analysis :
            - A:1, B:0, C:0
            - A:0, B:2, C:0
            - A:0, B:3, C:0
            - A:0, B:4, C:0
            - A:0, B:0, C:10
    """

    @classmethod
    def execute(cls, exploration_strategy_list):
        """
        Given a list of {ExplorationStrategy} it returns a list of corresponding {SystemModifierCombination}.
        :param exploration_strategy_list the list from which the Inner strategy will be extracted and applied
        to get the corresponding combination
        :returns list of {SystemModifierCombination} corresponding to the Inner logic.
        """
        inner_exploration_strategy_list = cls.filter_exploration(exploration_strategy_list,
                                                                 Inner)
        inner_combination_list = []

        for exploration_strategy_inner in inner_exploration_strategy_list:
            for inner_value in exploration_strategy_inner.values:
                curr_system_modifier = SystemModifier(exploration_strategy_inner.parameter_name, inner_value)
                inner_combination_list.append(SystemModifierCombination([curr_system_modifier]))
        return inner_combination_list
