# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest
from unittest.mock import patch
from availsim4core.src.reader.xlsx import xlsx_utils

from availsim4core.src.reader.xlsx.sensitivity_analysis_reader import SensitivityAnalysisReader
from availsim4core.src.sensitivity_analysis.exploration_strategy import Inner, Outer
from availsim4core.src.sensitivity_analysis.exploration_strategy_factory import ExplorationStrategyFactory, \
    SensitivityAnalysisStrategyError
from availsim4core.src.sensitivity_analysis.sensitivity_analysis import SensitivityAnalysis
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination_zip_strategy import \
    ZipStrategyError


class test_ExplorationStrategyFactory(unittest.TestCase):

    def test_build__inner(self):
        parameter_name = "param_test"
        float_values = [1., 2.]
        strategy = "iNner"
        expected_resut = Inner(parameter_name, float_values)

        result = ExplorationStrategyFactory.build(parameter_name,
                                                  float_values,
                                                  strategy)

        self.assertEqual(expected_resut, result)

    def test_build__outer(self):
        parameter_name = "param_test"
        float_values = [1., 2.]
        strategy = "oUter"
        expected_resut = Outer(parameter_name, float_values)

        result = ExplorationStrategyFactory.build(parameter_name,
                                                  float_values,
                                                  strategy)

        self.assertEqual(expected_resut, result)

    def test_build__exception(self):
        parameter_name = "param_test"
        float_values = [1., 2.]
        strategy = "random_name_to_raise_exception"

        self.assertRaises(SensitivityAnalysisStrategyError, ExplorationStrategyFactory.build,
                          parameter_name,
                          float_values,
                          strategy)

    def test_build__zip_construction_exception(self):

        sensitivity_analysis_dictionary = {'SENSITIVITY_ANALYSIS':
            {
                0: {"PARAMETER_NAME": 'COMPONENT_NUMBER/DUMBER',
                    "VALUES": f'[1, 2]',
                    "EXPLORATION_STRATEGY": "ZIP"},
                1: {"PARAMETER_NAME": 'FAILURE_PARAMETERS/DUMBERFAILURE',
                    "VALUES": f'[1, 2, 3]',
                    "EXPLORATION_STRATEGY": "ZIP"}
            }
        }

        with patch.object(xlsx_utils, "read", return_value=sensitivity_analysis_dictionary):
            sensitivity_analysis = SensitivityAnalysis(None,
                                                       None)

            self.assertRaises(ZipStrategyError, sensitivity_analysis.generate_analysis_list,
                                "fake_path")
