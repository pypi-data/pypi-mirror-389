# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from __future__ import annotations

from typing import List, Set

from availsim4core.src.context.context import Context
from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.system.children_logic.children_logic import ChildrenLogic
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.minimal_replaceable_unit import MinimalReplaceableUnit
from ....timeline.record_component import RecordComponent


class Compound(Component):
    """
    Node of the Component tree.
    Compound is a composite thus it includes a Children list of Component.
    """
    __slots__ = '_children', 'children_logic'

    def __init__(self,
                 global_id: int,
                 name: str,
                 local_id: int,
                 parents: List[Compound],
                 children_logic: ChildrenLogic,
                 list_of_mru_trigger: List[MinimalReplaceableUnit]):
        super().__init__(global_id, name, local_id, parents, list_of_mru_trigger)
        self._children: List[Component] = []
        self.children_logic = children_logic

    def __str__(self, level=0):
        ret = ("\t" * level +
               f"{self.name}_{self.local_id}"
               f" :uniq_id:{self.global_id}"
               f" :parents: {self.get_parents()}"
               f" :status: {self.status.name}"
               f" :mru: {self.list_of_mru_trigger}\n")

        for child in self._children:
            ret += child.__str__(level + 1)
        return ret

    def __repr__(self):
        return f"{self.name}_{self.local_id}_{self.global_id}"

    def get_children(self) -> List[Component]:
        return self._children

    def add_children_list(self, component_list: List[Component]) -> None:
        """
        Add a list of Component to the Children list of component.
        :param component_list: the list of component Children to add.
        """
        self._children.extend(component_list)

    def remove(self, component: Component) -> None:
        self._children.remove(component)
        component._parents = []

    def update_status(self,
                      timestamp: float,
                      phase: Phase,
                      description: str,
                      context: Context) -> List[RecordComponent]:
        new_status = self.evaluate_status(context)
        return self._update_status(new_status, timestamp, phase, description, context)

    def evaluate_status(self, context: Context) -> Status:
        return self.children_logic.evaluate(self._children, context)

    def to_set(self) -> Set[Component]:
        set_of_components: Set[Component] = set([self])
        for child in self._children:
            set_of_components.update(child.to_set())
        return set_of_components
