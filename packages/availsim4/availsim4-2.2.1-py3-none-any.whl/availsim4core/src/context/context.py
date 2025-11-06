# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Set

if TYPE_CHECKING:
    from availsim4core.src.context.system.component_tree.component import Component

from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.rca.rca_manager import RootCauseAnalysisManager
from availsim4core.src.timeline.record_component import RecordComponent
from availsim4core.src.timeline.timeline import Timeline


class Context:
    """
    This class represents the overall context state during a discrete event simulation.
    """
    __slots__ = 'root_component', 'phase_manager', 'timeline_record', 'b_events_set', 'c_events_set', 'absolute_simulation_time'

    def __init__(self,
                 root_component: Component,
                 phase_manager: PhaseManager,
                 rca_manager: Optional[RootCauseAnalysisManager] = None,
                 b_events_set: Optional[Set] = None,
                 c_events_set: Optional[Set] = None):
        self.root_component = root_component
        self.phase_manager = phase_manager
        self.timeline_record = Timeline(rca_manager)
        if b_events_set is None:
            self.b_events_set = set()
        else:
            self.b_events_set = b_events_set
        if c_events_set is None:
            self.c_events_set = set()
        else:
            self.c_events_set = c_events_set
        self.absolute_simulation_time = 0

    def __eq__(self, other):
        return self.root_component == other.root_component and \
                self.phase_manager == other.phase_manager and \
                self.timeline_record == other.timeline_record

    def __str__(self):
        return (f"Context : root_component name={self.root_component.name}, "
                f"current_phase={self.phase_manager.current_phase}")

    def add_record_of_each_component(self, absolute_time: float, description: str) -> List[RecordComponent]:
        """
        Function adding a record for each component.
        """
        records = []
        for component in self.root_component.to_set():
            records.append(
                RecordComponent(component,
                                component.status,
                                absolute_time,
                                self.phase_manager.current_phase,
                                description)
            )
        return records
