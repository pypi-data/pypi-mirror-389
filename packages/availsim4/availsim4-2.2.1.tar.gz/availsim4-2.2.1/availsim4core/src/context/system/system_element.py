# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for the interface SystemElement.
"""

from typing import Optional
from abc import ABC


class SystemElement(ABC):
    """
    Abstract class to build classes representing elements of the modeled system, such as failure modes, inspections,
    MRUs, etc.
    """

    class MissingReferenceError(Exception):
        """This error is thrown when a reference to another part of the system is missing."""


    def __init__(self, comments: Optional[str]) -> None:
        self.comments: str = ""
        if comments is not None:
            self.comments = comments

    def __repr__(self):
        return str(self)
