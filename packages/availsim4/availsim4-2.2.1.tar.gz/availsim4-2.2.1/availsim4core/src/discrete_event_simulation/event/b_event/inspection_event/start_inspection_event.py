# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for StartInspectionEvent class
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Set

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.discrete_event_simulation.event.b_event.b_event import \
    BEventPriority
from availsim4core.src.discrete_event_simulation.event.b_event.basic_b_event import \
    BasicBEvent
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.blind_failure_event import \
    BlindFailureEvent
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.detectable_failure_event import \
    DetectableFailureEvent
from availsim4core.src.discrete_event_simulation.event.b_event.held_event.end_holding_event import \
    EndHoldingEvent
from availsim4core.src.discrete_event_simulation.event.b_event.repair_event.end_repairing_event import \
    EndRepairingEvent
from availsim4core.src.discrete_event_simulation.event.b_event.repair_event.start_repairing_event import \
    StartRepairingEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import (
    CEvent, CEventPriority)
from availsim4core.src.discrete_event_simulation.event.c_event.inspection_event.order_end_inspection_event import \
    OrderEndInspectionEvent

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Basic


class StartInspectionEvent(BasicBEvent):
    """
    Defines the Start of an inspection event.
    Attributes:
        - absolute_occurrence_time: date when the inspection event will be started.
        - context
        - basic: component to inspect.
        - failure_mode: failure mode which triggered this inspection event.
    """
    __slots__ = ['failure_mode']

    def __init__(self,
                 absolute_occurrence_time: float,
                 context: Context,
                 basic: Basic,
                 failure_mode: FailureMode):
        super().__init__(absolute_occurrence_time, context, basic,
                         priority=BEventPriority.START_INSPECTION_EVENT)
        self.failure_mode = failure_mode

    def __hash__(self):
        return hash((type(self),
                     self.absolute_occurrence_time,
                     self.priority,
                     self.basic,
                     self.failure_mode))

    def __eq__(self, other):
        if not isinstance(other, StartInspectionEvent):
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

    def execute(self):
        return self.basic.update_status(Status.INSPECTION,
                                        self.absolute_occurrence_time,
                                        self.context.phase_manager.current_phase,  # or phase of the failure mode?
                                        "INSPECTION",
                                        self.context)

    @staticmethod
    def _b_events_to_be_cleaned() -> List:
        return [DetectableFailureEvent, BlindFailureEvent,
                StartRepairingEvent, EndRepairingEvent,
                EndHoldingEvent]

    def generate_c_event(self, **kwargs) -> Set[CEvent]:
        return {
            OrderEndInspectionEvent(
                priority=CEventPriority.ORDER_END_INSPECTION_EVENT,
                context=self.context,
                component=self.basic,
                event=self,
                failure_mode=self.failure_mode
            )
        }
