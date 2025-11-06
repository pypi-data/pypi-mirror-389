# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.system.rca_trigger import RootCauseAnalysisTrigger
from availsim4core.src.results.result_record_entry_phase import ResultRecordEntryPhase
from availsim4core.src.timeline.record import Record


class RecordPhase(Record):
    """
    Class of record dedicated to phases
    A record is an object used to keep trace of the state of the system
    """

    def __init__(self,
                 phase: Phase,
                 timestamp: float,
                 description: str):
        super().__init__(timestamp, phase, description)

    def __eq__(self, other):
        if not isinstance(other, RecordPhase):
            return NotImplemented
        return super().__eq__(other)

    def __repr__(self):
        return super().__repr__() + f" phase: {self.phase}"

    def __str__(self):
        return f"RecordPhase at {self.timestamp}: {self.phase.name}"

    def get_name(self) -> str:
        return self.phase.name

    def get_result_record_entry(self):
        return ResultRecordEntryPhase(self.phase, self.description)

    def triggers_rca(self, rca_triggers):
        return RootCauseAnalysisTrigger("PHASE", "_", self.phase.name) \
            in rca_triggers
