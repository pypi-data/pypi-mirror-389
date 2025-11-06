# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for MinimalReplaceableUnitEndRepairingEvent class
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Set

from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEventPriority

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.minimal_replaceable_unit import MinimalReplaceableUnit
from availsim4core.src.discrete_event_simulation.event.b_event.basic_b_event import BasicBEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEvent, CEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.component_c_event import ComponentCEvent

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Basic


class MinimalReplaceableUnitEndRepairingEvent(BasicBEvent):
    """
    This event defines the End of a reparation for a Minimal Replaceable Unit.
    """
    __slots__ = 'event', 'mru_trigger'

    def __init__(self,
                 absolute_occurrence_time: float,
                 context: Context,
                 basic: Basic,
                 event: ComponentCEvent,
                 mru_trigger: MinimalReplaceableUnit):
        super().__init__(absolute_occurrence_time, context, basic,
                         BEventPriority.MRU_END_REPAIRING_EVENT)
        self.event = event
        self.mru_trigger = mru_trigger

    def __hash__(self):
        return hash(
            (type(self),
            self.absolute_occurrence_time,
            self.priority,
            self.basic,
            self.event,
            self.mru_trigger))

    def __eq__(self, other):
        if not isinstance(other, MinimalReplaceableUnitEndRepairingEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.event == other.event and \
               self.mru_trigger == other.mru_trigger

    def __str__(self):
        return (f"type ::{type(self)} "
                f"basic ::{self.basic.name}, "
                f"lid ::{self.basic.local_id}, "
                f"gid ::{self.basic.global_id}, "
                f"mru trigger ::{self.mru_trigger}, "
                f"at t ::{self.absolute_occurrence_time} \n")

    def execute(self):
        return self.basic.update_status(Status.RUNNING,
                                        self.absolute_occurrence_time,
                                        self.context.phase_manager.current_phase,  # or phase of the failure mode?
                                        f"mru ({self.event.mru.name}) REPAIRED",
                                        self.context)

    def generate_c_event(self, **kwargs) -> Set[CEvent]:
        from availsim4core.src.discrete_event_simulation.c_event_generator import CEventGenerator
        from availsim4core.src.discrete_event_simulation.event.c_event. \
            repair_event.minimal_replaceable_unit_order_repair_event  \
                                                    import MinimalReplaceableUnitOrderRepairEvent
        set_of_c_events = set()

        set_of_c_events.update(
            CEventGenerator.get_c_events_for_failures(
                self.absolute_occurrence_time,
                self.context,
                self.basic
            )
        )

        set_of_c_events.add(
            MinimalReplaceableUnitOrderRepairEvent(
                priority=CEventPriority.MRU_ORDER_REPAIR_EVENT,
                context=self.context,
                component=self.event.component,
                mru=self.mru_trigger
            )
        )

        return set_of_c_events
