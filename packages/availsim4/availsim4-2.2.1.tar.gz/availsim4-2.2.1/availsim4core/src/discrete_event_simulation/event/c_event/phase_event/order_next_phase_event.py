# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.context import Context
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEvent, CEventPriority


class OrderNextPhaseEvent(CEvent):
    """
    CEvent class in charge of creating a BEvent {NextPhaseEvent}.
    """

    def __init__(self,
                 priority: CEventPriority,
                 context: Context):
        super().__init__(priority, context)

    def __eq__(self, other):
        if not isinstance(self, OrderNextPhaseEvent):
            return NotImplemented
        return super().__eq__(other)

    def __hash__(self):
        return hash((type(self), self.priority))

    def __str__(self):
        return f"OrderNextPhaseEvent:: " \
               f"priority:{self.priority}"

    def generate_b_events(self, absolute_simulation_time):
        from availsim4core.src.discrete_event_simulation.event.b_event.phase_event.next_phase_event import \
            NextPhaseEvent
        next_phase_time = absolute_simulation_time + self.context.phase_manager.current_phase.law.get_random_value()
        event = NextPhaseEvent(next_phase_time,
                               self.context)
        return {event}
