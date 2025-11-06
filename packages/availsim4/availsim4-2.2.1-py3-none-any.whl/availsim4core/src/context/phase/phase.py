# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for the Phase class.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Type, TypeVar
from availsim4core.src.context.system.probability_law import probability_law_factory

from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw


T = TypeVar('T', bound="Phase")


class Phase:
    """
    Class dealing with phases, defining each of them
    """
    __slots__ = 'name', 'law', 'next', 'next_phase_name', 'is_first_phase', 'next_phase_if_failure', \
        'next_phase_if_failure_name', 'comments'

    def __init__(self,
                 phase_name: str,
                 phase_law: ProbabilityLaw,
                 phase_first: bool,
                 next_phase_name: str = "NONE",
                 next_phase_if_failure_name: str = "NONE",
                 comments: str = ""):
        self.name: str = phase_name
        self.law: ProbabilityLaw = phase_law
        self.next: Optional[Phase] = None
        self.next_phase_name: str = next_phase_name
        self.is_first_phase: bool = phase_first
        self.next_phase_if_failure: Optional[Phase] = None
        self.next_phase_if_failure_name: str = next_phase_if_failure_name
        self.comments: str = comments

    def set_next_phase(self, next_phase: Phase):
        """This method sets the next phase phase to be ran after the current one finishes."""
        self.next = next_phase

    def set_next_phase_if_failure(self, next_phase_if_failure: Phase):
        """This method sets the next phase to run if the current one is a failure."""
        self.next_phase_if_failure = next_phase_if_failure

    def find_next_phase(self, phases_by_names: Dict[str, Phase]):
        """This method sets the next phase phase to be ran after the current one finishes."""
        self.next = phases_by_names[self.next_phase_name]

    def find_next_phase_if_failure(self, phases_by_names: Dict[str, Phase]):
        """This method sets the next phase to run if the current one is a failure."""
        if self.next_phase_if_failure_name != "NONE":
            self.next_phase_if_failure = phases_by_names[self.next_phase_if_failure_name]

    def __hash__(self):
        return hash((type(self), self.name))

    def __eq__(self, other):
        if not isinstance(other, Phase):
            return NotImplemented
        return self.name == other.name

    def __str__(self):
        if self.next is None or self.next_phase_if_failure is None:
            return (f"Phase name:{self.name} ~ "
                    f"law:{self.law} ~ "
                    f"first:{self.is_first_phase} ~ ")
        return (f"Phase name:{self.name} ~ "
                f"law:{self.law} ~ "
                f"next:{self.next.name} ~ "
                f"first:{self.is_first_phase} ~ "
                f"next if failure:{self.next_phase_if_failure.name}")

    @classmethod
    def build(cls: Type[T], name: str, distribution_name: str, distribution_parameters: List[float], is_first: bool,
              next_phase_name: str, next_phase_if_failure_name: str, comments: str) -> T:
        """
        Method to create objects of the Phase class using strings and lists of parameters.
        """
        probability_law = probability_law_factory.build(distribution_name, distribution_parameters)
        return Phase(name, probability_law, is_first, next_phase_name, next_phase_if_failure_name, comments)
