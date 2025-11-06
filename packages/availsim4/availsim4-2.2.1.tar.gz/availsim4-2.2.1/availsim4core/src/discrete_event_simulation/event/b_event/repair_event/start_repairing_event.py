# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from __future__ import annotations

from typing import TYPE_CHECKING

from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEventPriority

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Basic

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.discrete_event_simulation.event.b_event.basic_b_event import BasicBEvent
from availsim4core.src.discrete_event_simulation.event.event import Event


class StartRepairingEvent(BasicBEvent):
    """
    Defines a Repair event.
    Attributes:
        - absolute_occurrence_time: date when the repair event will be started.
        - component: associate component to repair.
        - event: event which triggered this repair event.
    """
    __slots__ = 'event'

    def __init__(self,
                 absolute_occurrence_time: float,
                 context: Context,
                 basic: Basic,
                 event: Event):
        super().__init__(absolute_occurrence_time, context, basic,
                         BEventPriority.START_REPAIRING_EVENT)
        self.event = event

    def __hash__(self):
        return hash((type(self), self.absolute_occurrence_time, self.priority, self.basic, self.event))

    def __eq__(self, other):
        if not isinstance(other, StartRepairingEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.event == other.event

    def __str__(self):
        return (f"type ::{type(self)} "
                f"basic ::{self.basic.name}, "
                f"lid ::{self.basic.local_id}, "
                f"gid ::{self.basic.global_id}, "
                f"at t ::{self.absolute_occurrence_time} \n")

    def execute(self):
        return self.basic.update_status(Status.UNDER_REPAIR,
                                        self.absolute_occurrence_time,
                                        self.context.phase_manager.current_phase,  # or phase of the failure mode?
                                        f"UNDER REPAIR - component {self.basic.name}_{self.basic.local_id}_{self.basic.global_id}",
                                        self.context)
