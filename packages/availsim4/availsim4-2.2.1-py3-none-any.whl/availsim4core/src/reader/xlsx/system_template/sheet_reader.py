# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module of the SheetReader abstract class"""

from abc import ABC
import logging

class SheetReader(ABC):
    """Abstract class for readers with one required `read` method"""

    class DuplicatedEntry(Exception):
        """Exception raised when more than one entry (component, failure mode, others) in a sheet has the same name."""

    def __init__(self) -> None:
        super().__init__()
        self.primary_keys = []

    def check_if_primary_key_already_defined(self, new_name: str, worksheet_name: str = "-") -> None:
        """Checks if an element defined by a sheet reader is already in the list of defined names. If so, throws an
        exception.

        Args:
            new_name
                A string specifying name which is about to be added to the system
            worksheet_name
                A string specififying in which worksheet the name is located. In case of a duplicate entry, it will be
                used to construct the exception message"""
        if new_name in self.primary_keys:
            msg = f"The component name {new_name} is duplicated in the sheet {worksheet_name}."
            logging.exception(msg)
            raise self.DuplicatedEntry(msg)
        self.primary_keys.append(new_name)
