# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from typing import Set

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.phase_jump_trigger import PhaseJumpTrigger
from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEventPriority
from availsim4core.src.discrete_event_simulation.event.b_event.phase_event.next_phase_event import NextPhaseEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEvent, CEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.phase_event.order_jump_phase_event import \
    OrderJumpPhaseEvent


class JumpPhaseEvent(NextPhaseEvent):
    """
    Class handling the change of phases
    """
    __slots__ = 'phase_jump_trigger'

    def __init__(self,
                 absolute_occurrence_time: float,
                 context: Context,
                 phase_jump_trigger: PhaseJumpTrigger):
        super().__init__(absolute_occurrence_time,context,
                         BEventPriority.JUMP_PHASE_EVENT)
        self.phase_jump_trigger = phase_jump_trigger

    def __hash__(self):
        return hash((type(self), self.absolute_occurrence_time, self.priority, self.phase_jump_trigger))

    def __eq__(self, other):
        if not isinstance(other, JumpPhaseEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.phase_jump_trigger == other.phase_jump_trigger

    def __str__(self):
        return (f"type ::{type(self)} "
                f"due to ::{self.phase_jump_trigger} "
                f"at t ::{self.absolute_occurrence_time} \n")

    def execute(self):

        records = [self.context.phase_manager.go_to_phase(
                self.absolute_occurrence_time,
                self.phase_jump_trigger.to_phase,
                f"Jump triggered by {self.phase_jump_trigger.component_name} "\
                f" with status {self.phase_jump_trigger.component_status} "\
                f" from phase {self.context.phase_manager.current_phase.name} "\
                f" to phase {self.phase_jump_trigger.to_phase.name}")]

        records.extend(self.context.add_record_of_each_component(
            self.absolute_occurrence_time,
            self.context.phase_manager.UPDATE_FOLLOWING_A_PHASE_CHANGE))

        return records

    def generate_c_event(self, **kwargs) -> Set:

        c_event_set = NextPhaseEvent.generate_c_event(self,**kwargs)

        #TODO regenerate only one c_event or all?

        c_event_set.add(
            OrderJumpPhaseEvent(
                priority=CEventPriority.ORDER_JUMP_PHASE_EVENT,
                context=self.context,
                phase_jump_trigger=self.phase_jump_trigger
            )
        )

        return c_event_set
