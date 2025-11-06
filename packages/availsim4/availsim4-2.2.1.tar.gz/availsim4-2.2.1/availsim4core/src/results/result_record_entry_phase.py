# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.results.result_record_entry import ResultRecordEntry


class ResultRecordEntryPhase(ResultRecordEntry):
    """
    This method defines an Identifier of the record entry.
    This is useful, in case we want to regroup the entry based on this identifier. {cf SimulationResults}
    That particular class is dedicated to entries of phases.
    """
    __slots__ = 'phase', 'description'

    def __init__(self,
                 phase,
                 description: str):
        self.phase = phase
        self.description = description

    def __hash__(self):
        return hash((self.phase, self.description))

    def __eq__(self, other) -> bool:
        return self.phase == other.phase and \
               self.description == other.description

    def __str__(self) -> str:
        return f"ResultRecordEntryPhase: {self.phase.name}"

    def identifier(self) -> str:
        """
        Function returning an identifier used to filter records
        """
        return f"Phase"
