# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for unit tests of the WeibullLaw class.
"""

import unittest
from availsim4core.src.context.system.probability_law.binomial_law import BinomialLaw
from availsim4core.src.context.system.probability_law.exponential_law import ExponentialLaw
from availsim4core.src.context.system.probability_law.exponentiated_weibull_law import ExponentiatedWeibullLaw
from availsim4core.src.context.system.probability_law.normal_law import NormalLaw

from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw

class test_ProbabilityLaw(unittest.TestCase):
    """
    Class with unit tests of the ProbabilityLaw class.
    """

    def _generate_values_for_seed(self, seed, generator_class, generator_parameters, n = 100):
        ProbabilityLaw.set_seed(seed)
        generator = generator_class(generator_parameters)
        return [generator.get_random_value() for _ in range(0, n)]

    def test_fixed_seed(self):
        """Test ensuding that a fixed seed always produceses same results"""
        tested_classes = [ExponentialLaw, BinomialLaw, NormalLaw, ExponentiatedWeibullLaw]
        tested_parameters = [[10], [0, 1], [1, 5], [1, 1, 1, 0]]

        for tested_class, tested_parameters in zip(tested_classes, tested_parameters):
            random_values_a = self._generate_values_for_seed(10, tested_class, tested_parameters)
            random_values_b = self._generate_values_for_seed(10, tested_class, tested_parameters)
            self.assertListEqual(random_values_a, random_values_b)


    def test_random_seed(self):
        """Test checking if `None` seed values translate into random seed"""
        tested_classes = [ExponentialLaw, BinomialLaw, NormalLaw, ExponentiatedWeibullLaw]
        tested_parameters = [[10], [0.5], [1, 5], [1, 1, 1, 0]]

        for tested_class, tested_parameters in zip(tested_classes, tested_parameters):
            random_values_a = self._generate_values_for_seed(None, tested_class, tested_parameters)
            random_values_b = self._generate_values_for_seed(None, tested_class, tested_parameters)
            self.assertNotEqual(random_values_a, random_values_b)

if __name__ == '__main__':
    unittest.main()
