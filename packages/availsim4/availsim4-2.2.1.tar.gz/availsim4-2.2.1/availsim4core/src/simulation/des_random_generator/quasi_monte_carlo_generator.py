# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import logging
from availsim4core.src.simulation.des_random_generator.des_random_generator import DESRandomGenerator

try:
    import qmcpy
except ImportError:
    logging.warning("Impossible to import the library qmcpy which is needed to Quasi-Monte Carlo simulations")

class QuasiMonteCarloGenerator(DESRandomGenerator):
    qmcNotApplicable = ["DeterministicLaw"]
    qmcpy_sobol_d_max = 21201

    def __init__(self, basic_components, duration_of_simulation, multiplier = 10, randomize="LMS_DS", seed=None, graycode=True) -> None:
        self.basic_components = basic_components
        self.failure_modes = [component.failure_mode
                              for component in basic_components
                              if self.is_qmc_applicable(component.failure_mode.failure_law)]

        self.n_failure_modes = len(self.failure_modes)
        self.n_sample_failures = 0
        self.n_dimensions = 0

        try:
            # TODO: Improve n_sample_failures estimation (add inspection MTTFs as well, etc.)
            self.n_sample_failures = int(2 + multiplier * (duration_of_simulation / min([component.failure_mode.failure_law.get_mean_value()
                                                                                    for component in basic_components
                                                                                    if component.failure_mode])))
            self.n_dimensions = self.n_failure_modes * self.n_sample_failures
        except IndexError:
            logging.warning(f"Quasi-Monte Carlo random number generator initiated for components without failure modes")
        except ValueError:
            logging.warning(f"Quasi-Monte Carlo random number generator initiated for an empty list of components")

        # QMCPy package has a limit on the number of dimensions, so when their number is too high, the number of low-discrepancy samples has to be limited.
        if self.n_dimensions > self.qmcpy_sobol_d_max:
            self.n_dimensions = self.qmcpy_sobol_d_max
            self.n_sample_failures = self.n_dimensions // self.n_failure_modes

        self.sobol = qmcpy.Sobol((self.n_dimensions), randomize=randomize, seed=seed, graycode=graycode)

    def generate_single_sample(self, n_min):
        return self.sobol.gen_samples(n_min=n_min, n_max=n_min + 1)[0]

    def generate_samples(self, n_min, n_max):
        return self.sobol.gen_samples(n_min=n_min, n_max=n_max)

    def get_number_of_sample_failures(self):
        return self.n_sample_failures

    def set_ttfs_of_failure_modes(self, random_sequence):
        affected_failure_modes_counter = 0
        for failure_mode in self.failure_modes:
            part_of_the_random_seq = random_sequence[affected_failure_modes_counter*self.n_sample_failures:(affected_failure_modes_counter+1)*self.n_sample_failures].copy()
            failure_mode.set_uniform_samples_for_quasi_monte_carlo(part_of_the_random_seq)
            affected_failure_modes_counter += 1

    def is_qmc_applicable(self, failure_law):
        return not(failure_law.name in self.qmcNotApplicable)
