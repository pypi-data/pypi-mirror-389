# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module for reading the sheet specifying the Root Cause Analysis Triggers in the Excel-formatted input"""

import logging
from availsim4core.resources.excel_strings import SystemTemplateRootCauseAnalysisColumn
from availsim4core.src.context.system.rca_trigger import RootCauseAnalysisTrigger
from availsim4core.src.reader.xlsx import xlsx_utils
from availsim4core.src.reader.xlsx.system_template.sheet_reader import SheetReader


class RootCauseAnalysisTriggersSheetReader(SheetReader):
    """This class is reponsible for reading the Root Cause Analysis Triggers input Excel sheet"""
    WORKSHEET = "ROOT_CAUSE_ANALYSIS"

    def generate_root_cause_analysis_trigger_from_row(self, row, phases_list) -> RootCauseAnalysisTrigger:
        """This method produces a number of RootCauseAnalysisTriggers based on the contents of the row provided as the
        argument."""
        exception_message_hint = f"root cause analysis row: {row}"

        root_cause_analysis_trigger_component_name = xlsx_utils.clean_str_cell(
            row, SystemTemplateRootCauseAnalysisColumn.COMPONENT_NAME,
            exception_message_hint=exception_message_hint)
        root_cause_analysis_trigger_component_status_list = xlsx_utils.clean_list_cell(
            row, SystemTemplateRootCauseAnalysisColumn.COMPONENT_STATUS, optional= False,
            exception_message_hint=exception_message_hint)
        root_cause_analysis_trigger_phase_list = xlsx_utils.read_cell_list_with_default(
            row, SystemTemplateRootCauseAnalysisColumn.PHASE, exception_message_hint,
            {phase.name for phase in phases_list}
        )

        root_cause_analysis_trigger_comments = xlsx_utils.get_cell_text(row,
                                                                        SystemTemplateRootCauseAnalysisColumn.COMMENTS,
                                                                        optional=True)

        return RootCauseAnalysisTrigger.build(
            root_cause_analysis_trigger_component_name,
            root_cause_analysis_trigger_component_status_list,
            root_cause_analysis_trigger_phase_list,
            root_cause_analysis_trigger_comments
        )

    def generate_root_cause_analysis_triggers(self, system_dictionary_root_cause_analysis, phase_list):
        """
        Generates a list of components and their statuses which trigger Root Cause Analysis dumps.
        :param system_dictionary_root_cause_analysis:
        :return: The complete list of RCA triggers for the system.
        """

        root_cause_analysis_triggers_list = []

        for row in system_dictionary_root_cause_analysis.values():
            try:
                root_cause_analysis_triggers_list.extend(self.generate_root_cause_analysis_trigger_from_row(row,
                                                                                                            phase_list))
            except AttributeError:
                logging.info("Non-empty line with missing content present in the root_cause_analysis sheet."
                                "\nCheck row: %s", row)

        logging.debug("Extracted from system file root_cause_analysis_list = %s", root_cause_analysis_triggers_list)
        return root_cause_analysis_triggers_list
