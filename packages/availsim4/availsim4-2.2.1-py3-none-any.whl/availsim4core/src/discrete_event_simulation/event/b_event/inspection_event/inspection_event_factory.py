# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.discrete_event_simulation.event.b_event.inspection_event.start_inspection_event import \
    StartInspectionEvent


class InspectionEventFactory:

    @staticmethod
    def build(absolute_occurrence_time: float,
              context: Context,
              basic: Basic,
              failure_mode: FailureMode):
        """
        Build a StartInspectionEvent.
        :param absolute_occurrence_time: absolute discrete event simulation time when the inspection event will be started.
        :param context:
        :param basic: associate basic to inspect.
        :param failure_mode: failure mode which triggered this inspection event.
        """
        if failure_mode.inspection is None:
            return None
        return StartInspectionEvent(absolute_occurrence_time + failure_mode.inspection.periodicity,
                                    context,
                                    basic,
                                    failure_mode)
