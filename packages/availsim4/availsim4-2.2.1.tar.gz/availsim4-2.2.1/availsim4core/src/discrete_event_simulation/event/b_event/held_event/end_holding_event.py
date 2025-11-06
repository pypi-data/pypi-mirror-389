# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from __future__ import annotations

from typing import TYPE_CHECKING, Set

from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEventPriority, CEvent
from availsim4core.src.discrete_event_simulation.event.c_event.failure_event.order_failure_event import \
    OrderFailureEvent

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Basic

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.discrete_event_simulation.event.b_event.basic_b_event import BasicBEvent


class EndHoldingEvent(BasicBEvent):
    """
    A component can be held in an "HELD" status after being repaired. The EndHoldingEvent put back the component into a
    RUNNING status.
    """
    __slots__ = 'failure_mode','held_event'

    def __init__(self,
                 absolute_occurrence_time: float,
                 context: Context,
                 basic: Basic,
                 failure_mode: FailureMode,
                 held_event: CEvent):
        super().__init__(absolute_occurrence_time, context, basic,
                         priority=BEventPriority.END_HOLDING_EVENT)
        self.failure_mode = failure_mode
        self.held_event = held_event

    def __hash__(self):
        return hash((type(self), self.absolute_occurrence_time, self.priority, self.basic, self.failure_mode,
                     self.held_event))

    def __eq__(self, other):
        if not isinstance(other, EndHoldingEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.failure_mode == other.failure_mode and \
               self.held_event == other.held_event

    def __str__(self):
        return (f"type ::{type(self)} "
                f"basic ::{self.basic.name}, "
                f"lid ::{self.basic.local_id}, "
                f"gid ::{self.basic.global_id}, "
                f"at t ::{self.absolute_occurrence_time}, "
                f"FailureMode ::{self.failure_mode}\n")

    def execute(self):
        if isinstance(self.held_event,OrderFailureEvent):
            return self.basic.update_status(Status.RUNNING,
                                        self.absolute_occurrence_time,
                                        self.context.phase_manager.current_phase,  # or phase of the failure mode?!
                                        f"{self.failure_mode.name} end holding of component {self.basic.name}_{self.basic.local_id}_{self.basic.global_id}",
                                        self.context)
        else:
            return []

    def generate_c_event(self, **kwargs) -> Set[CEvent]:
        return {self.held_event}
