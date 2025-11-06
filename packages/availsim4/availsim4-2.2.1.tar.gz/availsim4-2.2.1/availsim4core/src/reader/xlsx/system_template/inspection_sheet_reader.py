# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module for reading Minimal Replacable Unit sheet of the Excel-formatted input"""

import logging
from typing import List
from availsim4core.src.context.system.inspection import Inspection
from availsim4core.src.reader.xlsx.system_template.sheet_reader import SheetReader
from availsim4core.src.reader.xlsx import xlsx_utils
from availsim4core.resources.excel_strings import SystemTemplateInspectionsColumn

class InspectionSheetReader(SheetReader):
    """Class for reading entries of the Inspections sheet"""
    WORKSHEET = "INSPECTIONS"

    def generate_individual_inspection(self, row) -> Inspection:
        """Create an inspection object from a row describing it.

        Args:
            row

        Returns:
            An object of Inspection type.
        """
        exception_message_hint = f"inspection row: {row}"

        inspection_name_str = xlsx_utils.clean_str_cell(
            row, SystemTemplateInspectionsColumn.INSPECTION_NAME,
            exception_message_hint=exception_message_hint)

        inspection_period = xlsx_utils.clean_float_cell(
            row, SystemTemplateInspectionsColumn.INSPECTION_PERIOD)

        inspection_duration = xlsx_utils.clean_float_cell(
            row, SystemTemplateInspectionsColumn.INSPECTION_DURATION)

        inspection_comments = xlsx_utils.get_cell_text(row, SystemTemplateInspectionsColumn.COMMENTS, optional=True)

        return Inspection(inspection_name_str, inspection_period, inspection_duration, inspection_comments)

    def generate_inspections(self, system_dictionary_inspections) -> List[Inspection]:
        """
        Extract from the given system_dictionary_inspections the list of the inspection of the global system.
        :param system_dictionary_inspections: the system_dictionary inspections under the panda dictionary format.
        see> SystemTemplate
        :return: List of inspections of the global system.
        """

        inspections_list = []

        for row in system_dictionary_inspections.values():
            try:
                new_inspection = self.generate_individual_inspection(row)
                self.check_if_primary_key_already_defined(new_inspection.name, self.WORKSHEET)
                inspections_list.append(new_inspection)
            except AttributeError:
                logging.info("Non-empty line with missing content present in the Inspections sheet."
                             "\nCheck row: %s", row)

        logging.debug("Extracted from system file inspections_list = %s", inspections_list)

        return inspections_list
