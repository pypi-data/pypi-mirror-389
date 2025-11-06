# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module for reading Phases sheet of the Excel-formatted input"""


import logging
from typing import Dict
from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.reader.xlsx import xlsx_utils
from availsim4core.resources.excel_strings import SystemTemplatePhasesColumn
from availsim4core.src.reader.xlsx.system_template.sheet_reader import SheetReader


class PhasesSheetReader(SheetReader):
    """Class for reading entries in the Phases sheet of the Excel workbook."""
    WORKSHEET = "PHASES"

    def __init__(self):
        super().__init__()
        self.dict_name_next_phase: Dict[Phase, str] = {}
        self.dict_name_next_phase_if_failure: Dict[Phase, str] = {}

    def generate_phase(self, row) -> Phase:
        """Create an individual object of the Phase class from the contents of a row (containing columns as described
        in the user guide).
        """
        exception_message_hint = f"phases row: {row}"

        phase_name = xlsx_utils.clean_str_cell(row, SystemTemplatePhasesColumn.PHASE_NAME,
                                                              exception_message_hint)

        phase_distribution_name = xlsx_utils.clean_str_cell(row, SystemTemplatePhasesColumn.PHASE_LAW,
                                                             exception_message_hint)

        phase_distribution_parameters = xlsx_utils.clean_list_cell(row, SystemTemplatePhasesColumn.PHASE_PARAMETERS,
                                                                   optional=False,
                                                                   exception_message_hint=exception_message_hint)

        phase_next_name_str = xlsx_utils.clean_str_cell(row, SystemTemplatePhasesColumn.PHASE_NEXT,
                                                                   exception_message_hint)

        is_first_phase = xlsx_utils.clean_boolean_cell(row, SystemTemplatePhasesColumn.PHASE_FIRST,
                                                                    exception_message_hint, optional=True)

        next_phase_if_failure_name = xlsx_utils.read_cell_str_with_default(
            row, SystemTemplatePhasesColumn.PHASE_NEXT_IF_FAILURE, exception_message_hint, "NONE")

        phase_comment = xlsx_utils.get_cell_text(row, SystemTemplatePhasesColumn.COMMENTS, optional=True)

        return Phase.build(phase_name, phase_distribution_name, phase_distribution_parameters, is_first_phase,
                           phase_next_name_str, next_phase_if_failure_name, phase_comment)

    def assign_successor_phases(self, phases_by_names: Dict[str, Phase]):
        """This method goes through the supplied list of phases and sets their 'next_phase' and 'next_phase_if_failure'
        fields to existing phase objects."""
        for phase in phases_by_names.values():
            phase.find_next_phase(phases_by_names)
            phase.find_next_phase_if_failure(phases_by_names)

    def generate_phases(self, system_dictionary_phases):
        """
        Extract from the given `system_dictionary_phase` the list of the {Phase} of the global system.
        :param system_dictionary_phases: the system_dictionary_phases under the panda dictionary format.
        :return: List of {Phase} of the global system.
        """

        phases_by_names: Dict[str, Phase] = {}

        for row in system_dictionary_phases.values():
            try:
                new_phase = self.generate_phase(row)
                self.check_if_primary_key_already_defined(new_phase.name, self.WORKSHEET)
                phases_by_names[new_phase.name] = new_phase
            except AttributeError:
                logging.info("Non-empty line with missing content present in the Phases sheet."
                                "\nCheck row: %s", row)

        self.assign_successor_phases(phases_by_names)

        if not phases_by_names:
            return [PhaseManager.NO_PHASE]  # Default is NO_PHASE

        logging.debug("Extracted from system file phases_list = %s", phases_by_names)

        return list(phases_by_names.values())
