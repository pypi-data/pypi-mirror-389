# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import logging
import pathlib
from typing import List, Optional

from availsim4core.resources.excel_strings import SystemTemplateSheet
from availsim4core.src.context.system.system_template import SystemTemplate
from availsim4core.src.reader.reader import Reader
from availsim4core.src.reader.xlsx import xlsx_utils
from availsim4core.src.reader.xlsx.system_template.architecture_sheet_reader import ArchitectureSheetReader
from availsim4core.src.reader.xlsx.system_template.failure_mode_assignments_sheet_reader \
    import FailureModesAssignmentSheetReader
from availsim4core.src.reader.xlsx.system_template.failure_modes_sheet_reader import FailureModesSheetReader
from availsim4core.src.reader.xlsx.system_template.inspection_sheet_reader import InspectionSheetReader
from availsim4core.src.reader.xlsx.system_template.mru_sheet_reader import MinimalReplaceableUnitSheetReader
from availsim4core.src.reader.xlsx.system_template.phase_jump_triggers_sheet_reader import PhaseJumpTriggersSheetReader
from availsim4core.src.reader.xlsx.system_template.phases_sheet_reader import PhasesSheetReader
from availsim4core.src.reader.xlsx.system_template.root_cause_analysis_triggers_sheet_reader \
    import RootCauseAnalysisTriggersSheetReader

class SystemTemplateReader(Reader):
    """Class for reading the system input file. It creates a template from which the component tree is created later.

    Args:
        custom_children_logic_path: Optional[pathlib.Path]
            Path to the location containing custom children logic code.
    """
    def __init__(self, custom_children_logic_path: Optional[pathlib.Path] = None):
        self.defined_names: List[str] = []
        self.custom_children_logic_path = custom_children_logic_path

    def read(self, file_path: pathlib.Path):
        """
        This methods generates the SystemTemplate object based on the input file to which the `system_file_path`
        argument points.

        Args:
            system_file_path
                Path to the file describing the system (structure specific to AvailSim4 - see user guide).

        Returns:
            SystemTemplate object corresponding to the given inputs.
        """

        logging.debug("Reading system file %s", file_path)

        system_dictionary = xlsx_utils.read(file_path)

        architecture_entry_list = ArchitectureSheetReader().generate_architecture_entry_list(
            system_dictionary[SystemTemplateSheet.ARCHITECTURE])
        root_component_name = architecture_entry_list[0].component_name

        mru_list = MinimalReplaceableUnitSheetReader().generate_mrus(
            system_dictionary[SystemTemplateSheet.MINIMAL_REPLACEABLE_UNIT], root_component_name)
        inspections_list = InspectionSheetReader().generate_inspections(
            system_dictionary[SystemTemplateSheet.INSPECTIONS])
        phases_list = PhasesSheetReader().generate_phases(system_dictionary[SystemTemplateSheet.PHASES])
        phase_jump_triggers_list = PhaseJumpTriggersSheetReader().generate_phase_jump_triggers(
            system_dictionary[SystemTemplateSheet.PHASE_JUMP], phases_list)
        root_cause_analysis_triggers_list = RootCauseAnalysisTriggersSheetReader() \
            .generate_root_cause_analysis_triggers(system_dictionary[SystemTemplateSheet.ROOT_CAUSE_ANALYSIS],
                                                   phases_list)
        failure_modes_list = FailureModesSheetReader().generate_failure_modes(
            system_dictionary[SystemTemplateSheet.FAILURE_MODES],
            inspections_list,
            phases_list)
        failure_mode_assignments_list = FailureModesAssignmentSheetReader().generate_failure_mode_assignments(
            system_dictionary[SystemTemplateSheet.FAILURE_MODE_ASSIGNMENTS],
            failure_modes_list)

        return SystemTemplate(architecture_entry_list,
                              failure_mode_assignments_list,
                              failure_modes_list,
                              mru_list,
                              inspections_list,
                              phases_list,
                              set(root_cause_analysis_triggers_list),
                              set(phase_jump_triggers_list),
                              self.custom_children_logic_path)
