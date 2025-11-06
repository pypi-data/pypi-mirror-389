# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

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
from availsim4core.src.discrete_event_simulation.event.c_event.phase_event.order_next_phase_if_failure_event import \
    OrderNextPhaseIfFailureEvent


if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Basic

class BlindFailureEventError(Exception):
    pass

class BlindFailureEvent(FailureEvent):
    """
    Class dealing with blind failure events. A blind failure does not trigger a repair because that failure is ,
    in real life, not detected by the monitoring system
    """

    def __init__(self,
                 absolute_occurrence_time: float,
                 context: Context,
                 basic: Basic,
                 failure_mode: FailureMode):
        super().__init__(absolute_occurrence_time, context, basic, failure_mode,
                         priority=BEventPriority.BLIND_FAILURE_EVENT)

    def postpone(self, duration):
        return BlindFailureEvent(self.absolute_occurrence_time + duration,
                                 self.context,
                                 self.basic,
                                 self.failure_mode)

    def execute(self):
        return self.basic.update_status(Status.BLIND_FAILED,
                                        self.absolute_occurrence_time,
                                        self.context.phase_manager.current_phase,
                                        f"{self.failure_mode.name} failure mode of component {self.basic.name}_{self.basic.local_id}_{self.basic.global_id}",
                                        self.context)

    def update_b_event_collection(self,
                                event_set: Set,
                                types_of_event_to_clean: List[Event]) -> Tuple[Set, Set]:
        """
        The input event_set is cleaned from all the events of types provided by types_of_event_to_clean.
        Returns a clean set of Events and a set containing the removed events.
        """

        if self.failure_mode.phase_change_trigger in ["AFTER_FAILURE"]:
            # if the change of phase is to perform immediately after the failure, then event of the type "phase changed"
            # are removed from the event_set
            b_event_to_remove_set = {event
                                     for event in event_set
                                     if type(event) in types_of_event_to_clean}
            return event_set - b_event_to_remove_set, b_event_to_remove_set

        elif self.failure_mode.phase_change_trigger in ["NEVER"]:
            # we do not change the normal flow of the phases
            return event_set, set()
        elif self.failure_mode.phase_change_trigger in ['AFTER_REPAIR']:
            # this value is not possible for a blind failure
            message_exception = f"The phase_change_trigger of a BLIND failure has been set to AFTER_REPAIR which is not" \
                                f" an acceptable option. Please check the failure_mode {self.failure_mode.name}."
            logging.exception(message_exception)
            raise BlindFailureEventError(message_exception)
        logging.exception("The phase_change_trigger of a BLIND failure has been set to an " \
                          "unrecognized value. Please check the failure mode " \
                          "%s. In this execution, the trigger will be " \
                          "used as with 'NEVER' - not changing normal flow of phases.",
                          self.failure_mode.name)
        return event_set, set()

    def generate_c_event(self, **kwargs) -> Set[CEvent]:

        if self.failure_mode.phase_change_trigger in ["AFTER_FAILURE"]:
            return {
                OrderNextPhaseIfFailureEvent(
                    priority=CEventPriority.ORDER_NEXT_PHASE_EVENT,
                    context=self.context,
                    failure_mode=self.failure_mode
                )
            }
        else:
            return set()
