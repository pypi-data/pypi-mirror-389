# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module containing logic of importance splitting method in AvailSim4.
"""

import copy
import logging
from datetime import datetime
from typing import List, Optional

from availsim4core.src.context.context import Context
from availsim4core.src.discrete_event_simulation.discrete_event_simulation import DiscreteEventSimulation
from availsim4core.src.results.simulation_results import SimulationResults
from availsim4core.src.simulation.monte_carlo import MonteCarlo
from availsim4core.src.statistics.critical_failure_paths import CriticalFailurePaths


class QueueTask:
        """
        Objects used to carry information in the importance splitting queue
        """

        def __init__(self, context: Context,
                     simulation_absolute_time: float,
                     simulation_weight: float,
                     simulation_level_threshold: float,
                     simulations_to_execute: int,
                     recursion_depth: int):
            self.context = context
            self.simulation_absolute_time = simulation_absolute_time
            self.simulation_weight = simulation_weight
            self.simulation_level_threshold = simulation_level_threshold
            self.simulations_to_execute = simulations_to_execute
            self.recursion_depth = recursion_depth

class SplittingMonteCarlo(MonteCarlo):
    """
    Defines a MonteCarlo simulation that will be triggered by the Sensitivity Analysis.
    Attributes:
    - minimum_number_of_simulations: minimun number of call to discrete event simulation.
    - maximum_number_of_simulations: maximun number of call to discrete event simulation.
    - convergence_margin: Evaluate on the fly the appropriate number of simulation to run.
    - maximum_execution_time: used on the Cluster to stop the simulation after this period of time.
    - seed: Control the random generator to get different values over each simulation. Deterministic
      approach.
    - list_of_diagnosis: Defines the metrics to compute.
    - result_simulation: The ResultSimulation to return.
    Extends the simulation, by implementing the run() method.
    """
    SIMULATION_TYPE = "SPLITTING_MONTE_CARLO"

    def __init__(self, minimum_number_of_simulations: int,
                 maximum_number_of_simulations: int,
                 convergence_margin: float,
                 maximum_execution_time: float,
                 seed: Optional[int],
                 list_of_diagnosis: List[str],
                 duration_of_simulation: float,
                 system_root_component_name: str):
        self.system_root_component_name = system_root_component_name
        super().__init__(minimum_number_of_simulations,
                         maximum_number_of_simulations,
                         convergence_margin,
                         maximum_execution_time,
                         seed,
                         list_of_diagnosis,
                         duration_of_simulation)

    def run(self, context: Context):
        """
        This method is running multiple iterations of the model and updating statistics according to
        the results. The function provides means to repeat partially completed timelines (when DES
        function returns a timeline which has not reached the user-defined simulation duration
        value). Since in the splitting method the number of model evaluations is not known and
        changes dynamically, the method is based on a queue which gathers information about
        consecutive repeated timelines.
        """
        simulation_results = SimulationResults(self.maximum_number_of_simulations,
                                               self.duration_of_simulation)

        # Those two parameters are for now hardcoded below. In the long run, they are to be
        # optionally defined by users or determined in an automatic way (adaptive execution, pilot
        # jobs, etc.).
        restarts_in_level = [10, 10, 10, 10]
        threshold = 1

        # Critical failure paths are used to establish the distance to a critical failure
        # inside the DES
        cfp = CriticalFailurePaths(context.root_component, self.system_root_component_name)

        start_time = datetime.now()
        logging.info(f"Starting a SPLITTING Monte Carlo simulation {0+1} / {self.maximum_number_of_simulations}")

        # Initialization of the queue with the parameters creating the first level (equivalent
        # to standard MC)
        initial_task = QueueTask(context, 0, 1/self.maximum_number_of_simulations, threshold,
                                      self.maximum_number_of_simulations, 0)
        queue: List[QueueTask] = [initial_task]

        evaluations_counter = 0
        while queue:
            # unpack the parameters for a given queue element
            current_task = queue[0]
            context = current_task.context
            simulation_absolute_time = current_task.simulation_absolute_time
            simulation_weight = current_task.simulation_weight
            level_threshold = current_task.simulation_level_threshold
            recursion_depth = current_task.recursion_depth

            # initialisation of a DES
            seed = self.seed + evaluations_counter if self.seed is not None else None
            simulation_des = DiscreteEventSimulation(seed,
                                                     self.duration_of_simulation,
                                                     copy.deepcopy(context),
                                                     cfp,
                                                     level_threshold,
                                                     simulation_absolute_time)

            # simulation
            context, simulation_absolute_time = simulation_des.run()

            if simulation_absolute_time < self.duration_of_simulation:
                # restarting
                new_task = QueueTask(copy.deepcopy(context),
                                          simulation_absolute_time,
                                          simulation_weight / restarts_in_level[recursion_depth+1],
                                          level_threshold + 1,
                                          restarts_in_level[recursion_depth+1],
                                          recursion_depth+1)
                queue.append(new_task)
            else:
                timeline_record = simulation_des.context.timeline_record

                # updating statistics
                self.update_statistics(simulation_results,
                                       simulation_des,
                                       simulation_weight,
                                       recursion_depth)

            evaluations_counter += 1
            current_task.simulations_to_execute -= 1
            if current_task.simulations_to_execute == 0:
                del queue[0]

        simulation_results.evaluate_result()
        simulation_results.last_simulation_timeline = timeline_record.record_list
        return simulation_results
