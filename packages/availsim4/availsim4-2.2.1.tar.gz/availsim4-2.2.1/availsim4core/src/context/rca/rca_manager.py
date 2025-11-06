# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from typing import List, Set

from availsim4core.src.context.rca.rca_record import RootCauseAnalysisRecord
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.context.system.rca_trigger import RootCauseAnalysisTrigger
from availsim4core.src.timeline.record import Record


class RootCauseAnalysisManager:
    """
    Class managing the root cause analysis across DES iterations; contains a trigger set and, a set of components built
    from the root component and a list of RCA records, where the output of the root cause analysis is stored.
    """
    __slots__ = 'root_cause_analysis_trigger_set', 'root_component_set', 'root_cause_analysis_records'

    def __init__(self,
                 root_cause_analysis_trigger_set: Set[RootCauseAnalysisTrigger],
                 root_component_set: Set[Component]):
        self.root_cause_analysis_trigger_set = root_cause_analysis_trigger_set
        self.root_component_set = root_component_set
        self.root_cause_analysis_records: List[RootCauseAnalysisRecord] = []

    def __eq__(self, other):
        return self.root_cause_analysis_trigger_set == other.root_cause_analysis_trigger_set and \
                self.root_component_set == other.root_component_set and \
                self.root_cause_analysis_records == other.root_cause_analysis_records

    def _append_rca_snapshot(self, record: Record, seed: int, first_record: Record):
        new_rca_record = RootCauseAnalysisRecord(seed, record, self.root_component_set, first_record)
        self.root_cause_analysis_records.append(new_rca_record)

    def trigger_root_cause_analysis_check(self, changed_records: List[Record], seed: int):
        for record in changed_records:
            if record.triggers_rca(self.root_cause_analysis_trigger_set):
                self._append_rca_snapshot(record, seed, changed_records[0])
