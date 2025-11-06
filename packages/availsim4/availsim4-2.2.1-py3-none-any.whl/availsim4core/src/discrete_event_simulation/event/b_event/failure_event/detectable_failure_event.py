# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for DetectableFailureEvent class
"""

from __future__ import annotations
import logging

from typing import Set, TYPE_CHECKING, Tuple, List

from availsim4core.src.discrete_event_simulation.event.event import Event
from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEvent, CEventPriority
from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.discrete_event_simulation.event.b_event.failure_event.failure_event import FailureEvent
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.discrete_event_simulation.event.c_event.held_event.order_end_holding_event import \
    OrderEndHoldingEvent
from availsim4core.src.discrete_event_simulation.event.c_event.repair_event.order_repair_event import OrderRepairEvent
from .....timeline.record import Record

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Basic


class DetectableFailureEvent(FailureEvent):
    """
    Class dealing with detectable failure events. A detectable failure can trigger a repair because that failure is ,
    in real life, detected by the monitoring system
    """

    def __init__(self,
                 absolute_occurrence_time: float,
                 context: Context,
                 basic: Basic,
                 failure_mode: FailureMode):
        super().__init__(absolute_occurrence_time, context, basic, failure_mode,
                         priority=BEventPriority.DETECTABLE_FAILURE_EVENT)

    def postpone(self, duration) -> DetectableFailureEvent:
        return DetectableFailureEvent(self.absolute_occurrence_time + duration,
                                      self.context,
                                      self.basic,
                                      self.failure_mode)

    def execute(self) -> List[Record]:
        return self.basic.update_status(Status.FAILED,
                                        self.absolute_occurrence_time,
                                        self.context.phase_manager.current_phase,  # or phase of the failure mode?!
                                        f"{self.failure_mode.name} failure mode of component {self.basic.name}_{self.basic.local_id}_{self.basic.global_id}",
                                        self.context)

    def update_b_event_collection(self,
                                event_set: Set,
                                types_of_event_to_clean: List[Event]) -> Tuple[Set, Set]:
        """
        The input event_set is cleaned from all the events of types provided by types_of_event_to_clean.
        Returns a clean set of Events and a set containing the removed events.
        """

        if self.failure_mode.phase_change_trigger in ["AFTER_REPAIR", "AFTER_FAILURE"]:
            # we clean the flow of the phases as for failures, the tye_of_event_to_clean are only the phase event
            b_event_to_remove_set = {event
                                     for event in event_set
                                     if type(event) in types_of_event_to_clean}
            return event_set - b_event_to_remove_set, b_event_to_remove_set

        elif self.failure_mode.phase_change_trigger in ["NEVER"]:
            # we do not change the normal flow of the phases
            return event_set, set()
        else:
            logging.exception("The phase_change_trigger of a DETECTABLE failure has been set to " \
                "an unrecognized value. Please check the failure mode %s. In this execution, the " \
                "trigger will be used as with 'NEVER' - not changing normal flow of phases.",
                self.failure_mode.name)
            return event_set, set()

    def generate_c_event(self, **kwargs) -> Set[CEvent]:

        c_event_set = set()

        order_repair_event = OrderRepairEvent(
            priority=CEventPriority.ORDER_REPAIR_EVENT,
            context=self.context,
            component=self.basic,
            event=self,
            failure_mode=self.failure_mode
        )

        if self.failure_mode.held_before_repair_phase_set != {PhaseManager.HELD_FOREVER}:
            if self.context.phase_manager.current_phase not in self.failure_mode.held_before_repair_phase_set:
                c_event_set.add(OrderEndHoldingEvent(
                    priority=CEventPriority.ORDER_END_HOLDING_EVENT,
                    context=self.context,
                    component=self.basic,
                    event=self,
                    failure_mode=self.failure_mode,
                    held_event=order_repair_event,
                    held_until_phase_set=self.failure_mode.held_before_repair_phase_set
                ))
            else:
                c_event_set.add(order_repair_event)

        if self.failure_mode.phase_change_trigger in ["AFTER_FAILURE"]:

            from availsim4core.src.discrete_event_simulation.event.c_event.phase_event.order_next_phase_if_failure_event import \
                OrderNextPhaseIfFailureEvent
            c_event_set.add(
                OrderNextPhaseIfFailureEvent(
                    priority=CEventPriority.ORDER_NEXT_PHASE_EVENT,
                    context=self.context,
                    failure_mode=self.failure_mode
                )
            )

        return c_event_set
