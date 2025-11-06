# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module for the RecordComponent class representing records for the timeline"""

from __future__ import annotations

from typing import TYPE_CHECKING
from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.results.result_record_entry_component import ResultRecordEntryComponent
from availsim4core.src.timeline.record import Record
from availsim4core.src.context.system.rca_trigger import RootCauseAnalysisTrigger

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.basic import Component


class RecordComponent(Record):
    """
    Class of record dedicated to components
    A record is an object used to keep trace of the state of the system
    """
    __slots__ = ['component']

    def __init__(self,
                 component: Component,
                 status: Status,
                 timestamp: float,
                 phase: Phase,
                 description: str):
        super().__init__(timestamp, phase, description, status)
        self.component = component

    def __eq__(self, other):
        if not isinstance(other, RecordComponent):
            return NotImplemented
        return super().__eq__(other) and self.component == other.component

    def __repr__(self):
        return super().__repr__() \
               + f" component: {self.component.name} -> id: {self.component.global_id}" \
                 f" phase: {self.phase}"

    def __str__(self):
        return f"RecordComponent at {self.timestamp}: " \
               f"{self.component.name}_{self.component.local_id}_{self.component.global_id} " \
               f"with status {self.status} on phase {self.phase.name}__{self.status}"

    def get_name(self) -> str:
        return self.component.get_unique_name()

    def get_result_record_entry(self) -> ResultRecordEntryComponent:
        return ResultRecordEntryComponent(self.component,
                                          self.status,
                                          self.phase,
                                          self.description)

    def triggers_rca(self, rca_triggers) -> bool:
        return RootCauseAnalysisTrigger(self.component.name, str(self.component.status), self.phase.name) \
            in rca_triggers
