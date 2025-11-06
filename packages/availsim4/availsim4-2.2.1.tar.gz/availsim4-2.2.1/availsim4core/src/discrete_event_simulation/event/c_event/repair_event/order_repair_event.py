# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.discrete_event_simulation.event.b_event.repair_event.end_repairing_event import EndRepairingEvent
from availsim4core.src.discrete_event_simulation.event.b_event.repair_event.start_repairing_event import \
    StartRepairingEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.component_c_event import ComponentCEvent
from availsim4core.src.discrete_event_simulation.event.event import Event


class OrderRepairEvent(ComponentCEvent):
    """
    class used to regenerate all InspectionEvents at once, once they have all been executed
    C events are generated which themselves generate B events
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
        if not isinstance(self, OrderRepairEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.event == other.event and \
               self.failure_mode == other.failure_mode

    def __hash__(self):
        return hash((type(self), self.priority, self.component, self.event, self.failure_mode))

    def __str__(self):
        return f"OrderRepairEvent:: " \
               f"priority:{self.priority} - " \
               f"component:{self.component.name} - " \
               f"failure_mode:{self.failure_mode.name}"

    def generate_b_events(self, absolute_simulation_time):
        start_repairing_event = StartRepairingEvent(absolute_occurrence_time=absolute_simulation_time,
                                                    context=self.context,
                                                    basic=self.component,
                                                    event=self)

        end_repairing_event = EndRepairingEvent(
            absolute_occurrence_time=absolute_simulation_time + self.failure_mode.repair_law.get_random_value(),
            context=self.context,
            basic=self.component,
            event=self,
            failure_mode=self.failure_mode)

        return {start_repairing_event, end_repairing_event}
