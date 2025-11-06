# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from __future__ import annotations

from typing import TYPE_CHECKING, List

from availsim4core.src.context.context import Context
from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEventPriority
from availsim4core.src.discrete_event_simulation.event.b_event.held_event.end_holding_event import EndHoldingEvent
from availsim4core.src.discrete_event_simulation.event.c_event.held_event.order_end_holding_event import \
    OrderEndHoldingEvent

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Basic

from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.discrete_event_simulation.event.b_event.basic_b_event import BasicBEvent
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.blind_failure_event import \
    BlindFailureEvent
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.detectable_failure_event import \
    DetectableFailureEvent
from availsim4core.src.discrete_event_simulation.event.b_event.repair_event.end_repairing_event import EndRepairingEvent
from availsim4core.src.discrete_event_simulation.event.b_event.repair_event.start_repairing_event import \
    StartRepairingEvent
from availsim4core.src.discrete_event_simulation.event.c_event.failure_event.order_failure_event import \
    OrderFailureEvent
from availsim4core.src.discrete_event_simulation.event.c_event.repair_event.order_repair_event import OrderRepairEvent
from availsim4core.src.discrete_event_simulation.event.event import Event


class MinimalReplaceableUnitStartRepairingEvent(BasicBEvent):
    #TODO: maybe this event could be replaced by a normal start repairing event ?
    """
    Defines a Minimal Replaceable Unit Repair event.
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
                         BEventPriority.MRU_START_REPAIRING_EVENT)
        self.event = event

    def __hash__(self):
        return hash((type(self), self.absolute_occurrence_time, self.priority, self.basic, self.event))

    def __eq__(self, other):
        if not isinstance(other, MinimalReplaceableUnitStartRepairingEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.event == other.event

    def __str__(self):
        return (f"type ::{type(self)} "
                f"basic ::{self.basic.name}, "
                f"lid ::{self.basic.local_id}, "
                f"gid ::{self.basic.global_id}, "
                f"at t ::{self.absolute_occurrence_time} \n")

    @staticmethod
    def _b_events_to_be_cleaned() -> List:
        return [DetectableFailureEvent, BlindFailureEvent,
                EndRepairingEvent, StartRepairingEvent,
                EndHoldingEvent]

    @staticmethod
    def _c_events_to_be_cleaned() -> List:
        return [OrderRepairEvent, OrderFailureEvent, OrderEndHoldingEvent]

    def execute(self):
        return self.basic.update_status(Status.UNDER_REPAIR,
                                        self.absolute_occurrence_time,
                                        self.context.phase_manager.current_phase,  # or phase of the failure mode?
                                        f"mru ({self.event.mru.name}) UNDER REPAIR, " + \
                                        f"origin:{self.event.component.name} {self.event.component.global_id}",
                                        self.context)
