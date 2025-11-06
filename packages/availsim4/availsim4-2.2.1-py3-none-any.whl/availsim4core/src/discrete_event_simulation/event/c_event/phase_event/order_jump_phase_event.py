# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.phase_jump_trigger import PhaseJumpTrigger
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEvent, CEventPriority


class OrderJumpPhaseEvent(CEvent):
    """
    CEvent class in charge of creating a b_event {JumpPhaseEvent} if the jump conditions are satisfied.
    """
    def __init__(self,
                 priority: CEventPriority,
                 context: Context,
                 phase_jump_trigger: PhaseJumpTrigger):
        super().__init__(priority, context)
        self.phase_jump_trigger = phase_jump_trigger

    def __eq__(self, other):
        if not isinstance(self, OrderJumpPhaseEvent):
            return NotImplemented
        return super().__eq__(other) and \
            self.phase_jump_trigger == other.phase_jump_trigger

    def __hash__(self):
        return hash((type(self), self.priority, self.phase_jump_trigger))

    def __str__(self):
        return f"OrderJumpPhaseEvent:: " \
               f"priority:{self.priority}"

    def is_condition_valid(self):
        """
        The condition for the event to be valid in order to be processed.
        By default the value returned is True
        """
        for component in self.context.root_component.to_set():
            if (component.name == self.phase_jump_trigger.component_name and
                    component.status == self.phase_jump_trigger.component_status and
                    self.context.phase_manager.current_phase == self.phase_jump_trigger.from_phase and
                    self.context.phase_manager.current_phase != self.phase_jump_trigger.to_phase):
                        return True
        return False

    def generate_b_events(self, absolute_simulation_time):
        from availsim4core.src.discrete_event_simulation.event.b_event.phase_event.jump_phase_event import \
            JumpPhaseEvent
        jump_phase_time = absolute_simulation_time
        event = JumpPhaseEvent(jump_phase_time,
                               self.context,
                               self.phase_jump_trigger)
        return {event}
