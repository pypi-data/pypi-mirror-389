# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from typing import List, Set, Tuple

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEvent, BEventPriority
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event import detectable_failure_event, \
    blind_failure_event
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.failure_event import FailureEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEvent, CEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.phase_event.order_next_phase_event import \
    OrderNextPhaseEvent
from availsim4core.src.discrete_event_simulation.event.c_event.postpone_c_event import PostponeCEvent
from availsim4core.src.timeline.record_phase import RecordPhase
from availsim4core.src.discrete_event_simulation.event.event import Event


class NextPhaseEvent(BEvent):
    """
    Class handling the change of phases
    """

    def __init__(self,
                 absolute_occurrence_time: float,
                 context: Context,
                 priority=BEventPriority.NEXT_PHASE_EVENT):
        super().__init__(absolute_occurrence_time,
                         context,
                         priority)

    def __hash__(self):
        return hash((type(self), self.absolute_occurrence_time, self.priority))

    def __eq__(self, other):
        if not isinstance(other, NextPhaseEvent):
            return NotImplemented
        return super().__eq__(other)

    def __str__(self):
        return (f"type ::{type(self)} "
                f"at t ::{self.absolute_occurrence_time} \n")

    @staticmethod
    def _b_events_to_be_cleaned() -> List:
        return [detectable_failure_event.DetectableFailureEvent,
                blind_failure_event.BlindFailureEvent,
                NextPhaseEvent]

    @staticmethod
    def _c_events_to_be_cleaned() -> List:
        from availsim4core.src.discrete_event_simulation.event.c_event.phase_event.order_next_phase_if_failure_event import \
            OrderNextPhaseIfFailureEvent
        return [OrderNextPhaseIfFailureEvent,
                OrderNextPhaseEvent]

    def update_b_event_collection(self,
                                event_set: Set,
                                types_of_event_to_clean: List[Event]) -> Tuple[Set, Set]:
        """
        The input event_set is cleaned from all the events of types provided by types_of_event_to_clean.
        Returns a clean set of Events and a set containing the removed events.
        """
        b_event_to_remove_set = set()
        b_event_to_remove_and_not_to_postpone = set()
        previous_phase_record = self.context.timeline_record._get_previous_record_of_type(RecordPhase)
        if previous_phase_record is not None:
            for b_event in event_set:
                if isinstance(b_event,NextPhaseEvent):
                    b_event_to_remove_and_not_to_postpone.add(b_event)
                elif isinstance(b_event, FailureEvent):
                    if previous_phase_record.phase not in b_event.failure_mode.phase_set:
                        b_event_to_remove_set.add(b_event)
        return event_set - b_event_to_remove_set - b_event_to_remove_and_not_to_postpone, b_event_to_remove_set

    def execute(self):
        records = [self.context.phase_manager.go_to_phase(
            self.absolute_occurrence_time,
            self.context.phase_manager.current_phase.next,
            self.context.phase_manager.DEFAULT_PHASE_DESCRIPTION
        )]
        records.extend(self.context.add_record_of_each_component(self.absolute_occurrence_time,
                                                                 self.context.phase_manager.UPDATE_FOLLOWING_A_PHASE_CHANGE))
        return records

    def generate_c_event(self, **kwargs) -> Set:

        c_event_set: Set[CEvent] = {
            OrderNextPhaseEvent(
                priority=CEventPriority.ORDER_NEXT_PHASE_EVENT,
                context=self.context
            )
        }

        event_set = kwargs.pop('b_event_removed_set', set())
        previous_phase_record = self.context.timeline_record._get_previous_record_of_type(RecordPhase)
        if previous_phase_record is None:
            return c_event_set

        for b_postpone_event in event_set:

            if not isinstance(b_postpone_event,NextPhaseEvent):

                # Search for the previous record where the concerned basic component was running.
                # Either it entered the phase as RUNNING and we postpone the whole duration of the phase
                # Or it entered the phase as something else than RUNNING, but still it has been changed to RUNNING
                # otherwise no failure event would need to be postponed
                previous_record = self.context.timeline_record._get_previous_record_of_basic_in_status(
                    b_postpone_event.basic,
                    Status.RUNNING)

                c_event_set.add(
                    PostponeCEvent(
                        priority=CEventPriority.ORDER_POSTPONE_C_EVENT,
                        context=self.context,
                        postpone_duration=self.absolute_occurrence_time - previous_record.timestamp,
                        b_event=b_postpone_event
                    )
                )

        return c_event_set
