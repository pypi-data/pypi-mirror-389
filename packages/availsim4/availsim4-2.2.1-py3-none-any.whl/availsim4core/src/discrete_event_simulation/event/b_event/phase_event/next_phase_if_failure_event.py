# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.context import Context
from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEventPriority
from availsim4core.src.discrete_event_simulation.event.b_event.phase_event.next_phase_event import NextPhaseEvent
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.failure_mode import FailureMode


class NextPhaseIfFailureEvent(NextPhaseEvent):
    """
    event class that is in charge of switching Phases when a failure occurs.
    """
    __slots__ = 'failure_mode'

    def __init__(self,
                 absolute_occurrence_time: float,
                 context: Context,
                 failure_mode: FailureMode):

        if failure_mode.failure_mode_next_phase_if_failure is None:
            priority = BEventPriority.NEXT_PHASE_IF_FAILURE_EVENT
        else:
            priority = BEventPriority.NEXT_PHASE_IF_SPECIFIC_FAILURE_EVENT

        super().__init__(absolute_occurrence_time,
                         context,
                         priority)
        self.failure_mode = failure_mode

    def __hash__(self):
        return hash((type(self), self.absolute_occurrence_time, self.priority, self.failure_mode))

    def __eq__(self, other):
        if not isinstance(other, NextPhaseIfFailureEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.failure_mode == other.failure_mode

    def __str__(self):
        return (f"type ::{type(self)} "
                f"due to ::{self.failure_mode} "
                f"at t ::{self.absolute_occurrence_time}\n")

    def execute(self):
        if self.failure_mode.failure_mode_next_phase_if_failure is None:
            records = [self.context.phase_manager.go_to_phase(
                self.absolute_occurrence_time,
                self.context.phase_manager.current_phase.next_phase_if_failure,
                PhaseManager.DEFAULT_PHASE_IF_FAILURE_DESCRIPTION)]
        else:
            records = [self.context.phase_manager.go_to_phase(
                self.absolute_occurrence_time,
                self.failure_mode.failure_mode_next_phase_if_failure,
                PhaseManager.SPECIFIC_PHASE_IF_FAILURE_DESCRIPTION)]
        records.extend(self.context.add_record_of_each_component(
            self.absolute_occurrence_time,
            self.context.phase_manager.UPDATE_FOLLOWING_A_PHASE_CHANGE))
        return records
