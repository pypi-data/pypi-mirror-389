# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for BasicBEvent class
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Set, Tuple, List

from availsim4core.src.discrete_event_simulation.event.event import Event
from availsim4core.src.context.context import Context
from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEvent, BEventPriority

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Basic


class BasicBEvent(BEvent):
    """
    Class dealing with B events related to basic components
    """
    __slots__ = ['basic']

    def __init__(self,
                 absolute_occurrence_time: float,
                 context: Context,
                 basic: Basic,
                 priority: BEventPriority):
        super().__init__(absolute_occurrence_time, context, priority)
        self.basic = basic

    def __eq__(self, other):
        return super().__eq__(other) and \
               self.basic == other.basic

    def __lt__(self, other):
        if not isinstance(other, BasicBEvent):
            return super().__lt__(other)
        else:
            return super().__lt__(other) or (super().__eq__(other) and self.basic.global_id < other.basic.global_id)


    def update_b_event_collection(self,
                                  event_set: Set[Event],
                                  types_of_event_to_clean: List[Event]) -> Tuple[Set[Event], Set[Event]]:
        """
        The input event_set is cleaned from all the events of types provided by types_of_event_to_clean.
        Returns a clean set of Events and a set containing the removed events.
        """
        if not types_of_event_to_clean:
            return event_set, set()

        event_to_remove: Set[Event] = set()

        for event in event_set:
            if type(event) in types_of_event_to_clean:

                # if the event has a basic
                if isinstance(event, BasicBEvent): # old hasattr(event, 'basic'):
                    # and the basic is similar to the self.basic
                    if event.basic == self.basic:
                        # then this event has to be removed
                        event_to_remove.add(event)
                else:
                # if the event has no basic, then it has to be removed
                    event_to_remove.add(event)

        return event_set - event_to_remove, event_to_remove
