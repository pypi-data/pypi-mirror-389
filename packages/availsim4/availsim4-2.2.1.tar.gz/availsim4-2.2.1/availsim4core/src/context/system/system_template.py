# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import pathlib
from typing import List, Optional, Set

from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.system.architecture_entry import ArchitectureEntry
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.failure_mode_assignments import FailureModeAssignments
from availsim4core.src.context.system.inspection import Inspection
from availsim4core.src.context.system.minimal_replaceable_unit import MinimalReplaceableUnit
from availsim4core.src.context.system.phase_jump_trigger import PhaseJumpTrigger
from availsim4core.src.context.system.rca_trigger import RootCauseAnalysisTrigger


class SystemTemplate:
    """
    Domain object to represent the configuration template entries provided by the users.
    """
    __slots__ = 'architecture_entry_list', \
                'failure_mode_assignments_list', \
                'failure_mode_list', \
                'mru_list', \
                'inspection_list', \
                'phase_set', \
                'root_cause_analysis_trigger_set', \
                'phase_jump_trigger_set', \
                'custom_children_logic_path'

    def __init__(self,
                 architecture_entry_list: List[ArchitectureEntry],
                 failure_mode_assignments_list: List[FailureModeAssignments],
                 failure_mode_list: List[FailureMode],
                 mru_list: List[MinimalReplaceableUnit],
                 inspection_list: List[Inspection],
                 phase_set: Set[Phase],
                 root_cause_analysis_trigger_set: Set[RootCauseAnalysisTrigger],
                 phase_jump_trigger_set: Set[PhaseJumpTrigger],
                 custom_children_logic_path: pathlib.Path):
        self.architecture_entry_list = architecture_entry_list
        self.failure_mode_assignments_list = failure_mode_assignments_list
        self.failure_mode_list = failure_mode_list
        self.mru_list = mru_list
        self.inspection_list = inspection_list
        self.phase_set = phase_set
        self.root_cause_analysis_trigger_set = root_cause_analysis_trigger_set
        self.phase_jump_trigger_set = phase_jump_trigger_set
        self.custom_children_logic_path = custom_children_logic_path

    def __eq__(self, other):
        return self.architecture_entry_list == other.architecture_entry_list \
               and self.failure_mode_assignments_list == other.failure_mode_assignments_list \
               and self.failure_mode_list == other.failure_mode_list \
               and self.mru_list == other.mru_list \
               and self.inspection_list == other.inspection_list \
               and self.phase_set == other.phase_set \
               and self.root_cause_analysis_trigger_set == other.root_cause_analysis_trigger_set \
               and self.phase_jump_trigger_set == other.phase_jump_trigger_set \
               and self.custom_children_logic_path == other.custom_children_logic_path

    def find_architecture_entry(self, name: str) -> Optional[ArchitectureEntry]:
        return next((entry for entry in self.architecture_entry_list if entry.component_name == name), None)

    def find_failure_mode(self, name: str) -> Optional[FailureMode]:
        return next((failure_mode for failure_mode in self.failure_mode_list if failure_mode.name == name), None)

    def find_mru(self, name: str) -> Optional[MinimalReplaceableUnit]:
        return next((mru for mru in self.mru_list if mru.name == name), None)

    def find_inspection(self, name: str) -> Optional[Inspection]:
        return next((inspection for inspection in self.inspection_list if inspection.name == name), None)

    def find_phase(self, name: str) -> Optional[Phase]:
        return next((phase for phase in self.phase_set if phase.name == name), None)
