# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module for reading Failure Modes sheet of the Excel-formatted input"""

import logging
from availsim4core.resources.excel_strings import SystemTemplateFailureModeColumn
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.reader.xlsx.system_template.sheet_reader import SheetReader
from availsim4core.src.reader.xlsx import xlsx_utils


class FailureModesSheetReader(SheetReader):
    """Class for reading Failure Modes sheet of the system file"""
    WORKSHEET = "FAILURE_MODES"

    def generate_individual_failure_mode(self, row, inspections_list, phase_list) -> FailureMode:
        """Create a single failure mode from the contents of the row."""
        exception_message_hint = f"failure mode row: {row}"

        # Extract values through grouping functions
        failure_mode_name, failure_distribution_name, failure_distribution_params = self.extract_failure_details(row,
                                                                                                 exception_message_hint)
        repair_distribution_name, repair_distribution_params = self.extract_repair_details(row, exception_message_hint)
        applicable_phases_names, held_after_repair, phase_change_trigger, next_phase_if_failure_name = \
                                                                self.extract_phase_details(row, exception_message_hint)
        repair_strategy = self.extract_optional_columns(row, exception_message_hint)

        # Other values
        type_of_failure_name = xlsx_utils.clean_str_cell(
            row, SystemTemplateFailureModeColumn.TYPE_OF_FAILURE, exception_message_hint)
        held_before_repair = xlsx_utils.clean_list_cell(row, SystemTemplateFailureModeColumn.HELD_BEFORE_REPAIR,
                                                        optional=True, exception_message_hint=exception_message_hint)
        inspection_name = xlsx_utils.read_clean_string_from_cell(row, SystemTemplateFailureModeColumn.INSPECTION_NAME,
                                                        optional=True)
        comments = xlsx_utils.get_cell_text(row, SystemTemplateFailureModeColumn.COMMENTS, optional=True)

        return FailureMode.build(failure_mode_name, failure_distribution_name, failure_distribution_params,
              repair_distribution_name, repair_distribution_params, type_of_failure_name,
              held_before_repair, inspection_name, applicable_phases_names, held_after_repair,
              phase_change_trigger, next_phase_if_failure_name, comments, inspections_list, phase_list, repair_strategy)

    def extract_failure_details(self, row, exception_message_hint):
        failure_mode_name = xlsx_utils.clean_str_cell(row, SystemTemplateFailureModeColumn.FAILURE_MODE_NAME,
                                                                 exception_message_hint)
        failure_distribution_name = xlsx_utils.clean_str_cell(
            row, SystemTemplateFailureModeColumn.FAILURE_LAW, exception_message_hint=exception_message_hint)
        failure_distribution_params = xlsx_utils.clean_list_cell(
            row, SystemTemplateFailureModeColumn.FAILURE_PARAMETERS, exception_message_hint=exception_message_hint)
        return failure_mode_name, failure_distribution_name, failure_distribution_params


    def extract_repair_details(self, row, exception_message_hint):
        repair_distribution_name = xlsx_utils.clean_str_cell(row, SystemTemplateFailureModeColumn.REPAIR_LAW,
                                                                        exception_message_hint=exception_message_hint)
        repair_distribution_params = xlsx_utils.clean_list_cell(row, SystemTemplateFailureModeColumn.REPAIR_PARAMETERS,
                                                                exception_message_hint=exception_message_hint)
        return repair_distribution_name, repair_distribution_params

    def extract_phase_details(self, row, exception_message_hint):
        applicable_phases_names = xlsx_utils.clean_list_cell(row, SystemTemplateFailureModeColumn.PHASE_NAME,
                                                             optional=True,
                                                             exception_message_hint=exception_message_hint)

        held_after_repair = xlsx_utils.clean_list_cell(row, SystemTemplateFailureModeColumn.HELD_AFTER_REPAIR,
                                                       optional=True, exception_message_hint=exception_message_hint)

        phase_change_trigger = xlsx_utils.read_clean_string_from_cell(row,
                SystemTemplateFailureModeColumn.PHASE_CHANGE_TRIGGER, optional=True)
        next_phase_if_failure_name = xlsx_utils.read_clean_string_from_cell(
            row, SystemTemplateFailureModeColumn.PHASE_NEXT_IF_FAILURE_NAME, optional=True)
        return applicable_phases_names, held_after_repair, phase_change_trigger, next_phase_if_failure_name

    def extract_optional_columns(self, row, exception_message_hint) -> str:
        repair_strategy = xlsx_utils.read_clean_string_from_cell(row, SystemTemplateFailureModeColumn.REPAIR_STRATEGY,
                                                        optional=True)
        return repair_strategy

    def generate_failure_modes(self, system_dictionary_failure_mode, inspections_list, phase_list):
        """
        Extract from the given system_dictionary_failure_mode the list of the FailureModes of the global system.
        :param system_dictionary_failure_mode: the system_dictionary failure mode under the panda dictionary format.
        see> SystemTemplate
        :param inspections_list: the list of inspections objects
        :param phase_list: List of phases {Phase}
        :return: List of FailureMode of the global system.
        """

        failure_modes_list = []

        for row in system_dictionary_failure_mode.values():
            try:
                new_failure_mode = self.generate_individual_failure_mode(row, inspections_list, phase_list)
                self.check_if_primary_key_already_defined(new_failure_mode.name, self.WORKSHEET)
                failure_modes_list.append(new_failure_mode)
            except AttributeError:
                logging.warning("Non-empty line with missing content present in the failure_modes sheet. It is skipped"
                             "\nCheck row: %s", row)
        logging.debug("Extracted from system file failure_modes_list: %s", failure_modes_list)
        return failure_modes_list
