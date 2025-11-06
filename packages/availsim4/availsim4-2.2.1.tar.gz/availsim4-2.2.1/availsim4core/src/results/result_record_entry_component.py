# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.results.result_record_entry import ResultRecordEntry


class ResultRecordEntryComponent(ResultRecordEntry):
    """
    This method defines an Identifier of the record entry.
    This is useful, in case we want to regroup the entry based on this identifier. {cf SimulationResults}
    That particular class is dedicated to entries of components.
    """
    __slots__ = 'component', 'status', 'phase', 'description'

    def __init__(self,
                 component,
                 status,
                 phase,
                 description: str):
        self.component = component
        self.status = status
        self.phase = phase
        self.description = description

    def __hash__(self):
        return hash((self.component, self.status, self.phase, self.description))

    def __eq__(self, other) -> bool:
        return self.component == other.component and \
               self.phase == other.phase and \
               self.status == other.status and \
               self.description == other.description

    def __str__(self) -> str:
        return f"ResultRecordEntryComponent: {self.component.name}__{self.component.local_id}__{self.component.global_id}"

    def identifier(self) -> str:
        """
        Function returning an identifier used to filter records
        """
        return f"{self.component.name}_{self.component.local_id}_{self.component.global_id}"
