# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from __future__ import annotations

from typing import TYPE_CHECKING

from availsim4core.src.context.context import Context
from availsim4core.src.discrete_event_simulation.event.c_event.c_event import CEvent, CEventPriority

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Component

class ComponentCEvent(CEvent):
    __slots__ = 'component'

    def __init__(self,
                 priority: CEventPriority,
                 context: Context,
                 component: Component):
        super().__init__(priority, context)
        self.component = component

    def __eq__(self, other):
        if not isinstance(self, ComponentCEvent):
            return NotImplemented
        return super().__eq__(other) and \
            self.component == other.component

    def __lt__(self, other):
        if not isinstance(self, ComponentCEvent):
            return super().__lt__(self, ComponentCEvent)
        else:
            return super().__lt__(other) or (super().__eq__(other) and self.component.global_id < other.component.global_id)

    def __hash__(self):
        return hash((type(self), self.priority, self.component))

    def __str__(self):
        return (f"failure ComponentCEvent {self.__class__.__name__}:"
                f"of component={self.component.name} : {self.component.global_id} with priority ={self.priority}\n")
