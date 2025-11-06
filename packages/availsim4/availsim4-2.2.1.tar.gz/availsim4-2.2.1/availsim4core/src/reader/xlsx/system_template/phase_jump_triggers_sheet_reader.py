# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module for reading Phase Jump Triggers sheet of the Excel-formatted input"""

import logging
from typing import List
from availsim4core.resources.excel_strings import SystemTemplatePhaseJumpColumn
from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.system.phase_jump_trigger import PhaseJumpTrigger
from availsim4core.src.reader.xlsx import xlsx_utils
from availsim4core.src.reader.xlsx.system_template.sheet_reader import SheetReader


class PhaseJumpTriggersSheetReader(SheetReader):
    """Class for reading the content of the phase jump triggers sheet of the Excel input"""

    def generate_phase_jump_triggers_from_row(self, row, phase_list: List[Phase]) -> List[PhaseJumpTrigger]:
        """Create a list of objects defined by the row parameter"""
        exception_message_hint = f"phase jump row: {row}"

        phase_jump_trigger_component_name = xlsx_utils.clean_str_cell(
            row, SystemTemplatePhaseJumpColumn.COMPONENT_NAME, exception_message_hint)
        phase_jump_trigger_component_status_list = xlsx_utils.clean_list_cell(
            row, SystemTemplatePhaseJumpColumn.COMPONENT_STATUS, optional=False,
            exception_message_hint=exception_message_hint)
        phase_jump_trigger_from_phase_list = xlsx_utils.clean_list_cell(
            row, SystemTemplatePhaseJumpColumn.FROM_PHASE, optional=True,
            exception_message_hint=exception_message_hint)
        phase_jump_trigger_to_phase = xlsx_utils.clean_str_cell(
            row, SystemTemplatePhaseJumpColumn.TO_PHASE, exception_message_hint)
        phase_jump_trigger_comments = xlsx_utils.get_cell_text(row, SystemTemplatePhaseJumpColumn.COMMENTS,
                                                               optional=True)

        return PhaseJumpTrigger.build(phase_jump_trigger_component_name, phase_jump_trigger_component_status_list,
                                      phase_jump_trigger_from_phase_list, phase_jump_trigger_to_phase, phase_list,
                                      phase_jump_trigger_comments)

    def generate_phase_jump_triggers(self, system_dictionary_phase_jump, phase_list: List[Phase]):
        """
        Generates a list of (component, status, in_phase, jump_to_phase) which trigger phase jumps.
        :param system_dictionary_phase_jump:
        :return: The complete list of phase jump triggers.
        """

        phase_jump_triggers_list = []

        for row in system_dictionary_phase_jump.values():
            try:
                new_phase_jump_triggers = self.generate_phase_jump_triggers_from_row(row, phase_list)
                self._check_if_phase_jump_destinations_disjoint(new_phase_jump_triggers)
                phase_jump_triggers_list.extend(new_phase_jump_triggers)
            except AttributeError:
                logging.info("Non-empty line with missing content present in the phase_jump sheet."
                             "\nCheck row: %s", row)
        logging.debug("Extracted from system file phase_jump_triggers_list = %s", phase_jump_triggers_list)
        return phase_jump_triggers_list

    @staticmethod
    def _check_if_phase_jump_destinations_disjoint(triggers: List[PhaseJumpTrigger]) -> None:
        for trigger in triggers:
            if trigger.from_phase == trigger.to_phase:
                # not `if trigger.to_phase in tigger.from_phase` since phases grouped in "from" field are separated when
                # creating the PhaseJumpTrigger objects, with each having a separate one
                message = (f"The same phase ({trigger.to_phase}) is specified both in the FROM_PHASE and TO_PHASE "
                           f"fields of a phase jump trigger set on the component {trigger.component_name} with status "
                           f"{trigger.component_status}.")
                logging.warning(message)
