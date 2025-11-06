# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import logging
from availsim4core.src.reader.reader import Reader

from availsim4core.src.sensitivity_analysis.exploration_strategy_factory import ExplorationStrategyFactory
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination_strategy_director import \
    SystemModifierCombinationStrategyDirector
from availsim4core.src.reader.xlsx import xlsx_utils


class SensitivityAnalysisSheet:
    SHEET = "SENSITIVITY_ANALYSIS"
    EXPLORATION_STRATEGY = "EXPLORATION_STRATEGY"
    PARAMETER_NAME = "PARAMETER_NAME"
    VALUES = "VALUES"


class SensitivityAnalysisError(Exception):
    pass


class SensitivityAnalysisReader(Reader):
    """
    Specific reader for the sensitivity analysis.
    """

    @classmethod
    def generate_system_modifier_combination_list(cls,
                                                  sensitivity_analysis_file_path):
        """
        Given a path for the configuration file of the sensitivity analysis it returns a list of
        SystemModifierCombination to apply.
        :param sensitivity_analysis_file_path the path of the configuration file for the sensitivity analysis.
        """
        exploration_strategy_list = cls._read_exploration_strategy_list(sensitivity_analysis_file_path)
        return SystemModifierCombinationStrategyDirector.execute(exploration_strategy_list)

    @classmethod
    def _read_exploration_strategy_list(cls,
                                        sensitivity_analysis_file_path):
        """
        Reads the sensitivity configuration file and returns the list of strategies to apply.
        """
        sensitivity_analysis_dictionary = xlsx_utils.read(sensitivity_analysis_file_path)

        exploration_strategy_list = []
        for row in sensitivity_analysis_dictionary[SensitivityAnalysisSheet.SHEET].values():

            exception_message_hint = f"sensitivity analysis row: {row}"

            current_line_strategy = xlsx_utils.clean_str_cell(row, SensitivityAnalysisSheet.EXPLORATION_STRATEGY,
                                                  exception_message_hint=exception_message_hint)
            current_line_parameter_name = xlsx_utils.clean_str_cell(row, SensitivityAnalysisSheet.PARAMETER_NAME,
                                                        exception_message_hint=exception_message_hint)
            current_line_values = row[SensitivityAnalysisSheet.VALUES]
            current_line_values = [current_line_values] if isinstance(current_line_values, (int, float)) \
                else xlsx_utils.clean_list_cell(row, SensitivityAnalysisSheet.VALUES)

            if len(current_line_values) == 0:
                message_exception = f"Error in the sensitivity analysis file: \n The parameter "\
                                    f"{current_line_parameter_name} is associated to an empty list of values"
                logging.exception(message_exception)
                raise SensitivityAnalysisError(message_exception)

            strategy = ExplorationStrategyFactory.build(current_line_parameter_name,
                                                        current_line_values,
                                                        current_line_strategy)
            exploration_strategy_list.append(strategy)

        logging.debug("Extracted from sensitivity file exploration_strategy_list: %s", exploration_strategy_list)
        return exploration_strategy_list
