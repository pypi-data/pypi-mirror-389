# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.system.probability_law.deterministic_law import DeterministicLaw
from availsim4core.src.context.system.probability_law.exponential_law import ExponentialLaw
from availsim4core.src.context.system.probability_law.exponentiated_weibull_law import ExponentiatedWeibullLaw
from availsim4core.src.context.system.probability_law.normal_law import NormalLaw
from availsim4core.src.context.system.probability_law import probability_law_factory
from availsim4core.src.context.system.probability_law.probability_law_factory import ProbabilityLawFactoryError
from availsim4core.src.context.system.probability_law.weibull_law import WeibullLaw


class test_probabilityLawFactory(unittest.TestCase):

    def test_build_ExponentialLaw(self):
        distribution_str = "EXP"
        parameters = [1]
        result = probability_law_factory.build(distribution_str, parameters)
        self.assertEqual(ExponentialLaw([1]), result)

        distribution_str = "EXPONENTIAL"
        parameters = [2, 10]
        result = probability_law_factory.build(distribution_str, parameters)
        self.assertEqual(ExponentialLaw([2, 10]), result)
        self.assertNotEqual(ExponentialLaw([2, 5]), result)

    def test_build_NormalLaw(self):
        distribution_str = "NORMAL"
        parameters = [1]
        result = probability_law_factory.build(distribution_str, parameters)
        self.assertEqual(NormalLaw([1]), result)

    def test_build_WeibullLaw(self):
        distribution_str = "WEIBULL"
        parameters = [1, 2, 3]
        result = probability_law_factory.build(distribution_str, parameters)
        self.assertEqual(WeibullLaw([1, 2, 3]), result)

    def test_build_ExpWeibullLaw(self):
        distribution_str = "EW"
        parameters = [1, 2, 3, 4]
        result = probability_law_factory.build(distribution_str, parameters)
        self.assertEqual(ExponentiatedWeibullLaw([1, 2, 3, 4]), result)

    def test_build_DeterministicLaw(self):
        distribution_str = "FIX"
        parameters = []
        result = probability_law_factory.build(distribution_str, parameters)
        self.assertEqual(DeterministicLaw([]), result)

        distribution_str = "DETERMINISTIC"
        parameters = [2, 3]
        result = probability_law_factory.build(distribution_str, parameters)
        self.assertEqual(DeterministicLaw([2, 3]), result)

    def test_build_invalid_probability_law(self):
        distribution_str = "invalid"
        parameters = []
        with self.assertRaises(ProbabilityLawFactoryError) as context:
            probability_law_factory.build(distribution_str, parameters)
        self.assertTrue('wrong type of distribution function' in str(context.exception))
