# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

import numpy as np
import qmcpy as qp

from availsim4core.src.simulation.des_random_generator.quasi_monte_carlo_generator import QuasiMonteCarloGenerator
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.failure import FailureType, Failure
from availsim4core.src.context.system.probability_law.exponential_law import ExponentialLaw

class test_QuasiMonteCarloGenerator(unittest.TestCase):

    def setUp(self):
        """
        setUp is a function called by the unit tester to initialize the class
        """
        simulation_duration = 1
        exponential_law_value = 1
        self.failure_mode_1 = FailureMode("test_run_1",
                                     ExponentialLaw([exponential_law_value]),
                                     ExponentialLaw([exponential_law_value]),
                                     Failure(FailureType.DETECTABLE),
                                     [],
                                     None,
                                     [],
                                     None,
                                     'NEVER',
                                     [])
        self.failure_mode_2 = FailureMode("test_run_2",
                                     ExponentialLaw([exponential_law_value]),
                                     ExponentialLaw([exponential_law_value]),
                                     Failure(FailureType.DETECTABLE),
                                     [],
                                     None,
                                     [],
                                     None,
                                     'NEVER',
                                     [])

        self.components_list = [Basic(1, "test_basic_1", 0, [], self.failure_mode_1, [], []),
                                Basic(2, "test_basic_2", 0, [], self.failure_mode_2, [], [])]
        self.qmc_generator = QuasiMonteCarloGenerator(self.components_list, simulation_duration, randomize=None, seed=0, graycode=True, multiplier=1)

    def test_generate_single_sample(self):
        expected_result_0 = qp.Sobol((6*1), randomize=None, seed=0, graycode=True).gen_samples(n_min=0, n_max=1)[0]
        expected_result_5 = qp.Sobol((6*1), randomize=None, seed=0, graycode=True).gen_samples(n_min=5, n_max=6)[0]
        expected_result_10 = qp.Sobol((6*1), randomize=None, seed=0, graycode=True).gen_samples(n_min=10, n_max=11)[0]

        np.testing.assert_almost_equal(self.qmc_generator.generate_single_sample(0), expected_result_0)
        np.testing.assert_almost_equal(self.qmc_generator.generate_single_sample(5), expected_result_5)
        np.testing.assert_almost_equal(self.qmc_generator.generate_single_sample(10),expected_result_10)

    def test_get_number_of_sample_failures(self):
        self.assertEqual(self.qmc_generator.get_number_of_sample_failures(), 3)

        # Empty components list
        result = QuasiMonteCarloGenerator([], 1).get_number_of_sample_failures()
        self.assertEqual(result, 0)

        # Components with and without failure modes
        qmc_gen = QuasiMonteCarloGenerator([Basic(1, "test_basic_1", 0, [], self.failure_mode_1, [], []),
                                            Basic(1, "test_basic_1", 0, [], self.failure_mode_1, [], [])], 3, multiplier=3)
        result = qmc_gen.get_number_of_sample_failures()
        self.assertEqual(result, 11)
        # Explanation: number of sample failures is the duration of simulation divided by the lowest mean time to fail defined in the system multiplied by
        # the multplier provided as the constructor argument.
        # In this case, the simulation duration is 3, the lowest MTTF is equal to 1 and the multiplier is equal to 3, therefore the expected result is 9.


    def test_set_uniform_samples_for_quasi_monte_carlo(self):
        sequence = [1, 2, 3, 4, 5, 6]
        self.qmc_generator.set_ttfs_of_failure_modes(sequence)

        self.assertEqual(self.components_list[0].failure_mode.uniform_samples_for_quasi_monte_carlo, [1,2,3])
        self.assertEqual(self.components_list[1].failure_mode.uniform_samples_for_quasi_monte_carlo, [4,5,6])
