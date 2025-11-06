# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

class SystemModifierCombinationStrategy:

    @classmethod
    def execute(cls, exploration_strategy_list):
        pass

    @staticmethod
    def filter_exploration(exploration_strategy_list,
                           exploration_class):
        """
        Given an {ExplorationStrategy} list it will filter and return only the elements of a given exploration class.
        :param exploration_strategy_list list of {ExplorationStrategy} to filter
        :param exploration_class the {ExplorationStrategy} class to filter out.
        """
        return [
            exploration_strategy
            for exploration_strategy in exploration_strategy_list
            if isinstance(exploration_strategy, exploration_class)
        ]
