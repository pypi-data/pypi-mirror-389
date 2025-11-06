# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Basic

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.discrete_event_simulation.event.b_event.basic_b_event import BasicBEvent


class FailureEvent(BasicBEvent):
    """
    Defines a failure event associated to a Component and a Failure Mode.
    """
    __slots__ = 'failure_mode'

    def __init__(self,
                 absolute_occurrence_time: float,
                 context: Context,
                 basic: Basic,
                 failure_mode: FailureMode,
                 priority):
        super().__init__(absolute_occurrence_time, context, basic, priority)
        self.failure_mode = failure_mode
        self.failure_mode.sample_generation_time = context.absolute_simulation_time

    def __hash__(self):
        return hash((type(self), self.absolute_occurrence_time, self.priority, self.basic, self.failure_mode))

    def __eq__(self, other):
        # TODO: when only one failure_mode is present in a basic, the comparison should not be on the failure mode anymore
        if not isinstance(other, type(self)):
            return NotImplemented
        return super().__eq__(other) and \
               self.failure_mode == other.failure_mode

    def __str__(self):
        return (f"type ::{type(self)} "
                f"basic ::{self.basic.name}, "
                f"lid ::{self.basic.local_id}, "
                f"gid ::{self.basic.global_id}, "
                f"at t ::{self.absolute_occurrence_time}, "
                f"FailureMode ::{self.failure_mode}\n")

    def is_context_valid(self):
        return self.context.phase_manager.current_phase in self.failure_mode.phase_set

    @staticmethod
    def _b_events_to_be_cleaned() -> List:
        from availsim4core.src.discrete_event_simulation.event.b_event.phase_event.next_phase_event import \
            NextPhaseEvent
        from availsim4core.src.discrete_event_simulation.event.b_event.phase_event.next_phase_if_failure_event import \
            NextPhaseIfFailureEvent
        from availsim4core.src.discrete_event_simulation.event.b_event.phase_event.jump_phase_event import \
            JumpPhaseEvent
        return [NextPhaseEvent, NextPhaseIfFailureEvent, JumpPhaseEvent]
