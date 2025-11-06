# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for the FailureModeAssignment class. Represents mappings from FailureMode objects to the relevant Component ones.
"""

import logging
from typing import List, Optional, Type, TypeVar
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.system_element import SystemElement


T = TypeVar('T', bound="SystemElement")


class FailureModeAssignments(SystemElement):
    """
    Objects of this class contains just two elements: a reference to a component and a relevant failure mode.
    Optionally, it may store a user-defined comment related to the mapping.
    """
    __slots__ = 'component_name', 'failure_mode'

    def __init__(self, component_name: str, failure_mode: FailureMode, comments: Optional[str] = ""):
        self.component_name: str = component_name
        self.failure_mode: FailureMode = failure_mode
        super().__init__(comments)

    def __eq__(self, other):
        if not isinstance(other, FailureModeAssignments):
            return NotImplemented
        return self.component_name == other.component_name and \
               self.failure_mode == other.failure_mode

    def __repr__(self):
        return f"component_name: {self.component_name} -> " \
               f"failure_mode.name: {self.failure_mode.name}"

    @classmethod
    def build(cls: Type[T], component_name: str, failure_mode_name: str, comments: str,
              failure_modes: List[FailureMode]) -> T:
        """
        Build method for the FailureModeAssignments objects. Produces an object from two strings identifying the
        component and the corresponding failure mode.

        Args:
            component_name
                A string specifying the name of the component which is supposed to have the failure mode.
            failure_mode_name
                A string specifying the name of the failure mode.

        Returns:
            A newly-created FailureModeAssignment object.

        Raises:

        """
        failure_mode = next((failure_mode for failure_mode in failure_modes if failure_mode.name == failure_mode_name),
                            None)
        if failure_mode is None:
            msg = "Creation of a new failure mode assignment has failed. A corresponding failure mode has not been" \
                  "found in the system."
            logging.error(msg)
            raise cls.MissingReferenceError(msg)
        return FailureModeAssignments(component_name, failure_mode, comments)
