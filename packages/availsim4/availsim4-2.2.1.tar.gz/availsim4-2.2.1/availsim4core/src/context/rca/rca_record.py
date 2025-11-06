# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from collections import defaultdict
from typing import Dict, Set

from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.timeline.record import Record


class RootCauseAnalysisRecord:
    """
    Class managing the records made by the RCA feature. It generates a snapshot of the state of the system
    """
    __slots__ = 'simulation_id', 'timestamp', 'rca_trigger_component', 'rca_trigger_status', 'rca_trigger_phase', \
                'trigger_root_cause', 'description', 'component_statuses'

    def __init__(self,
                 simulation_id: int,
                 record: Record,
                 components: Set[Component],
                 trigger_root_cause_record: Record):
        self.simulation_id = simulation_id
        self.timestamp = record.timestamp

        # name of the component, status and phase that triggered the RCA (as defined by user)
        self.rca_trigger_component = record.get_name()
        self.rca_trigger_status = str(record.status)
        self.rca_trigger_phase = record.phase.name

        # name of the component that triggered the flow of events eventually triggering the RCA snapshot
        self.trigger_root_cause = trigger_root_cause_record.get_name()

        self.description = record.description

        self.component_statuses: Dict[str, str] = defaultdict(list)
        for component in components:
            # for each component, record its name in a list associated with the status at the moment of taking snapshot
            # i.e., {"RUNNING": ["ROOT", "COMP1"], "FAILED": ["COMP2"]}
            self.component_statuses[component.status.name].append(component.get_unique_name())

    def __members(self):
        return (self.simulation_id, self.timestamp, self.rca_trigger_component, self.rca_trigger_status,
                self.rca_trigger_phase, self.description, self.component_statuses)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__members() == other.__members()
        else:
            return False

    def __hash__(self):
        return hash(self.__members())
