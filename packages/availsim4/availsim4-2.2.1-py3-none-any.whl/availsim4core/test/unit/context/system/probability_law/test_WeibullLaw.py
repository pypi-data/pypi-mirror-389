# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for unit tests of the WeibullLaw class.
"""

import unittest

from availsim4core.src.context.system.probability_law.weibull_law import WeibullLaw

class test_WeibullLaw(unittest.TestCase):
    """
    Class with unit tests of the WeibullLaw class.
    """

    def test__eq__(self):
        """
        Tests of the equality function
        """
        weibull_1 = WeibullLaw([1, 0.5])
        weibull_2 = WeibullLaw([1, 0.5])
        weibull_3 = WeibullLaw([1, 0.5, 2])
        weibull_4 = WeibullLaw([0, 0.5])

        self.assertEqual(weibull_1, weibull_2)
        self.assertNotEqual(weibull_4, weibull_1)
        self.assertNotEqual(weibull_1, weibull_3)

    def test_get_random_value(self):
        """
        Tests of generating random values; for case with location parameter, it checks that values are indeed shifted
        """
        weibull_1 = WeibullLaw([1, 0.5])
        weibull_2 = WeibullLaw([1, 0.5, 10])

        self.assertTrue(weibull_1.get_random_value() > 0)
        self.assertTrue(weibull_2.get_random_value() > 10)

    def test_get_quantile_value(self):
        """
        Tests of the quantule value function
        """
        weibull_1 = WeibullLaw([1, 1])
        weibull_2 = WeibullLaw([1, 1, 10])

        self.assertAlmostEqual(weibull_1.get_quantile_value(0.5), 0.69314718)
        self.assertAlmostEqual(weibull_1.get_quantile_value(0.9), 2.30258509)
        self.assertAlmostEqual(weibull_2.get_quantile_value(0.5), 10.69314718)
        self.assertAlmostEqual(weibull_2.get_quantile_value(0.1), 10.10536051)

    def test_get_mean_value(self):
        """
        Tests of the function returning the mean value of the distribution
        """
        weibull_1 = WeibullLaw([5, 1])
        weibull_2 = WeibullLaw([5, 2.5])
        weibull_3 = WeibullLaw([1, 1, 10])

        self.assertAlmostEqual(weibull_1.get_mean_value(), 5.0)
        self.assertAlmostEqual(weibull_2.get_mean_value(), 4.43631909)
        self.assertAlmostEqual(weibull_3.get_mean_value(), 11.0)

    def test_get_variance_value(self):
        """
        Tests of the function returning variance
        """
        weibull_1 = WeibullLaw([2.5, 2])
        weibull_2 = WeibullLaw([1, 1, 10])

        self.assertAlmostEqual(weibull_1.get_variance_value(), 1.34126148)
        self.assertAlmostEqual(weibull_2.get_variance_value(), 1.0)


if __name__ == '__main__':
    unittest.main()
