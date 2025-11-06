# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for PhaseJumpTrigger class
"""

import logging
from typing import List, Optional, Type, TypeVar

from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.system_element import SystemElement

T = TypeVar('T', bound="PhaseJumpTrigger")


class PhaseJumpTrigger(SystemElement):
    """
    Objects of this class represent triggers of phase jumps, which can be defined by users in the
    `PHASE_JUMP_TRIGGERS` sheet of the input file.
    """

    def __init__(self, component_name: str, component_status: Status, from_phase: Phase,to_phase: Phase,
                 comments: Optional[str] = ""):
        self.component_name: str = component_name
        self.component_status: Status = component_status
        self.from_phase: Phase = from_phase
        self.to_phase: Phase = to_phase
        super().__init__(comments)

    def __str__(self):
        return f"Phase Jump trigger on {self.component_name}, "\
        f"status {self.component_status} from phase {self.from_phase} to phase {self.to_phase}"

    def __hash__(self):
        return hash((self.component_name, self.component_status,
                     self.from_phase, self.to_phase))

    def __eq__(self, other):
        if not isinstance(other, PhaseJumpTrigger):
            return NotImplemented
        return self.component_name == other.component_name and \
               self.component_status == other.component_status and \
               self.from_phase == other.from_phase and \
               self.to_phase == other.to_phase

    @classmethod
    def build(cls: Type[T],
              triggering_component_name: str,
              triggering_component_status_list: List[str],
              triggering_from_phase_list: List[str],
              triggering_to_phase: str,
              phase_list: List[Phase],
              comments: str = "") -> List[T]:
        """
        A builder of PhaseJumpTrigger objects. Returns a list of those based on input arguments,
        creating as many PhaseJumpTrigger objects as many combinations of elements of lists specifying
        triggering statuses and applicable phases. Each PhaseJumpTrigger can have only one of those.
        """

        if len(triggering_from_phase_list) == 0 or triggering_from_phase_list[0] == "NONE":
            triggering_from_phase_list = [phase.name for phase in phase_list]
        try:
            return [PhaseJumpTrigger(
                        triggering_component_name,
                        Status(status),
                        next(phase for phase in phase_list if phase.name == from_phase),
                        next(phase for phase in phase_list if phase.name == triggering_to_phase),
                        comments
                    )
                    for status in triggering_component_status_list
                    for from_phase in triggering_from_phase_list]
        except StopIteration:
            logging.error("Phase %s has invalid originating or destination phase specified in the PHASE_JUMP sheet.",
                          triggering_component_name)
            return []
