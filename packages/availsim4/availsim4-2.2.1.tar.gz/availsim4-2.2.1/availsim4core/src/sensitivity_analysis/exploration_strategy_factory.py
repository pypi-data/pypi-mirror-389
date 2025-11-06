# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.sensitivity_analysis.exploration_strategy import Inner, Outer, Zip


class SensitivityAnalysisStrategyError(Exception):
    pass


class ExplorationStrategyFactory:
    """
    Factory class for the Exploration Strategy
    """

    @staticmethod
    def build(parameter_name,
              values,
              strategy_str):
        """
        Given a strategy_str it creates the corresponding ExplorationStrategy.
        Note: strategy_name is case UNsensitive.
        :param parameter_name name of the parameter onto which the strategy will be applied
        :param values the values to apply
        :param strategy_str the string representation of the strategy to apply.
        :raise SensitivityAnalysisStrategyException when the given strategy_str is not applicable.
        """
        if strategy_str.upper() == "INNER":
            return Inner(parameter_name, values)
        elif strategy_str.upper() == "OUTER":
            return Outer(parameter_name, values)
        elif strategy_str.upper() == "ZIP":
            return Zip(parameter_name, values)
        else:
            message_exception = f"{strategy_str} wrong strategy in sensitivity analysis for line"
            import logging
            logging.exception(message_exception)
            raise SensitivityAnalysisStrategyError(message_exception)
