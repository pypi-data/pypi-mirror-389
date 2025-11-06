# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for an Inspection class
"""

from typing import Optional
from availsim4core.src.context.system.system_element import SystemElement


class Inspection(SystemElement):
    """
    Defines the failure attributes based on a probability law.
    Also defines the repair attributes related to this failure based on a probability law.
    # TODO : Refactoring of this class introducing dedicated classes for the failure / repair / inspection :
    cf https://gitlab.cern.ch/availsim4/availsim4core/-/issues/30
    """
    __slots__ = 'name', 'periodicity', 'duration', 'comments'

    def __init__(self,
                 name,
                 inspection_periodicity: float,
                 inspection_duration: float,
                 comments: Optional[str] = ""):
        self.name: str = name
        self.periodicity: float = inspection_periodicity
        self.duration: float = inspection_duration
        super().__init__(comments)

    def __hash__(self):
        return hash((type(self), self.name))

    def __str__(self):
        return f"{self.name} :: every {self.periodicity} during {self.duration}"

    def __eq__(self, other):
        if not isinstance(other, Inspection):
            return NotImplemented
        return self.name == other.name
