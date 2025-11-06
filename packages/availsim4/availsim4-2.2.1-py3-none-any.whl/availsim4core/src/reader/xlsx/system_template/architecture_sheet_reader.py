# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module for reading Architecture sheet of the Excel-formatted input"""

import logging
from typing import List
from availsim4core.src.context.system.architecture_entry import ArchitectureEntry
from availsim4core.src.reader.xlsx import xlsx_utils
from availsim4core.resources.excel_strings import SystemTemplateArchitectureColumn
from availsim4core.src.reader.xlsx.system_template.sheet_reader import SheetReader


class ArchitectureSheetReader(SheetReader):
    """Class for reading entries from the Architecture sheet"""
    WORKSHEET = "ARCHITECTURE"

    def generate_architecture_entry(self, row):
        """This method reads a row from a dataframe containing the Architecture table and produces an ArchitectureEntry
        object."""
        exception_message_hint = f"architecture row: {row}"
        logging.debug("Reading: %s", exception_message_hint)

        component_name_str = xlsx_utils.clean_str_cell(row, SystemTemplateArchitectureColumn.COMPONENT_NAME,
                                                            exception_message_hint=exception_message_hint)
        component_type_str = xlsx_utils.clean_str_cell(row, SystemTemplateArchitectureColumn.COMPONENT_TYPE,
                                                            exception_message_hint=exception_message_hint)
        component_number = xlsx_utils.clean_int_cell(row, SystemTemplateArchitectureColumn.COMPONENT_NUMBER,
                                                            exception_message_hint=exception_message_hint)
        children_name_list = xlsx_utils.read_cell_list_with_default(row, SystemTemplateArchitectureColumn.CHILDREN_NAME,
                                                                    exception_message_hint)
        children_logic_str = xlsx_utils.read_cell_str_with_default(row, SystemTemplateArchitectureColumn.CHILDREN_LOGIC,
                                                                   exception_message_hint, "")
        in_mru_str_list = xlsx_utils.read_cell_list_with_default(row, SystemTemplateArchitectureColumn.IN_MRU,
                                                                 exception_message_hint)
        trigger_mru_str_list = xlsx_utils.read_cell_list_with_default(row, SystemTemplateArchitectureColumn.TRIGGER_MRU,
                                                                      exception_message_hint)
        comments = xlsx_utils.get_cell_text(row, SystemTemplateArchitectureColumn.COMMENTS, optional=True)

        return ArchitectureEntry(component_name_str,
                                 component_type_str,
                                 component_number,
                                 children_name_list,
                                 children_logic_str,
                                 in_mru_str_list,
                                 trigger_mru_str_list,
                                 comments)

    def generate_architecture_entry_list(self, system_dictionary_architecture) -> List[ArchitectureEntry]:
        """
        Generate a list of ArchitectureEntry objects for a given dataframe containing Architecture worksheet content

        Args:
            system_dictionary_architecture

        Returns:
            List of {ArchitectureEntry} of the system defined in the dataframe provided as the argument.
        """
        architecture_entry_list = []

        for row in system_dictionary_architecture.values():
            try:
                new_entry = self.generate_architecture_entry(row)
                self.check_if_primary_key_already_defined(new_entry.component_name, self.WORKSHEET)
                architecture_entry_list.append(new_entry)
            except AttributeError:
                logging.info("A non-empty line with missing content is present in the architecture sheet."
                             "\nCheck the row: %s", row)
        logging.debug("Extracted from system file architecture_entry_list: %s", architecture_entry_list)
        return architecture_entry_list
