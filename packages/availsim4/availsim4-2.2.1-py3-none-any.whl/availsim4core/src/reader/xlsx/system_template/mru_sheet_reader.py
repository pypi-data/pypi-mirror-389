# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module for reading Minimal Replacable Unit sheet of the Excel-formatted input"""


import logging
from typing import List
from availsim4core.src.context.system.minimal_replaceable_unit import MinimalReplaceableUnit
from availsim4core.src.reader.xlsx.system_template.sheet_reader import SheetReader
from availsim4core.src.reader.xlsx import xlsx_utils
from availsim4core.resources.excel_strings import SystemTemplateMinimalReplaceableUnitColumn


class MinimalReplaceableUnitSheetReader(SheetReader):
    """Class for reading entries of Minimal Replaceable Unit sheet"""
    WORKSHEET = "MINIMAL REPLACABLE UNITS"

    def generate_mru_from_row(self, row, root_component_name: str) -> List[MinimalReplaceableUnit]:
        """Generate a list of Minimal Replacable Unit objects defined in the row parameter.

        Args
            row

            root_component_name
                String, definining the root component of the system. It will be used as a default value when there is no
                scope defined.

        Returns:
            A list of MinimalReplaceableUnit objects created from the row.
        """
        exception_message_hint = f"mru row: {row}"

        mru_name_str = xlsx_utils.clean_str_cell(
            row, SystemTemplateMinimalReplaceableUnitColumn.MINIMAL_REPLACEABLE_UNIT_NAME,
            exception_message_hint=exception_message_hint)

        mru_repair_law_name = xlsx_utils.clean_str_cell(
            row, SystemTemplateMinimalReplaceableUnitColumn.REPAIR_LAW,
            exception_message_hint=exception_message_hint)

        mru_repair_parameters = row[SystemTemplateMinimalReplaceableUnitColumn.REPAIR_PARAMETERS]
        mru_repair_parameters = [mru_repair_parameters] if isinstance(mru_repair_parameters, (int, float)) \
            else xlsx_utils.clean_list_cell(row, SystemTemplateMinimalReplaceableUnitColumn.REPAIR_PARAMETERS,
                                            exception_message_hint=exception_message_hint)

        minimal_replaceable_repair_schedule = xlsx_utils.read_cell_str_with_default(row,
            SystemTemplateMinimalReplaceableUnitColumn.REPAIR_SCHEDULE, exception_message_hint, "None")

        lowest_common_parent_name_list = xlsx_utils.read_cell_list_with_default(
            row, SystemTemplateMinimalReplaceableUnitColumn.LOWEST_COMMON_ANCESTOR, exception_message_hint,
            root_component_name)

        triggering_status_list_of_str = xlsx_utils.clean_list_cell(
            row, SystemTemplateMinimalReplaceableUnitColumn.TRIGGERING_STATUS,
            exception_message_hint=exception_message_hint)

        mru_comments = xlsx_utils.get_cell_text(row, SystemTemplateMinimalReplaceableUnitColumn.COMMENTS, optional=True)

        return MinimalReplaceableUnit.build(mru_name_str,
                                            mru_repair_law_name,
                                            mru_repair_parameters,
                                            minimal_replaceable_repair_schedule,
                                            triggering_status_list_of_str,
                                            lowest_common_parent_name_list,
                                            mru_comments)

    def generate_mrus(self, system_dictionary_mru, root_component_name: str):
        """
        Extract from the given system_dictionary_mru the list of the MRUs of the global system.
        :param system_dictionary_mru: the system_dictionary mru under the panda dictionary format.
        see> SystemTemplate
        :return: List of Minimal Replaceable Unit of the global system.
        """
        mru_list = []

        for row in system_dictionary_mru.values():
            try:
                new_mrus = self.generate_mru_from_row(row, root_component_name)
                mru_list.extend(new_mrus)
            except AttributeError:
                logging.info("Non-empty line with missing content present in the MRU sheet.\n"
                             "Check row: %s", row)

        logging.debug("Extracted from system file mru_list: %s", mru_list)

        return mru_list
