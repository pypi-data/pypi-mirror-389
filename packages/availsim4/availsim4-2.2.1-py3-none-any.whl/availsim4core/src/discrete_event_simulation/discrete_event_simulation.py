# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import logging
from typing import Optional

from availsim4core.src.context.context import Context
from availsim4core.src.discrete_event_simulation.b_event_generator import BEventGenerator
from availsim4core.src.discrete_event_simulation.c_event_generator import CEventGenerator
from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEvent
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.failure_event import FailureEvent
from availsim4core.src.timeline.record_generator import RecordGenerator
from availsim4core.src.statistics.critical_failure_paths import CriticalFailurePaths
from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw


class DiscreteEventSimulation:
    """
    Implementation of the Discrete event simulation following the documentation :
    https://en.wikipedia.org/wiki/Discrete-event_simulation
    """
    __slots__ = 'seed', 'duration_of_simulation', 'context', 'execution_metrics', 'absolute_simulation_time', \
                'root_component_set', 'cfp_threshold', 'critical_failure_paths'

    def __init__(self,
                 seed: Optional[int],
                 duration_of_simulation: float,
                 context: Context,
                 cfp: CriticalFailurePaths = None,
                 cfp_threshold: float = 0.0,
                 time: float = 0):

        self.seed = seed
        self.duration_of_simulation = duration_of_simulation
        self.context = context

        self.execution_metrics = {
            "number_of_time_iterations": 0,
            "number_of_b_events_executed": 0,
            "number_of_c_events_executed": 0,
            "number_of_b_events_removed": 0,
            "number_of_c_events_removed": 0,
            "length_of_timeline_record":0,
        }

        self.absolute_simulation_time = time

        self.critical_failure_paths = cfp
        self.cfp_threshold = cfp_threshold

        self.root_component_set = self.context.root_component.to_set()

    def regenerate_events(self, b_events, absolute_simulation_time):
        """
        Whenever a timeline is restarted, exsting b_events are updated to create new timelines. Each event has a corresponding
        attribute defining its occurrence time (`absolute_occurrence_time`), which decides if and when the event takes place.
        This method iterated through all events provided in the argument and re-draws absolute_occurrence_time using the original
        sample_generation_time (in-simulation time when a given sample was created) in respect to which a new sample is created
        using appropriate failure laws and scale parameters.

        The condition checked for each re-drawn sample is that the event occurrs after the current simulation time (second argument,
        `absolute_simulation_time`). Otherwise, the events could be expected to take place before the event triggering the splitting,
        changing the timeline which is to be replicated.
        """

        new_b_events = set()
        for b_event in b_events:
            if isinstance(b_event, FailureEvent):
                proposed_random_adjustment = b_event.failure_mode.failure_law.get_quantile_value(ProbabilityLaw.random_number_generator.uniform())
                b_event.absolute_occurrence_time = b_event.failure_mode.sample_generation_time + proposed_random_adjustment
                while b_event.absolute_occurrence_time < absolute_simulation_time:
                    proposed_random_adjustment = b_event.failure_mode.failure_law.get_quantile_value(ProbabilityLaw.random_number_generator.uniform())
                    b_event.absolute_occurrence_time = b_event.failure_mode.sample_generation_time + proposed_random_adjustment
            new_b_events.add(b_event)
        return new_b_events

    def __eq__(self, other):
        return self.seed == other.seed and \
               self.duration_of_simulation == other.duration_of_simulation and \
               self.context == other.context and \
               self.execution_metrics == other.execution_metrics and \
               self.absolute_simulation_time == other.absolute_simulation_time and \
               self.b_events_set == other.b_events_set and \
               self.c_events_set == other.c_events_set and \
               self.root_component_set == other.root_component_set

    def run(self):
        """
        This method runs the three phase approach of the discrete simulation algorithm.
        The discrete event simulation runs step by step from event to event until it reaches
        the 'duration of simulation'.
        Note: each event is evaluated at a time. If several events are happening at the exact same time,
        they will be processed one by one.
        """

        ProbabilityLaw.set_seed(self.seed)

        logging.debug(f"Discrete event simulation iteration: {self.execution_metrics['number_of_time_iterations']}")
        logging.debug(f"Discrete event simulation absolute time: {self.absolute_simulation_time}")

        logging.debug(f"BEvents list: {self.context.b_events_set}")
        logging.debug(f"CEvents list: {self.context.c_events_set}")

        if not (self.context.b_events_set or self.context.c_events_set):
            # if b events set or c events set are both empty, then the simulation is starting from the beginning
            # and thus needs to initialize first events in the simulation
            init_record = RecordGenerator.get_initial_records(self.absolute_simulation_time,
                                                            self.context)
            self.context.timeline_record.record_list.extend(init_record)
            self.context.b_events_set = BEventGenerator.generate_first_events(self.absolute_simulation_time,
                                                                  self.context)
            self.context.c_events_set = CEventGenerator.generate_first_events(self.absolute_simulation_time,
                                                                  self.context)
            # first execution of c_events in order to generate some additional b_events
            self._execute_c_events()
        else:
            # when there are some b or c events, the simulation is not starting at the begininng, which means that we
            # are restarting inside another timeline
            self.context.b_events_set = self.regenerate_events(self.context.b_events_set, self.absolute_simulation_time)

        # reached_old_threshold = False

        while True:
            if not self.context.b_events_set:
                break

            if(self.cfp_threshold > 0.0):
                # when cfp_threshold is above 0.0, check the ISp thresholds and possibly trigger more branches of the simulation
                # - define failure_states_atm
                failure_states_atm_vector = self.critical_failure_paths.calculate_failures_atm_vector(self.root_component_set)

                # - calculate the failure_criticallity matrix
                failure_criticallity = self.critical_failure_paths.calculate_distance_to_critical_failure(failure_states_atm_vector)

                if(failure_criticallity >= self.cfp_threshold):
                    return self.context, self.absolute_simulation_time

            b_events_valid_context = {b_event
                                      for b_event in self.context.b_events_set
                                      if b_event.is_context_valid()}

            current_b_event = min(b_events_valid_context)

            self.absolute_simulation_time = current_b_event.absolute_occurrence_time

            if self.absolute_simulation_time > self.duration_of_simulation:
                break

            logging.debug(f"Current valid BEvent: {current_b_event}")

            self.execution_metrics['number_of_time_iterations'] += 1

            self._execute_b_events(b_events_valid_context)

            self._execute_c_events()

        self.execution_metrics["length_of_timeline_record"]=len(self.context.timeline_record.record_list)
        return self.context, self.absolute_simulation_time

    def _execute_b_events(self, b_events_valid_context):
        """
        Manage the all the simultaneous B events.
        For each of the b_events_set, it tests if the b_event is happening at the current time.
        """
        b_events_simultaneous = {b_event
                                 for b_event in b_events_valid_context
                                 if b_event.absolute_occurrence_time == self.absolute_simulation_time}

        logging.debug(f"Simultaneous BEvent list: {b_events_simultaneous}")
        for b_event in sorted(b_events_simultaneous):
            if b_event in self.context.b_events_set:
                self._execute_b_event(b_event)

        self.context.b_events_set = self.context.b_events_set - b_events_simultaneous

    def _execute_b_event(self, b_event: BEvent):
        """
        Given a b_event, this method:
         - update the component status (and propagate the status)
         - update the occurrence time of the for each component of the b_event_list
         - generate a list of c_event related to the current b_event and update the c_event_set.
        :param b_event: The b_event to execute.
        """

        logging.debug(f"Executed BEvent: {b_event}")
        record_list = b_event.execute()
        self.execution_metrics['number_of_b_events_executed'] += 1
        logging.debug(f"Records list: {record_list}")
        self.context.timeline_record.add_records(record_list, self.seed)

        self.context.b_events_set, b_event_removed_set = b_event.update_b_event_collection(
            self.context.b_events_set,
            b_event._b_events_to_be_cleaned()
        )

        self.execution_metrics["number_of_b_events_removed"]+=len(b_event_removed_set)

        self.context.c_events_set, c_event_removed_set = b_event.update_c_event_collection(
            self.context.c_events_set,
            b_event._c_events_to_be_cleaned()
        )

        self.execution_metrics["number_of_c_events_removed"]+=len(c_event_removed_set)

        new_c_event_set = b_event.generate_c_event(b_event_removed_set=b_event_removed_set)

        logging.debug("Generated CEvent list: %s", new_c_event_set)

        self.context.c_events_set.update(new_c_event_set)

    def _execute_c_events(self):
        """
        Manage the C events.
        For each of the c_events_list, it tests if the condition is valid and apply it.
        If the result of this valid c_event generates b_event, then the b_event_list is updated and sorted accordingly.
        """
        valid_c_events = {event
                          for event in self.context.c_events_set
                          if event.is_condition_valid()}

        for valid_c_event in sorted(valid_c_events):
            logging.debug(f"Executed CEvent with condition valid: {valid_c_event}")
            new_b_events_set = valid_c_event.generate_b_events(self.absolute_simulation_time)
            self.execution_metrics['number_of_c_events_executed'] += 1
            logging.debug(f"Generated BEvents: {new_b_events_set}")
            self.context.b_events_set.update(new_b_events_set)

        self.context.c_events_set = self.context.c_events_set - valid_c_events
