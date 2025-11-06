# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from __future__ import annotations

from abc import abstractmethod
from typing import List, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from availsim4core.src.context.context import Context
    from availsim4core.src.context.system.component_tree.compound import Compound

from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.minimal_replaceable_unit import MinimalReplaceableUnit
from availsim4core.src.timeline.record_component import RecordComponent


class ComponentType:
    BASIC = "BASIC"
    COMPOUND = "COMPOUND"


class Component:
    """
    Defines a component of the MUTABLE Tree system structure. It can be specified as Compound or Basic.
    The tree is mutable (on the Discrete event simulation level, status and statistics_des)
    because it needs to handle million of iteration when manipulating the status and evaluating the statistics.
    """
    __slots__ = 'global_id', 'name', 'local_id', '_parents', 'status', 'list_of_mru_trigger'

    def __init__(self,
                 global_id: int,
                 name: str,
                 local_id: int,
                 parents: List[Compound],
                 list_of_mru_trigger: List[MinimalReplaceableUnit]):
        self.global_id = global_id
        self.local_id = local_id
        self.name = name
        self._parents: List[Compound] = parents
        self.status = Status.RUNNING
        self.list_of_mru_trigger = list_of_mru_trigger

    def __hash__(self):
        return hash(self.global_id)

    def __eq__(self, other):
        return self.global_id == other.global_id

    def __lt__(self, other):
        return self.global_id < other.global_id

    def get_parents(self):
        return self._parents

    def add_parent(self, parent: Compound):
        self._parents.append(parent)

    def get_children(self):
        return []

    def get_unique_name(self) -> str:
        """Returns the unique name of the component in format: `NAME_LOCAL-ID_GLOBAL-ID`.

        Returns:
            str: unique name of the component
        """
        return f"{self.name}_{self.local_id}_{self.global_id}"

    def remove(self, component) -> None:
        pass

    def is_shared(self):
        return len(self._parents) > 1

    def _propagate_status(self,
                          timestamp: float,
                          phase: Phase,
                          description: str,
                          context: Context) -> List[RecordComponent]:
        """
        Propagate the status to the parents Components.
        :param timestamp: timestamps of the new status
        :param phase: phase in which the new status changed
        :param description: description of the status.
        :param context: the context of the simulation (structure containing almost everything)
        """
        record_list = []
        for compound_parent in self._parents:
            new_record_list = compound_parent.update_status(timestamp, phase, description, context)
            record_list.extend(new_record_list)
        return record_list

    def _update_status(self, new_status: Status, timestamp: float, phase: Phase, description: str, context: Context) \
                                                                                             -> List[RecordComponent]:
        """Update the status of the current component object. If the status changes it is recorded in the records list
        being returned and the status propagates to the component parents.

        Args:
            new_status (Status): new status of the component.
            timestamp (float): timestamp of the status.
            phase (Phase): phase in which the event occurs.
            description (str): description of the new status.
            context (Phase): context object used to evaluate children logic.

        Returns:
            List[RecordComponent]: list of records to be included in the records list of the current timeline. Note that
                events in the list should preserve causal order, with the event initiating the chain supposed to be the
                first in the list.
        """
        record_list = []
        if self.status != new_status:
            self.status = new_status
            record = RecordComponent(self, new_status, timestamp, phase, description)
            record_list.append(record)
            new_record_list = self._propagate_status(timestamp, phase, description, context)
            record_list.extend(new_record_list)
        return record_list

    @abstractmethod
    def to_set(self) -> Set:
        """
        :return: The flat Pre-order (NLR) representation of the tree.
        ::see https://en.wikipedia.org/wiki/Tree_traversal
        """
