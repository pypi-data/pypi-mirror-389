# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest
from unittest.mock import patch
from availsim4core.src.reader.xlsx import xlsx_utils

from availsim4core.src.reader.xlsx.sensitivity_analysis_reader import SensitivityAnalysisReader
from availsim4core.src.sensitivity_analysis.exploration_strategy import Inner, Outer
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier import SystemModifier
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination import SystemModifierCombination


class test_SensitivityAnalysisReader(unittest.TestCase):

    def test_generate_system_template_modifier_combination_list(self):
        sensitivity_analysis_dictionary = {
            'SENSITIVITY_ANALYSIS': {
                0: {"PARAMETER_NAME": 'FIRST_OUTER_PARAM_COLUMN/DUMBER',
                    "VALUES": '[4, 5]',
                    "EXPLORATION_STRATEGY": "OUTER"},
                1: {"PARAMETER_NAME": 'SECOND_OUTER_PARAM_COLUMN/DUMBERFailure',
                    "VALUES": '[1., 2.]',
                    "EXPLORATION_STRATEGY": "OUTER"},
                2: {"PARAMETER_NAME": 'FIRST_INNER_PARAM_COLUMN/INNER_PARAM_LINE',
                    "VALUES": '[2., 3.]',
                    "EXPLORATION_STRATEGY": "INNER"},
                3: {"PARAMETER_NAME": 'SECOND_INNER_PARAM_COLUMN/INNER_PARAM_LINE',
                    "VALUES": '[12., 13.]',
                    "EXPLORATION_STRATEGY": "INNER"}
            }
        }

        expected_combination_results = [

            SystemModifierCombination([
                SystemModifier("FIRST_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 2.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 4.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 1.)
            ]),
            SystemModifierCombination([
                SystemModifier("FIRST_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 2.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 4.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 2.)
            ]),
            SystemModifierCombination([
                SystemModifier("FIRST_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 2.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 5.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 1.)
            ]),
            SystemModifierCombination([
                SystemModifier("FIRST_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 2.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 5.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 2.)
            ]),
            SystemModifierCombination([
                SystemModifier("FIRST_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 3.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 4.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 1.)
            ]),
            SystemModifierCombination([
                SystemModifier("FIRST_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 3.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 4.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 2.)
            ]),
            SystemModifierCombination([
                SystemModifier("FIRST_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 3.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 5.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 1.)
            ]),
            SystemModifierCombination([
                SystemModifier("FIRST_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 3.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 5.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 2.)
            ]),



            SystemModifierCombination([
                SystemModifier("SECOND_INNER_PARAM_COLUMN/INNER_PARAM_LINE",12.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 4.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 1.)
            ]),
            SystemModifierCombination([
                SystemModifier("SECOND_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 12.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 4.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 2.)
            ]),
            SystemModifierCombination([
                SystemModifier("SECOND_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 12.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 5.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 1.)
            ]),
            SystemModifierCombination([
                SystemModifier("SECOND_INNER_PARAM_COLUMN/INNER_PARAM_LINE",12.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 5.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 2.)
            ]),
            SystemModifierCombination([
                SystemModifier("SECOND_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 13.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 4.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 1.)
            ]),
            SystemModifierCombination([
                SystemModifier("SECOND_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 13.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 4.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 2.)
            ]),
            SystemModifierCombination([
                SystemModifier("SECOND_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 13.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 5.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 1.)
            ]),
            SystemModifierCombination([
                SystemModifier("SECOND_INNER_PARAM_COLUMN/INNER_PARAM_LINE", 13.),
                SystemModifier("FIRST_OUTER_PARAM_COLUMN/DUMBER", 5.),
                SystemModifier("SECOND_OUTER_PARAM_COLUMN/DUMBERFAILURE", 2.)
            ]),


            ]

        with patch.object(xlsx_utils, "read", return_value=sensitivity_analysis_dictionary):
            result = SensitivityAnalysisReader.generate_system_modifier_combination_list("fake_path")

        self.assertEqual(expected_combination_results, result)

    def test_read_exploration_strategy_list(self):
        sensitivity_analysis_dictionary = {
            'SENSITIVITY_ANALYSIS': {
                0: {"PARAMETER_NAME": 'COMPONENT_NUMBER/DUMBER',
                    "VALUES": '[4, 5]',
                    "EXPLORATION_STRATEGY": "OUTER"},
                1: {"PARAMETER_NAME": 'FAILURE_PARAMETERS/DUMBERFAILURE',
                    "VALUES": '[1., 2.]',
                    "EXPLORATION_STRATEGY": "OUTER"},
                2: {"PARAMETER_NAME": 'FAILURE_PARAMETERS/DUMBERFAILURE',
                    "VALUES": '[2., 3.]',
                    "EXPLORATION_STRATEGY": "INNER"}
            }
        }

        expected_value = [
            Outer('COMPONENT_NUMBER/DUMBER', [4, 5]),
            Outer('FAILURE_PARAMETERS/DUMBERFAILURE', [1., 2.]),
            Inner('FAILURE_PARAMETERS/DUMBERFAILURE', [2., 3.]),
        ]

        with patch.object(xlsx_utils, "read", return_value=sensitivity_analysis_dictionary):
            result = SensitivityAnalysisReader._read_exploration_strategy_list("fake_path")

        self.assertEqual(expected_value, result)
