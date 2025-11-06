# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.component_c_event import ComponentCEvent
from availsim4core.src.discrete_event_simulation.event.event import Event


class ReevaluateOrderAllFailureEvent(ComponentCEvent):
    """
    class used to regenerate all FailureEvents at once, once they have all been executed
    C events are generated which themselves generate B events
    """
    __slots__ = 'event'

    def __init__(self,
                 priority: CEventPriority,
                 context: Context,
                 component: Component,
                 event: Event):
        super().__init__(priority, context, component)
        self.event = event

    def __eq__(self, other):
        if not isinstance(self, ReevaluateOrderAllFailureEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.event == other.event

    def __hash__(self):
        return hash((type(self), self.priority, self.component, self.event))

    def __str__(self):
        return f"ReevaluateOrderAllFailureEvent:: " \
               f"priority:{self.priority} - " \
               f"component:{self.component.name}"

    def generate_b_events(self, absolute_simulation_time):
        from availsim4core.src.discrete_event_simulation.b_event_generator import BEventGenerator
        return BEventGenerator.get_b_events_failure(absolute_simulation_time,
                                                    self.context,
                                                    self.component)
