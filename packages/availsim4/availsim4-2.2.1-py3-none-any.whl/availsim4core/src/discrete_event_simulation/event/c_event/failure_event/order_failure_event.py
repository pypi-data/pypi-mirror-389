# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import logging
from typing import Optional

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.component_c_event import ComponentCEvent
from availsim4core.src.discrete_event_simulation.event.event import Event


class OrderFailureEvent(ComponentCEvent):
    """
    class used to generate C events themselves generating B events to handle failure events
    """
    __slots__ = 'event', 'failure_mode'

    def __init__(self,
                 priority: CEventPriority,
                 context: Context,
                 component: Component,
                 event: Optional[Event],
                 failure_mode: FailureMode):
        super().__init__(priority, context, component)
        self.event = event
        self.failure_mode = failure_mode

    def __eq__(self, other):
        if not isinstance(self, OrderFailureEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.event == other.event and \
               self.failure_mode == other.failure_mode

    def __hash__(self):
        return hash((type(self), self.priority, self.component, self.event, self.failure_mode))

    def __str__(self):
        return f"OrderFailureEvent:: " \
               f"priority:{self.priority} - " \
               f"component:{self.component.name} - " \
               f"failure_mode:{self.failure_mode.name}"

    def is_condition_valid(self):

        if not self.failure_mode.failure_law.is_failure_on_demand:
            # this failure mode is not a failure on demand, the next failure can be immediately ordered
            return True

        # if the code passes here, then the failure mode is of the type 'failure on demand'

        if self.context.phase_manager.current_phase not in self.failure_mode.phase_set:
            # this failure mode is a failure on demand BUT the system is not in the right phase
            return False

        if self.failure_mode.uniform_samples_for_quasi_monte_carlo:
            # the code uses Quasi Monte Carlo
            is_failing_now = self.failure_mode.failure_law.get_quantile_value(
                self.failure_mode.uniform_samples_for_quasi_monte_carlo.pop(0)
            )
            if not self.failure_mode.uniform_samples_for_quasi_monte_carlo:
                # if the list of predefined Quasi Monte Carlo samples is empty, display the information
                logging.info("The simulation is going from QMC to MC")
        else:
            # the code is not using Quasi Monte Carlo
            is_failing_now = self.failure_mode.failure_law.get_random_value()
        return is_failing_now

    def generate_b_events(self, absolute_simulation_time):


        if self.failure_mode.failure_law.is_failure_on_demand:
            time_to_fail = 0

        else:

            # -> uniform_samples_for_quasi_monte_carlo
            if self.failure_mode.uniform_samples_for_quasi_monte_carlo != []:
                time_to_fail = self.failure_mode.failure_law.get_quantile_value(
                    self.failure_mode.uniform_samples_for_quasi_monte_carlo.pop(0)
                )
                if not self.failure_mode.uniform_samples_for_quasi_monte_carlo:
                    logging.info("The simulation is going from QMC to MC")
            else:
                time_to_fail = self.failure_mode.failure_law.get_random_value()
        from availsim4core.src.discrete_event_simulation.event.b_event.failure_event import failure_event_factory
        event = failure_event_factory.build(
            absolute_simulation_time + time_to_fail,
            self.context,
            self.component,
            self.failure_mode
        )
        return {event}
