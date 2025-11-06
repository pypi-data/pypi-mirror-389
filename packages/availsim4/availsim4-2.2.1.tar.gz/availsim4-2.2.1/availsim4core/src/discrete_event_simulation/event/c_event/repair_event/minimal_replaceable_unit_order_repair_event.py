# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from __future__ import annotations

from typing import TYPE_CHECKING, Set
import logging
import sys


from availsim4core.src.context.context import Context
from availsim4core.src.context.system.minimal_replaceable_unit import MinimalReplaceableUnit
from availsim4core.src.context.system.system_utils import SystemUtils
from availsim4core.src.discrete_event_simulation.event.b_event.b_event import BEvent
from availsim4core.src.discrete_event_simulation.event.b_event. \
    repair_event.minimal_replaceable_unit_end_repairing_event import MinimalReplaceableUnitEndRepairingEvent
from availsim4core.src.discrete_event_simulation.event.b_event.repair_event. \
    minimal_replaceable_unit_start_repairing_event import MinimalReplaceableUnitStartRepairingEvent
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.component_c_event import ComponentCEvent

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Component

class MinimalReplaceableUnitOrderRepairEvent(ComponentCEvent):
    """
   MinimalReplaceableUnit are a mechanism used to repair a group of components when one or a group of specific monitored
   components fail. This class generates the C event used in that mechanism
   """
    __slots__ = 'mru'

    def __init__(self,
                 priority: CEventPriority,
                 context: Context,
                 component: Component,
                 mru: MinimalReplaceableUnit):
        super().__init__(priority, context, component)
        self.mru = mru

    def __eq__(self, other):
        if not isinstance(other, MinimalReplaceableUnitOrderRepairEvent):
            return NotImplemented
        return super().__eq__(other) and \
               self.mru == other.mru

    def __hash__(self):
        return hash((type(self), self.priority, self.component, self.mru))

    def __str__(self):
        return f"MinimalReplaceableUnitOrderRepairEvent:: " \
               f"priority:{self.priority} - " \
               f"component:{self.component.name} - " \
               f"mru:{self.mru.name}"

    def is_condition_valid(self):
        return self.component.status == self.mru.status

    def _create_mru_b_event(self,
                            absolute_simulation_time,
                            component):
        start_repairing_event = \
            MinimalReplaceableUnitStartRepairingEvent(absolute_occurrence_time=absolute_simulation_time,
                                                      context=self.context,
                                                      basic=component,
                                                      event=self)

        end_repairing_event = \
            MinimalReplaceableUnitEndRepairingEvent(
                absolute_occurrence_time=absolute_simulation_time + self.mru.repair_law.get_random_value(),
                context=self.context,
                basic=component,
                event=self,
                mru_trigger=self.mru)

        return {start_repairing_event, end_repairing_event}

    def get_b_events_from_mru_target(self,
                                     absolute_simulation_time) -> Set[BEvent]:
        """
        Finds the lowest common ancestor component, then for each of its children associated to the mru,
        generates the corresponding b_event.
        """

        # get up to the lowest common ancestor
        scope_common_ancestor_list = [SystemUtils.find_first_lowest_level_ancestor_with_name(self.component, scope_ancestor)
                                                                                       for scope_ancestor in self.mru.scope_common_ancestor]
        try:
            scope_common_ancestor = next(ancestor for ancestor in scope_common_ancestor_list if ancestor is not None)
        except StopIteration:
            message = f"No component defining the size of MRU scope ({self.mru.scope_common_ancestor}) was located in the list of ancestors of the component {self.component}"
            logging.error(message)
            sys.exit(1)
            # TODO: SANITY CHECK: catch this error earlier in the process

        # get list of components subject to the trigger
        list_of_components_matching_mru = self.get_list_of_components_subject_to_the_trigger(
            scope_common_ancestor)

        return {b_event
                for mru_component in list_of_components_matching_mru
                for b_event in self._create_mru_b_event(absolute_simulation_time,
                                                        mru_component)}

    def get_list_of_components_subject_to_the_trigger(self, component):
        """
        For a given component, this method retrieves the associated matching minimal replaceable target units.
        """
        if not component.get_children():
            return [component
                    for mru_target in component.list_of_mru_group
                    if self.mru == mru_target]

        return [component_trigger
                for child in component.get_children()
                for component_trigger in self.get_list_of_components_subject_to_the_trigger(child)]

    def generate_b_events(self, absolute_simulation_time):
        return self.get_b_events_from_mru_target(absolute_simulation_time)
