# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for a FailureMode class
"""

import logging
from typing import Optional, Set, List, Type, TypeVar
import numpy

from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system import failure_factory
from availsim4core.src.context.system.failure import Failure, FailureType
from availsim4core.src.context.system.inspection import Inspection
from availsim4core.src.context.system.probability_law import probability_law_factory
from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw
from availsim4core.src.context.system.system_element import SystemElement


class FailureModeError(Exception):
    """
    Error raised when initialiation of FailureMode goes wrong. For example, when a wrong combination of a failure type
    (BLIND) and a phase change trigger (AFTER_REPAIR) is defined in the input, the error informs the user that it will
    never occur.
    """


T = TypeVar('T', bound="FailureMode")


class FailureMode(SystemElement):
    """
    Defines the failure attributes based on a probability law.
    Also defines the repair attributes related to this failure based on a probability law.
    # TODO : Refactoring of this class introducing dedicated classes for the failure / repair / inspection:
    cf https://gitlab.cern.ch/availsim4/availsim4core/-/issues/30
    """
    __slots__ = 'name', 'failure_law', 'repair_law', 'failure', 'held_before_repair_phase_set', 'inspection', \
                'phase_set', 'failure_mode_next_phase_if_failure', 'phase_change_trigger', \
                'held_after_repair_phase_set', 'uniform_samples_for_quasi_monte_carlo', 'sample_generation_time', \
                'comments'

    def __init__(self,
                 name: str,
                 failure_law: ProbabilityLaw,
                 repair_law: ProbabilityLaw,
                 failure: Failure,
                 held_before_repair_phase_set: Set[Phase],
                 inspection: Optional[Inspection],
                 phase_set: Set[Phase],
                 failure_mode_next_phase_if_failure: Optional[Phase],
                 phase_change_trigger: Optional[str],
                 held_after_repair_phase_set: Set[Phase],
                 comments: Optional[str] = "",
                 repair_strategy: Optional[str] = ""):

        if failure.type_of_failure == FailureType.BLIND and phase_change_trigger == 'AFTER_REPAIR':
            message = f"Wrong combination of type_of_failure ({failure}) " \
                      f"and phase_change_timing ({phase_change_trigger}) " \
                      f"for the failure mode named {name}"
            logging.exception(message)
            raise FailureModeError(message)

        self.name: str = name
        self.failure_law: ProbabilityLaw = failure_law
        self.repair_law: ProbabilityLaw = repair_law
        self.failure: Failure = failure
        self.held_before_repair_phase_set: Set[Phase] = held_before_repair_phase_set
        self.inspection: Optional[Inspection] = inspection
        self.phase_set: Set[Phase] = phase_set
        self.failure_mode_next_phase_if_failure: Phase = failure_mode_next_phase_if_failure
        self.phase_change_trigger: str = "NEVER"
        self.held_after_repair_phase_set: Set[Phase] = held_after_repair_phase_set
        self.uniform_samples_for_quasi_monte_carlo: List[numpy.ndarray] = []
        self.sample_generation_time: float = 0.0
        self.repair_strategy = repair_strategy

        if phase_change_trigger is not None and phase_change_trigger != "":
            self.phase_change_trigger = phase_change_trigger

        if repair_strategy is None or repair_strategy == "":
            self.repair_strategy = "OPTIMAL"

        super().__init__(comments)

    def __hash__(self):
        return hash((type(self), self.name))

    def __str__(self):
        return (f"{self.name} :: "
                f"{self.failure_law} / "
                f"{self.repair_law} / "
                f"{self.failure} / "
                f"{[phase.name for phase in self.held_before_repair_phase_set]} / "
                f"{self.inspection} / "
                f"{[phase.name for phase in self.phase_set]} / "
                f"{self.phase_change_trigger} /"
                f"{[phase.name for phase in self.held_after_repair_phase_set]}")

    def __eq__(self, other):
        if not isinstance(other, FailureMode):
            return NotImplemented
        return self.name == other.name

    def set_uniform_samples_for_quasi_monte_carlo(self, uniform_samples_for_quasi_monte_carlo: numpy.ndarray) -> None:
        """
        TODO: refactor the method so that FailureMode is not concerned with Quasi MC stuff
        """
        self.uniform_samples_for_quasi_monte_carlo = list(uniform_samples_for_quasi_monte_carlo)

    @classmethod
    def build(cls: Type[T], component_name: str, failure_distribution_name: str,
              failure_distribution_params: List[float], repair_distribution_name: str,
              repair_distribution_params: List[float], failure_type_name: str, held_before_repair_in_phases: List[str],
              inspection_name: str, applicable_phases_names: List[str], held_after_repair_in_phases: List[str],
              phase_change_trigger: str, next_phase_name_if_failure: str, comments: str,
              global_inspection_list: List[Inspection], global_phase_list: List[Phase], repair_strategy: str = "") -> T:
        """
        This method is used for creating the FailureMode objects from strings and lists of strings or floats.
        """

        def process_phase_constraints(cell_content: List[str], all_phases: List[Phase]) -> Set[Phase]:
            failure_mode_held_phase_set: Optional[Set[Phase]] = None
            if len(cell_content) == 0 or cell_content[0] == "NEVER_HELD":
                # Default option - failure mode applicable in all phases
                failure_mode_held_phase_set = set(all_phases)
            elif cell_content[0] == "HELD_FOREVER":
                # Special phase used to never release some held components
                failure_mode_held_phase_set = set([PhaseManager.HELD_FOREVER])
            else:
                failure_mode_held_phase_set = set([phase for phase in all_phases if phase.name in cell_content])
            return failure_mode_held_phase_set

        failure_law = probability_law_factory.build(failure_distribution_name, failure_distribution_params)
        repair_law = probability_law_factory.build(repair_distribution_name, repair_distribution_params)
        failure_type = failure_factory.build(failure_type_name)

        if len(applicable_phases_names) == 0 or applicable_phases_names[0] == "NONE":
            # if user decides to not provide any name or use a keyword -> apply all existing phases
            applicable_phases =  set(global_phase_list)
        else:
            applicable_phases = {phase for phase in global_phase_list if phase.name in applicable_phases_names}

        inspection = next((inspection for inspection in global_inspection_list if inspection.name == inspection_name),
                          None)

        held_before_phase = process_phase_constraints(held_before_repair_in_phases, global_phase_list)
        held_after_phase = process_phase_constraints(held_after_repair_in_phases, global_phase_list)

        next_phase_if_failure = None
        if next_phase_name_if_failure not in []:
            for phase in global_phase_list:
                if phase.name == next_phase_name_if_failure:
                    next_phase_if_failure = phase

        return FailureMode(component_name, failure_law, repair_law, failure_type, held_before_phase, inspection,
                           applicable_phases, next_phase_if_failure, phase_change_trigger, held_after_phase, comments,
                           repair_strategy)
