# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from typing import List
import copy

from availsim4core.src.context.context import Context
from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.minimal_replaceable_unit import MinimalReplaceableUnit


class Basic(Component):
    """
    Leaf element of the Component tree.
    It defines the 'basic' element of the system which is susceptible of failure.
    """
    __slots__ = 'failure_mode', 'list_of_mru_group'

    def __init__(self,
                 global_id: int,
                 name: str,
                 local_id: int,
                 parents: List[Compound],
                 failure_mode: FailureMode,
                 list_of_mru_trigger: List[MinimalReplaceableUnit],
                 list_of_mru_group: List[MinimalReplaceableUnit]
                 ):
        super().__init__(global_id, name, local_id, parents, list_of_mru_trigger)
        self.failure_mode = copy.deepcopy(failure_mode)
        self.list_of_mru_group = list_of_mru_group

    def __str__(self, level=0) -> str:
        return ("\t" * level +
                f"{self.name}_{self.local_id}"
                f" :uniq_id:{self.global_id}"
                f" :parents: {self.get_parents()}"
                f" :status: {self.status.name}"
                f" :failure mode: {self.failure_mode}"
                f" :mru: {self.list_of_mru_group} -- {self.list_of_mru_trigger}\n")

    def __repr__(self):
        return f"{self.name}_{self.local_id} uniq_id: {self.global_id}"

    def to_set(self):
        return set([self])

    def update_status(self,
                      new_status: Status,
                      timestamp: float,
                      phase: Phase,
                      description: str,
                      context: Context):
        return self._update_status(new_status, timestamp, phase, description, context)
