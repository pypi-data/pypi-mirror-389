# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.discrete_event_simulation.event.b_event.inspection_event.end_inspection_event import \
    EndInspectionEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.component_c_event import ComponentCEvent
from availsim4core.src.discrete_event_simulation.event.event import Event


class OrderEndInspectionEvent(ComponentCEvent):
    """
    class used to generate a C event, generating itself a B event. That final B event ends an inspection.
    """
    __slots__ = 'event', 'failure_mode'

    def __init__(self,
                 priority: CEventPriority,
                 context: Context,
                 component: Component,
                 event: Event,
                 failure_mode: FailureMode):
        super().__init__(priority, context, component)
        self.event = event
        self.failure_mode = failure_mode

    def __eq__(self, other):
        if not isinstance(self, OrderEndInspectionEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.event == other.event and \
               self.failure_mode == other.failure_mode

    def __hash__(self):
        return hash((type(self), self.priority, self.component, self.event, self.failure_mode))

    def __str__(self):
        return f"OrderEndInspectionEvent:: " \
               f"priority:{self.priority} - " \
               f"component:{self.component.name} - " \
               f"failure_mode:{self.failure_mode.name}"

    def generate_b_events(self, absolute_simulation_time):
        duration = self.failure_mode.inspection.duration
        # TODO: the inspection duration could take into account the actual duration of a repair, if a repair is needed

        event = EndInspectionEvent(absolute_simulation_time + duration,
                                   self.context,
                                   self.component,
                                   self.event,
                                   self.failure_mode)

        return set([event])
