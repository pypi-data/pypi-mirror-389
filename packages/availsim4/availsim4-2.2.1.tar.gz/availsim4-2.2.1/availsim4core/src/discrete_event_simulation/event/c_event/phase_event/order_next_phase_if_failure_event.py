# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.discrete_event_simulation.event.b_event.phase_event.next_phase_if_failure_event import \
    NextPhaseIfFailureEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEvent, CEventPriority


class OrderNextPhaseIfFailureEvent(CEvent):
    """
    CEvent class in charge of creating a b_event {NextPhaseIfFailureEvent}.
    Note: The valid condition is based on the ROOT component of the system.
    # TODO removed the condition on the ROOT component. the condition should be recursive on any component of the system.
    """
    __slots__ = 'failure_mode'

    def __init__(self,
                 priority: CEventPriority,
                 context: Context,
                 failure_mode: FailureMode):
        super().__init__(priority, context)
        self.failure_mode = failure_mode

    def __eq__(self, other):
        if not isinstance(self, OrderNextPhaseIfFailureEvent):
            return NotImplemented
        return super().__eq__(other) and self.failure_mode == other.failure_mode

    def __hash__(self):
        return hash((type(self), self.priority, self.failure_mode))

    def __str__(self):
        return f"OrderNextPhaseIfFailureEvent:: " \
               f"priority:{self.priority} - " \
               f"failure_mode:{self.failure_mode.name}"

    def is_condition_valid(self):
        if self.failure_mode.phase_change_trigger in ["AFTER_REPAIR"]:
            return self.context.root_component.status == Status.RUNNING
        elif self.failure_mode.phase_change_trigger in ["AFTER_FAILURE"]:
            return True
        elif self.failure_mode.phase_change_trigger in ["NEVER"]:
            return False

    def generate_b_events(self, absolute_simulation_time):
        next_phase_time = absolute_simulation_time
        event = NextPhaseIfFailureEvent(next_phase_time,
                                        self.context,
                                        self.failure_mode)
        return {event}
