# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for CEventGenerator class
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from availsim4core.src.context.system.component_tree.basic import Basic

from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEventPriority
from availsim4core.src.discrete_event_simulation.event.c_event.failure_event.order_failure_event \
    import OrderFailureEvent
from availsim4core.src.discrete_event_simulation.event.c_event.phase_event.order_jump_phase_event \
    import OrderJumpPhaseEvent

from availsim4core.src.context.context import Context
from availsim4core.src.discrete_event_simulation.event.c_event.repair_event \
    .minimal_replaceable_unit_order_repair_event import  MinimalReplaceableUnitOrderRepairEvent

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.component import Component


class CEventGenerator:
    """
    Generator of CEvent objects
    """

    @classmethod
    def generate_first_events(cls,
                              absolute_simulation_time: float,
                              context: Context):
        """
        Function generating the first C events when a simulation is started
        """

        set_of_c_events = set()

        set_of_c_events.update(
            cls.get_c_events_for_mrus(
                context,
                context.root_component
            )
        )
        set_of_c_events.update(
            cls.get_c_events_for_failures(
                absolute_simulation_time,
                context,
                context.root_component
            )
        )
        set_of_c_events.update(
            cls._generate_first__phase_jump_events(
                context
            )
        )
        return set_of_c_events

    @classmethod
    def get_c_events_for_mrus(cls,
                             context: Context,
                             component: Component):
        """
        Function generating mru C events of a component recursively,
        calling itself on children of the current component if any
        """
        set_of_c_events = set()
        for mru in component.list_of_mru_trigger:
            set_of_c_events.add(
                MinimalReplaceableUnitOrderRepairEvent(
                    priority=CEventPriority.MRU_ORDER_REPAIR_EVENT,
                    context=context,
                    component=component,
                    mru=mru
                )
            )
        for child_component in component.get_children():
            events = cls.get_c_events_for_mrus(context,
                                               child_component)
            set_of_c_events.update(events)
        return set_of_c_events

    @classmethod
    def get_c_events_for_failures(cls,
                                  absolute_simulation_time: float,
                                  context: Context,
                                  component: Component):
        """
        Function generating first failure B events of a component recursively,
        calling itself on children of the current component if any
        """
        set_of_events = set()
        for child_component in component.get_children():
            events = cls.get_c_events_for_failures(absolute_simulation_time,
                                                   context,
                                                   child_component)
            set_of_events.update(events)
        if isinstance(component, Basic): # earlier it was 'not component.get_children():'
            set_of_events.add(
                OrderFailureEvent(
                    priority=CEventPriority.ORDER_FAILURE_EVENT,
                    context=context,
                    component=component,
                    event=None,
                    failure_mode=component.failure_mode
                )
            )
        return set_of_events

    @classmethod
    def _generate_first__phase_jump_events(cls,
                                           context: Context):
        """
        Function generating first C events of a component recursively,
        calling itself on children of the current component if any
        """
        set_of_c_events = set()
        for phase_jump_trigger in context.phase_manager.phase_jump_trigger_set:
            set_of_c_events.add(
                OrderJumpPhaseEvent(
                    priority=CEventPriority.ORDER_JUMP_PHASE_EVENT,
                    context=context,
                    phase_jump_trigger=phase_jump_trigger
                )
            )

        return set_of_c_events
