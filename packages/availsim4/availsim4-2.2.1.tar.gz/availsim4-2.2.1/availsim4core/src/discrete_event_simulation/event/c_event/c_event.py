# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for CEventPriority class
"""

from enum import Enum
from availsim4core.src.context.context import Context
from availsim4core.src.discrete_event_simulation.event.event import Event


class CEventPriority(Enum):
    """
    class used to easily order the C Event set
    """

    ORDER_START_INSPECTION_EVENT = -7
    ORDER_END_INSPECTION_EVENT = -6

    ORDER_JUMP_PHASE_EVENT = -5
    ORDER_NEXT_PHASE_EVENT_IF_SPECIFIC_FAILURE = -4
    ORDER_NEXT_PHASE_EVENT = -3

    ORDER_POSTPONE_C_EVENT = -2

    MRU_ORDER_REPAIR_EVENT = -1

    ORDER_FAILURE_EVENT = 0
    REEVALUATE_ORDER_ALL_FAILURE_EVENTS = 1
    REEVALUATE_ORDER_ALL_INSPECTION_EVENTS = 2
    ORDER_REPAIR_EVENT = 3
    ORDER_END_HOLDING_EVENT = 4

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class CEvent(Event):
    """
    C events = Conditioned events.
    Those events are not planned in advance but only occur when some particular conditions are present. This type of events would be planning of actions in our case, that
    is to say creating B events:  ordering a repair now or at a later date, advancing the end of a phase or the next maintenance period, the next periodic inspection.
    The logic could be complex. Maybe some C events are postponed because conditions are not realised to trigger a B event associated: lack of spare or man power to repair something, ...
    """
    __slots__ = 'priority'

    def __init__(self,
                 priority: CEventPriority,
                 context: Context):
        super().__init__(context)
        self.priority = priority

    def __eq__(self, other):
        return self.priority == other.priority

    def __lt__(self, other):
        return self.priority < other.priority

    def is_condition_valid(self):
        """
        The condition for the event to be valid in order to be processed.
        By default the value returned is True
        """
        return True

    def generate_b_events(self, absolute_simulation_time):
        """
        Given an absolute_simulation_time, this method returns the set of BEvents
        triggered by this particular c_event.
        """
        pass
