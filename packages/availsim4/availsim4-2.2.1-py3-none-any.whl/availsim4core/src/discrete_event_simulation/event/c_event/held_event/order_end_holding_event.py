# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from typing import Set

from availsim4core.src.context.context import Context
from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.discrete_event_simulation.event.b_event.held_event.end_holding_event import EndHoldingEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEvent
from availsim4core.src.discrete_event_simulation.event.c_event.component_c_event import ComponentCEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEventPriority
from availsim4core.src.discrete_event_simulation.event.event import Event


class OrderEndHoldingEvent(ComponentCEvent):
    """
    class used to generate C events themselves generating B events to handle failure events
    """
    __slots__ = 'event', 'failure_mode', 'held_event', 'held_until_phase_set'

    def __init__(self,
                 priority: CEventPriority,
                 context: Context,
                 component: Component,
                 event: Event,
                 failure_mode: FailureMode,
                 held_event: CEvent,
                 held_until_phase_set: Set[Phase]):
        super().__init__(priority, context, component)
        self.event = event
        self.failure_mode = failure_mode
        self.held_event = held_event
        self.held_until_phase_set = held_until_phase_set

    def __eq__(self, other):
        if not isinstance(self, OrderEndHoldingEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.event == other.event and \
               self.failure_mode == other.failure_mode and \
               self.held_event == other.held_event
        # no need for the held_until_phase_set because it's already implied by the failure mode

    def __hash__(self):
        return hash((type(self), self.priority, self.component, self.event, self.failure_mode, self.held_event))
        # no need for the held_until_phase_set because it's already implied by the failure mode

    def __str__(self):
        return f"OrderEndHoldingEvent:: " \
               f"priority:{self.priority} - " \
               f"component:{self.component.name} - " \
               f"failure_mode:{self.failure_mode.name}"

    def is_condition_valid(self):
        """
        The condition for the event to be valid in order to be processed.
        By default the value returned is True
        """
        return self.context.phase_manager.current_phase in self.held_until_phase_set

    def generate_b_events(self, absolute_simulation_time):
        return {EndHoldingEvent(absolute_simulation_time,
                                self.context,
                                self.component,
                                self.failure_mode,
                                self.held_event)}
