# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from typing import Set

import numpy

from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.system.phase_jump_trigger import PhaseJumpTrigger
from availsim4core.src.context.system.probability_law.deterministic_law import DeterministicLaw
from availsim4core.src.timeline.record_phase import RecordPhase


class PhaseManager:
    """
    This class provides all the methods to manipulate {Phase}.
    Note : When no {Phase} is defined in the simulation. The NO_PHASE is used by default.
    """
    __slots__ = 'phase_set', 'current_phase', 'phase_jump_trigger_set'

    NO_PHASE = Phase("NONE", DeterministicLaw([numpy.inf]), True)
    NO_PHASE.set_next_phase(NO_PHASE)
    NO_PHASE.set_next_phase_if_failure(NO_PHASE)

    HELD_FOREVER = Phase("HELD_FOREVER", DeterministicLaw([numpy.inf]), False)
    HELD_FOREVER.set_next_phase(HELD_FOREVER)
    HELD_FOREVER.set_next_phase_if_failure(HELD_FOREVER)

    DEFAULT_PHASE_DESCRIPTION = "default"
    DEFAULT_PHASE_IF_FAILURE_DESCRIPTION = "default failure"
    SPECIFIC_PHASE_IF_FAILURE_DESCRIPTION = "specific failure"
    JUMP_INTO_PHASE_DESCRIPTION = "jump into phase"
    UPDATE_FOLLOWING_A_PHASE_CHANGE = "Update following a phase change"

    def __init__(self,
                 phase_set: Set[Phase],
                 phase_jump_trigger_set: Set[PhaseJumpTrigger]):
        self.phase_set: Set[Phase] = phase_set
        self.current_phase = self._get_first_phase()
        self.phase_jump_trigger_set = phase_jump_trigger_set

    def __eq__(self, other):
        return self.phase_set == other.phase_set and \
               self.current_phase == other.current_phase and \
               self.phase_jump_trigger_set == other.phase_jump_trigger_set


    def __str__(self):
        return f"Current Phase -> {self.current_phase}"

    def _get_first_phase(self) -> Phase:
        """
        Find the first {Phase} of the simulation.
        :return: The first {Phase} of the simulation, NO_PHASE otherwise.
        """
        return next((phase
                     for phase in self.phase_set
                     if phase.is_first_phase), PhaseManager.NO_PHASE)

    def _find_phase(self, phase_name_to_find: str) -> Phase:
        """
        Given a string name of phase, this methods returns the corresponding {Phase} is defined in the init list.
        If the `phase_name_to_find` is not found, returns the NO_PHASE.
        :param phase_name_to_find: the str name of the phase to find.
        :return: {Phase} with the given `phase_name_to_find`, NO_PHASE otherwise.
        """
        return next((phase
                     for phase in self.phase_set
                     if phase.name == phase_name_to_find), PhaseManager.NO_PHASE)

    def go_to_phase(self,
                    phase_start_time: float,
                    phase: Phase,
                    description: str) -> RecordPhase:
        """
        Updating the "current_phase" of the phase manager
        """
        self.current_phase = phase
        return RecordPhase(self.current_phase,
                           phase_start_time,
                           description)
