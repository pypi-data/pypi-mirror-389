# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module for reading Architecture sheet of the Excel-formatted input"""

import logging
from typing import List
from availsim4core.resources.excel_strings import SystemTemplateFailureModeAssignmentsColumn
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.failure_mode_assignments import FailureModeAssignments
from availsim4core.src.reader.xlsx.system_template.sheet_reader import SheetReader
from availsim4core.src.reader.xlsx import xlsx_utils


class FailureModesAssignmentSheetReader(SheetReader):
    """Class reading Architecture sheet of the Excel-formatted input"""
    WORKSHEET = "FAILURE_MODES_ASSIGNMENT"

    def generate_individual_failure_mode_assignment(self, row,
                                                    failure_modes: List[FailureMode]) -> FailureModeAssignments:
        """This method creates an individual failure mode assignment object based on the contents of the row
        parameter"""
        exception_message_hint = f"failure mode assignements row: {row}"

        assignment_component_name = xlsx_utils.clean_str_cell(
            row, SystemTemplateFailureModeAssignmentsColumn.COMPONENT_NAME, exception_message_hint)
        assignment_failure_mode_name = xlsx_utils.clean_str_cell(
            row, SystemTemplateFailureModeAssignmentsColumn.FAILURE_MODE_NAME, exception_message_hint)
        assignment_comment = xlsx_utils.get_cell_text(row, SystemTemplateFailureModeAssignmentsColumn.COMMENTS,
                                                      optional=True)

        return FailureModeAssignments.build(assignment_component_name, assignment_failure_mode_name, assignment_comment,
                                            failure_modes)

    def generate_failure_mode_assignments(self, system_dictionary_assignments, failure_mode_list):
        """
        Generates failure mode assignments containing failure mode components by matching failure modes from the given
        `system_dictionary_assignments` with failure modes in the `failure modes list`.
        :param system_dictionary_assignments: The dictionary of failure assignments under the panda dataframe format.
        see> SystemTemplate.
        :param failure_mode_list: The List of Failure Mode to be associated to each of the FailureModeAssignment.
        :return: The complete list of the FailureModeAssignment for the system.
        """
        failure_mode_assignments_list = []
        for row in system_dictionary_assignments.values():
            try:
                new_assignment = self.generate_individual_failure_mode_assignment(row, failure_mode_list)
                self.check_if_primary_key_already_defined(new_assignment.component_name, self.WORKSHEET)
                failure_mode_assignments_list.append(self.generate_individual_failure_mode_assignment(row,
                                                                                                    failure_mode_list))
            except AttributeError:
                logging.info("Non-empty line with missing content present in the failure_mode_assignments sheet."
                             "\nCheck row: %s", row)
            except IndexError:
                logging.info("A failure mode might not have a defined assignment")

        logging.debug("Extracted from system file failure_mode_assignments_list = %s", failure_mode_assignments_list)
        return failure_mode_assignments_list
