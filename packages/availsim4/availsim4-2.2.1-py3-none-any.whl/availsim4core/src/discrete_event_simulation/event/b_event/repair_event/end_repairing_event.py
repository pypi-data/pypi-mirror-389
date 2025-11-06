# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from __future__ import annotations

from typing import TYPE_CHECKING, Set, List, Tuple

from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEventPriority
from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.discrete_event_simulation.event.b_event.basic_b_event import BasicBEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEvent, CEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.failure_event.order_failure_event import \
    OrderFailureEvent
from availsim4core.src.discrete_event_simulation.event.event import Event


if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Basic

class EndRepairingEvent(BasicBEvent):
    """
    Defines a Repair event.
    Attributes:
        - absolute_occurrence_time: date when the repair event will be started.
        - context:
        - basic: associate basic to repair.
        - event: event which triggered this repair event.
    """
    __slots__ = 'event', 'failure_mode'

    def __init__(self,
                 absolute_occurrence_time: float,
                 context: Context,
                 basic: Basic,
                 event: Event,
                 failure_mode: FailureMode):
        super().__init__(absolute_occurrence_time, context, basic,
                         BEventPriority.END_REPAIRING_EVENT)
        self.event = event
        self.failure_mode = failure_mode

    def __hash__(self):
        return hash((type(self), self.absolute_occurrence_time, self.priority, self.basic, self.failure_mode,
                     self.event))

    def __eq__(self, other):
        if not isinstance(other, EndRepairingEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.event == other.event and \
               self.failure_mode == other.failure_mode

    def __str__(self):
        return (f"type ::{type(self)} "
                f"basic ::{self.basic.name}, "
                f"lid ::{self.basic.local_id}, "
                f"gid ::{self.basic.global_id}, "
                f"at t ::{self.absolute_occurrence_time}, "
                f"FailureMode ::{self.failure_mode} \n")

    def execute(self):

        if self.context.phase_manager.current_phase not in self.failure_mode.held_after_repair_phase_set:
            return self.basic.update_status(Status.HELD,
                                        self.absolute_occurrence_time,
                                        self.context.phase_manager.current_phase,
                                        f"REPAIRED and set to HELD - component {self.basic.name}_{self.basic.local_id}_{self.basic.global_id}",
                                        self.context)
        else:
            return self.basic.update_status(Status.RUNNING,
                                            self.absolute_occurrence_time,
                                            self.context.phase_manager.current_phase,
                                            f"REPAIRED - component {self.basic.name}_{self.basic.local_id}_{self.basic.global_id}",
                                            self.context)

    def generate_c_event(self, **kwargs) -> Set[CEvent]:

        c_event_set = set()

        order_failure_event = OrderFailureEvent(
            priority=CEventPriority.ORDER_FAILURE_EVENT,
            context=self.context,
            component=self.basic,
            event=self.event,
            failure_mode=self.failure_mode
        )

        if self.failure_mode.held_after_repair_phase_set != {PhaseManager.HELD_FOREVER}:
            if self.context.phase_manager.current_phase not in self.failure_mode.held_after_repair_phase_set:
                from availsim4core.src.discrete_event_simulation.event.c_event.held_event.order_end_holding_event import \
                    OrderEndHoldingEvent
                c_event_set.add( OrderEndHoldingEvent(
                    priority=CEventPriority.ORDER_END_HOLDING_EVENT,
                    context=self.context,
                    component=self.basic,
                    event=self.event,
                    failure_mode=self.failure_mode,
                    held_event=order_failure_event,
                    held_until_phase_set=self.failure_mode.held_after_repair_phase_set
                ))
            else:
                c_event_set.add(order_failure_event)

        if self.failure_mode.phase_change_trigger in ["AFTER_REPAIR"]:

            priority = CEventPriority.ORDER_NEXT_PHASE_EVENT
            if self.failure_mode.failure_mode_next_phase_if_failure is not None:
                priority = CEventPriority.ORDER_NEXT_PHASE_EVENT_IF_SPECIFIC_FAILURE

            from availsim4core.src.discrete_event_simulation.event.c_event.phase_event.order_next_phase_if_failure_event import \
                OrderNextPhaseIfFailureEvent
            c_event_set.add(OrderNextPhaseIfFailureEvent(priority, self.context, self.failure_mode))

        return c_event_set

    def update_b_event_collection(self,
                                event_set: Set,
                                types_of_event_to_clean: List[Event]) -> Tuple[Set, Set]:
        """
        The input event_set is cleaned from all the events of types provided by types_of_event_to_clean.
        Returns a clean set of Events and a set containing the removed events.
        """

        if self.failure_mode.phase_change_trigger in ["AFTER_REPAIR"]:
            event_to_remove = {event
                               for event in event_set
                               if type(event) in types_of_event_to_clean}

            return event_set - event_to_remove, event_to_remove

        return event_set, set()

    def update_c_event_collection(self,
                                event_set: Set,
                                types_of_event_to_clean: List[Event]) -> Tuple[Set, Set]:
        """
        The input event_set is cleaned from all the events of types provided by types_of_event_to_clean.
        Returns a clean set of Events and a set containing the removed events.
        """

        if self.failure_mode.phase_change_trigger in ["AFTER_REPAIR"]:
            event_to_remove = {event
                               for event in event_set
                               if type(event) in types_of_event_to_clean}

            return event_set - event_to_remove, event_to_remove

        return event_set, set()

    @staticmethod
    def _b_events_to_be_cleaned() -> List:
        from availsim4core.src.discrete_event_simulation.event.b_event.phase_event.next_phase_event import \
            NextPhaseEvent
        from availsim4core.src.discrete_event_simulation.event.b_event.phase_event.next_phase_if_failure_event import \
            NextPhaseIfFailureEvent
        from availsim4core.src.discrete_event_simulation.event.b_event.phase_event.jump_phase_event import \
            JumpPhaseEvent
        return [NextPhaseEvent, NextPhaseIfFailureEvent, JumpPhaseEvent]

    @staticmethod
    def _c_events_to_be_cleaned() -> List:
        from availsim4core.src.discrete_event_simulation.event.c_event.phase_event.order_next_phase_event import \
            OrderNextPhaseEvent
        from availsim4core.src.discrete_event_simulation.event.c_event.phase_event.order_next_phase_if_failure_event import \
            OrderNextPhaseIfFailureEvent
        return [OrderNextPhaseEvent,OrderNextPhaseIfFailureEvent]
