# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.


import copy
import math
import logging
from datetime import datetime
from typing import List, Optional

from availsim4core.src.context.context import Context
from availsim4core.src.discrete_event_simulation.discrete_event_simulation import DiscreteEventSimulation
from availsim4core.src.results.simulation_results import SimulationResults
from availsim4core.src.simulation.simulation import Simulation


class MonteCarlo(Simulation):
    """
    Defines a MonteCarlo simulation that will be triggered by the Sensitivity Analysis.

    Attributes:
        minimum_number_of_simulations:
            Minimun number of call to discrete event simulation.
        maximum_number_of_simulations:
            Maximun number of call to discrete event simulation.
        convergence_margin:
            Evaluate on the fly the appropriate number of simulation to run.
        maximum_execution_time:
            Used on the Cluster to stop the simulation after this period of time.
        seed:
            Control the random generator to get different values over each simulation. Deterministic approach.
        list_of_diagnosis:
            Defines the metrics to compute.
        duration_of_simulation:
            Total time of system's simulated lifetime.
        simulation_results:
            The ResultSimulation to return.

    Extends the simulation, by implementing the run() method.
    """
    SIMULATION_TYPE = "MONTE_CARLO"

    def __init__(self,
                 minimum_number_of_simulations: int,
                 maximum_number_of_simulations: int,
                 convergence_margin: float,
                 maximum_execution_time: float,
                 seed: Optional[int],
                 list_of_diagnosis: List[str],
                 duration_of_simulation: float,
                 number_of_exporting_stages: int = 1):
        self.minimum_number_of_simulations = minimum_number_of_simulations
        self.maximum_number_of_simulations = maximum_number_of_simulations
        self.convergence_margin = convergence_margin
        self.maximum_execution_time = maximum_execution_time
        self.seed = seed
        self.list_of_diagnosis = list_of_diagnosis
        self.duration_of_simulation = duration_of_simulation

        self.simulation_results = SimulationResults(self.maximum_number_of_simulations, self.duration_of_simulation)
        self._number_of_iterations_per_run = math.ceil(maximum_number_of_simulations / number_of_exporting_stages)
        self._current_iteration = 0

    def __str__(self):
        return f"{self.SIMULATION_TYPE}:: " \
               f"minimum_number_of_simulations: {self.minimum_number_of_simulations} - " \
               f"maximum_number_of_simulations: {self.maximum_number_of_simulations} - " \
               f"maximum_execution_time: {self.maximum_execution_time} - " \
               f"diagnostics: {self.list_of_diagnosis} - " \
               f"seed: {self.seed} - " \
               f"duration_of_simulation: {self.duration_of_simulation}"

    def __eq__(self, other):
        return self.minimum_number_of_simulations == other.minimum_number_of_simulations \
               and self.maximum_number_of_simulations == other.maximum_number_of_simulations \
               and self.convergence_margin == other.convergence_margin \
               and self.maximum_execution_time == other.maximum_execution_time \
               and self.seed == other.seed \
               and self.list_of_diagnosis == other.list_of_diagnosis \
               and self.duration_of_simulation == other.duration_of_simulation

    def update_statistics(self, simulation_results: SimulationResults, simulation_des: DiscreteEventSimulation,
                          simulation_weight: float, simulation_level: int) -> None:
        """
        Function to update SimulationResults object with statistics of the finished run. It is called after each
        iteration of the Monte Carlo algorithm to update the statistics incrementally.

        Args:
            simulation_results:
                SimulationResults object which contains statistics of already completed stages. It is modified in this
                function.
            simulation_des:
                Individual DiscreteEventSimulation object which is the simulation iteration which statistics are
                supposed to be added to the SimulationResults object.
            simulation_weight:
                Parameter used to weight results for averaging.
            simulation_level:
                Used in tracking how many times the simulation was executed. Supports multi-level execution (for
                importance splitting, where simulations not equal to each other)

        Returns:
            None, the function changes the SimulationResults object passed as the first argument.
        """
        simulation_results.update_with_des_results(simulation_des.execution_metrics,
                                        simulation_des.context.timeline_record,
                                        simulation_weight)
        if simulation_des.context.timeline_record.rca_manager:
            simulation_results.root_cause_analysis_records.extend(simulation_des.context.timeline_record.rca_manager.root_cause_analysis_records)
        if simulation_level not in simulation_results.number_of_DES_simulations_executed:
            simulation_results.number_of_DES_simulations_executed[simulation_level] = 0
        simulation_results.number_of_DES_simulations_executed[simulation_level] += 1

    def run(self, context: Context):
        max_iteration_of_the_run = min(self._current_iteration + self._number_of_iterations_per_run,
                                       self.minimum_number_of_simulations)
        for simulation_index in range(self._current_iteration, max_iteration_of_the_run):
            start_time = datetime.now()
            logging.info("Starting Monte Carlo simulation %d / %d", simulation_index+1,
                         self.maximum_number_of_simulations)

            local_context = copy.deepcopy(context)
            seed = self.seed + simulation_index if self.seed is not None else None

            # initialisation of a DES
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

    def get_list_of_diagnosis(self):
        return self.list_of_diagnosis
