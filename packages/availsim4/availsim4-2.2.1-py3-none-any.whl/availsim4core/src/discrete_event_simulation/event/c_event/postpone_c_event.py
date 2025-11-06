# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.context import Context
from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEvent, CEventPriority


class PostponeCEvent(CEvent):
    """
    Class dealing with C events used to postpone some events, for example when using phases
    """
    __slots__ = 'postpone_duration', 'b_event'

    def __init__(self,
                 priority: CEventPriority,
                 context: Context,
                 postpone_duration: float,
                 b_event: BEvent):
        super().__init__(priority, context)
        self.postpone_duration = postpone_duration
        self.b_event = b_event

    def __hash__(self):
        return hash((type(self), self.priority, self.postpone_duration, self.b_event))

    def __eq__(self, other):
        if not isinstance(self, PostponeCEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.postpone_duration == other.postpone_duration and \
               self.b_event == other.b_event

    def __str__(self):
        return f"PostponeCEvent:: " \
               f"priority:{self.priority} - " \
               f"postpone_duration:{self.postpone_duration} - " \
               f"b_event:{self.b_event}"

    def generate_b_events(self, absolute_simulation_time):
        return {self.b_event.postpone(self.postpone_duration)}
