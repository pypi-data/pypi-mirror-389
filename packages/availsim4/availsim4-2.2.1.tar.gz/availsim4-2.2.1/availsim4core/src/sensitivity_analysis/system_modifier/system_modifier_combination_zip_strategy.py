# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import logging

from availsim4core.src.sensitivity_analysis.exploration_strategy import Zip
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier import SystemModifier
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination import SystemModifierCombination
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination_strategy import \
    SystemModifierCombinationStrategy


class ZipStrategyError(Exception):
    pass


class SystemModifierCombinationZipStrategy(SystemModifierCombinationStrategy):
    """
    Strategy to apply the Inner logic.

    :eg.
        Default analysis with
            - A:0, B:0, C:0
        Given:
            - Zip(A; 1,2,3)
            - Zip(B; 1,2,3)
            - Zip(C; 1,2,3)

        It results in 3 analysis :
            - A:1, B:1, C:1
            - A:2, B:2, C:2
            - A:3, B:3, C:3
    """

    @classmethod
    def execute(cls, exploration_strategy_list):
        """
        Given a list of {ExplorationStrategy} it returns a list of corresponding {SystemModifierCombination}.
        :param exploration_strategy_list the list from which the Zip strategy will be extracted and applied
        to get the corresponding combination
        :returns list of {SystemModifierCombination} corresponding to the Inner logic.
        """
        zip_exploration_strategy_list = cls.filter_exploration(exploration_strategy_list, Zip)
        zip_combination_list = []

        # if len(zip_exploration_strategy_list)==0, then the user did not request any ZIP strategy

        if len(zip_exploration_strategy_list)==1:
            exception_message = (f"ZIP strategies misconfigured, at least two occurrences of ZIP strategies should be "
                                 f"in the sensitivity analysis input file but only one is present")
            logging.exception(exception_message)
            raise ZipStrategyError(exception_message)

        elif len(zip_exploration_strategy_list)>1:

            # testing if the length of all the zip_exploration_strategy are equal
            length = len(zip_exploration_strategy_list[0].values)
            for idx in range(1,len(zip_exploration_strategy_list)):
                idx_length = len(zip_exploration_strategy_list[idx].values)
                if idx_length != length:
                    exception_message = (f"ZIP strategies missconfigured, the length of the {idx} strategy has "
                                         f"{idx_length} elements instead of {length}")
                    logging.exception(exception_message)
                    raise ZipStrategyError(exception_message)

            # building the system modifiers
            for idv in range(0,length):
                curr_system_modifier_list = [SystemModifier(zip_exploration_strategy_list[0].parameter_name,
                                                            zip_exploration_strategy_list[0].values[idv])]
                for idx in range(1,len(zip_exploration_strategy_list)):
                    curr_system_modifier_list.append(SystemModifier(zip_exploration_strategy_list[idx].parameter_name,
                                                                    zip_exploration_strategy_list[idx].values[idv]))
                zip_combination_list.append(SystemModifierCombination(curr_system_modifier_list))

        return zip_combination_list
