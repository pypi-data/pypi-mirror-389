# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from __future__ import annotations

from typing import TYPE_CHECKING, Set

from availsim4core.src.discrete_event_simulation.c_event_generator import CEventGenerator
from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEventPriority

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Basic

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.discrete_event_simulation.event.b_event.basic_b_event import BasicBEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEvent, CEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.inspection_event.reevaluate_order_all_inspection_event import \
    ReevaluateOrderAllInspectionEvent
from availsim4core.src.discrete_event_simulation.event.event import Event


class EndInspectionEvent(BasicBEvent):
    """
    Defines the End of an inspection event.
    Attributes:
        - absolute_occurrence_time: date when the inspection event will be started.
        - component: associate component to inspect.
        - event: root event generating the EndInspectionEvent
        - failure_mode: failure mode which triggered this inspection event.
    """
    __slots__ = 'failure_mode', 'event'

    def __init__(self,
                 absolute_occurrence_time: float,
                 context: Context,
                 basic: Basic,
                 event: Event,
                 failure_mode: FailureMode):
        super().__init__(absolute_occurrence_time, context, basic,
                         priority=BEventPriority.END_INSPECTION_EVENT)
        self.event = event
        self.failure_mode = failure_mode

    def __hash__(self):
        return hash((type(self), self.absolute_occurrence_time, self.priority, self.basic, self.failure_mode,
                     self.event))

    def __eq__(self, other):
        if not isinstance(other, EndInspectionEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.failure_mode == other.failure_mode and \
               self.event == other.event

    def __str__(self):
        return (f"type ::{type(self)} "
                f"basic ::{self.basic.name}, "
                f"lid ::{self.basic.local_id}, "
                f"gid ::{self.basic.global_id}, "
                f"at t ::{self.absolute_occurrence_time}, "
                f"FailureMode ::{self.failure_mode}\n")

    def execute(self):
        return self.basic.update_status(Status.RUNNING,
                                        self.absolute_occurrence_time,
                                        self.context.phase_manager.current_phase,  # or phase of the failure mode?
                                        "EndInspectionEvent",
                                        self.context)

    def generate_c_event(self, **kwargs) -> Set[CEvent]:
        """
        function which parses the list of C events and updates it:
        when an inspection is performed, the C events related to a given (component - failure mode)
        have to be removed, only the next inspection has to be ordered again
        In StartInspectionEvent we remove those events.
        In EndInspectionEvent we generate new ones.
        """

        set_of_c_events = set()

        set_of_c_events.update(
            CEventGenerator.get_c_events_for_failures(
                self.absolute_occurrence_time,
                self.context,
                self.basic
            )
        )

        set_of_c_events.add(
            ReevaluateOrderAllInspectionEvent(
                priority=CEventPriority.REEVALUATE_ORDER_ALL_INSPECTION_EVENTS,
                context=self.context,
                component=self.basic,
                event=self.event
            )
        )

        return set_of_c_events
