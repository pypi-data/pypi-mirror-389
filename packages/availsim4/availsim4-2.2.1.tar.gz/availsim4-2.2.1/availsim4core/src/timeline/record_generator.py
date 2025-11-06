# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.context import Context
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.timeline.record_component import RecordComponent
from availsim4core.src.timeline.record_phase import RecordPhase


class RecordGenerator:
    """
    Class handling the generation of the initial records used at the beginning of a timeline
    """

    DESCRIPTION_INIT = "Init"

    @classmethod
    def get_initial_records(cls,
                            absolute_simulation_time: float,
                            context: Context):
        """
        Function returning the initial records related to phases and components
        """
        record_list = []
        init_phase_records = cls._get_initial_phase_records(absolute_simulation_time,
                                                            context)
        init_component_records = cls._get_initial_component_records(absolute_simulation_time,
                                                                    context)
        record_list.extend(init_phase_records)
        record_list.extend(init_component_records)
        return record_list

    @classmethod
    def _get_initial_phase_records(cls,
                                   absolute_simulation_time: float,
                                   context: Context):
        return [RecordPhase(context.phase_manager.current_phase,
                            absolute_simulation_time,
                            RecordGenerator.DESCRIPTION_INIT)]

    @classmethod
    def _get_initial_component_records(cls,
                                       absolute_simulation_time: float,
                                       context: Context):
        record_list = []
        component_set = context.root_component.to_set()

        for component in component_set:
            record = RecordComponent(component,
                                     Status.RUNNING,
                                     absolute_simulation_time,
                                     context.phase_manager.current_phase,
                                     RecordGenerator.DESCRIPTION_INIT)
            record_list.append(record)
        return record_list
