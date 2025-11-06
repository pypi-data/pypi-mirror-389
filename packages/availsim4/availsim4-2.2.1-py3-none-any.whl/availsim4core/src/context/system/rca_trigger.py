# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module for the RootCauseAnalysisTrigger which is an input for the RCA feature of the AvailSim4"""

from typing import List, Optional, Type, TypeVar

from availsim4core.src.context.system.system_element import SystemElement


T = TypeVar('T', bound="RootCauseAnalysisTrigger")


class RootCauseAnalysisTrigger(SystemElement):
    """Describes triggers set for the Root Cause Analysis feature.

    Args:
        component_name
            The name of the component which will trigger an RCA snapshot of the system when it's status changes
        component_status
            This string specifies the status which will trigger the RCA snapshot
        phase
            This string specifies which phases the trigger should be applicable in.
    """

    def __init__(self, component_name: str, component_status: str, phase: str, comments: Optional[str] = ""):
        self.component_name = component_name
        self.component_status = component_status
        self.phase = phase
        super().__init__(comments)

    def __str__(self):
        return f"RCA trigger on {self.component_name}, status {self.component_status} in phase {self.phase}"

    def __hash__(self):
        return hash((self.component_name, self.component_status, self.phase))

    def __eq__(self, other):
        if not isinstance(other, RootCauseAnalysisTrigger):
            return NotImplemented
        return self.component_name == other.component_name and \
               self.component_status == other.component_status and \
               self.phase == other.phase

    @classmethod
    def build(cls: Type[T],
              triggering_component_name: str,
              triggering_component_statuses: List[str],
              triggering_phases: List[str],
              comments: str = "") -> List[T]:
        """Build method for the RootCauseAnalysisTrigger class.

        Args:
            triggering_component_name
                The component's name upon which statuses the RCA trigger will act.
            triggering_component_statuses
                This is expected to be a list of strings specifying statuses which will trigger the RCA snapshot when
                the component identified in the first argument enters them.
            triggering_phases
                A list of phase names in which the trigger will be active.
            comments
                Optional, this string is for users to provide additional information regarding the trigger.

        Returns:
            List of RootCausesAnalysisTrigger objects for each component status and each phase specified in the
            arguments to the method."""
        return [RootCauseAnalysisTrigger(triggering_component_name, status, phase, comments)
                for status in triggering_component_statuses
                for phase in triggering_phases]
