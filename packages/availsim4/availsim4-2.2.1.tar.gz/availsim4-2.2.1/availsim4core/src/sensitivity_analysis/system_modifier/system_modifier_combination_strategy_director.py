# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import itertools
import logging

from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier import SystemModifier
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination import SystemModifierCombination
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination_inner_strategy import \
    SystemModifierCombinationInnerStrategy
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination_outer_strategy import \
    SystemModifierCombinationOuterStrategy
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination_zip_strategy import \
    SystemModifierCombinationZipStrategy


class SystemModifierCombinationStrategyDirector:
    """
    Director Strategy class which defines the sensitivity strategies to apply.
    """

    @staticmethod
    def execute(exploration_strategy_list):
        """
        Defines the strategy to apply on the given exploration strategy list
        and returns the corresponding {SystemModifierCombination}
        :param exploration_strategy_list the list of {ExplorationStrategy}
        """
        system_modifier_combination_inner_list = SystemModifierCombinationInnerStrategy.execute(exploration_strategy_list)
        system_modifier_combination_zip_list = SystemModifierCombinationZipStrategy.execute(exploration_strategy_list)
        system_modifier_combination_outer_list = SystemModifierCombinationOuterStrategy.execute(exploration_strategy_list)

        system_modifier_combination_list = []

        for values_tuple in itertools.product(*[_list for _list in [
            system_modifier_combination_inner_list,
            system_modifier_combination_zip_list,
            system_modifier_combination_outer_list
            ]
            if _list]):

            local_system_modifier_combination_list=[]
            for value in values_tuple:

                local_system_modifier_combination_list.extend(value.system_modifier_list)

            system_modifier_combination_list.append(SystemModifierCombination(local_system_modifier_combination_list))

        logging.debug(f"sensitivity modifier combination list : {system_modifier_combination_list}")
        return system_modifier_combination_list
