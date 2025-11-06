# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import copy
import logging
from datetime import datetime

from availsim4core.src.context.context import Context
from availsim4core.src.discrete_event_simulation.discrete_event_simulation import DiscreteEventSimulation
from availsim4core.src.simulation.monte_carlo import MonteCarlo
from availsim4core.src.simulation.des_random_generator.quasi_monte_carlo_generator import QuasiMonteCarloGenerator

from availsim4core.src.context.system.component_tree.basic import Basic


class QuasiMonteCarlo(MonteCarlo):
    """
    Defines a MonteCarlo simulation that will be triggered by the Sensitivity Analysis.
    Attributes:
    - minimum_number_of_simulations: minimun number of call to discrete event simulation.
    - maximum_number_of_simulations: maximun number of call to discrete event simulation.
    - convergence_margin: Evaluate on the fly the appropriate number of simulation to run.
    - maximum_execution_time: used on the Cluster to stop the simulation after this period of time.
    - seed: Control the random generator to get different values over each simulation. Deterministic approach.
    - list_of_diagnosis: Defines the metrics to compute.
    - result_simulation: The ResultSimulation to return.
    Extends the simulation, by implementing the run() method.
    """
    SIMULATION_TYPE = "QUASI_MONTE_CARLO"

    def run(self, context: Context):
        basic_components = [component for component in context.root_component.to_set() if isinstance(component, Basic)]
        qp_sobol = QuasiMonteCarloGenerator(basic_components, self.duration_of_simulation)
        qp_sobol_samples = qp_sobol.generate_samples(self.seed, self.seed+self.maximum_number_of_simulations)

        max_iteration_of_the_run = min(self._current_iteration + self._number_of_iterations_per_run,
                                       self.minimum_number_of_simulations)
        for simulation_index in range(self._current_iteration, max_iteration_of_the_run):
            start_time = datetime.now()
            logging.info("Starting Quasi-Monte Carlo simulation %d / %d", simulation_index+1,
                         self.maximum_number_of_simulations)

            random_sequence = qp_sobol_samples[simulation_index]
            qp_sobol.set_ttfs_of_failure_modes(random_sequence)

            local_context = copy.deepcopy(context)

            # initialisation of a DES
            seed = self.seed + simulation_index if self.seed is not None else None
            simulation_des = DiscreteEventSimulation(seed,
                                                     self.duration_of_simulation,
                                                     local_context, None, -1 , 0)

            # simulation
            _, _ = simulation_des.run()
            timeline_record = local_context.timeline_record

            # updating statistics
            self.update_statistics(self.simulation_results, simulation_des, 1, 0)

        self.simulation_results.maximum_number_of_simulations = max_iteration_of_the_run
        self.simulation_results.evaluate_result(max_iteration_of_the_run)
        self.simulation_results.last_simulation_timeline = timeline_record.record_list
        self.simulation_results.execution_time = (datetime.now() - start_time).total_seconds()
        self._current_iteration = max_iteration_of_the_run
        return self.simulation_results
