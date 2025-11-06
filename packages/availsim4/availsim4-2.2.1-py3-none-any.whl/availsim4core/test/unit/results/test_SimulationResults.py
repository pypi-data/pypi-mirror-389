# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.children_logic.children_logic import ChildrenLogic
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.probability_law.deterministic_law import DeterministicLaw
from availsim4core.src.results.result_record_entry_component import ResultRecordEntryComponent
from availsim4core.src.results.result_record_entry_phase import ResultRecordEntryPhase
from availsim4core.src.results.simulation_results import SimulationResults
from availsim4core.src.timeline.record_component import RecordComponent
from availsim4core.src.timeline.record_generator import RecordGenerator
from availsim4core.src.timeline.record_phase import RecordPhase
from availsim4core.src.timeline.timeline import Timeline


class test_SimulationResults(unittest.TestCase):

    def test_update_with_des_results(self):
        basic_1 = Basic(1, "test_basic_1", 0, [], [], [], [])
        basic_2 = Basic(2, "test_basic_2", 0, [], [], [], [])

        component_list = [basic_1, basic_2]
        compound = Compound(3, "test_compound_1", 1, [], ChildrenLogic(), [])
        compound.add_children_list(component_list)
        record_list = [RecordPhase(PhaseManager.NO_PHASE,
                                   0,
                                   RecordGenerator.DESCRIPTION_INIT),
                       RecordComponent(basic_1,
                                       Status.RUNNING,
                                       0,
                                       PhaseManager.NO_PHASE,
                                       RecordGenerator.DESCRIPTION_INIT),
                       RecordComponent(basic_2,
                                       Status.RUNNING,
                                       0,
                                       PhaseManager.NO_PHASE,
                                       RecordGenerator.DESCRIPTION_INIT),
                       RecordComponent(compound,
                                       Status.RUNNING,
                                       0,
                                       PhaseManager.NO_PHASE,
                                       RecordGenerator.DESCRIPTION_INIT)
                       ]

        timeline = Timeline()
        timeline.record_list = record_list
        simulation_results = SimulationResults(10, 50)
        simulation_results.update_with_des_results({'number_of_time_iteration':5}, timeline)
        self.assertEqual(simulation_results.execution_metrics_statistics['number_of_time_iteration'].min, 5)
        self.assertEqual(simulation_results.execution_metrics_statistics['number_of_time_iteration'].max, 5)
        self.assertEqual(simulation_results.execution_metrics_statistics['number_of_time_iteration'].sum, 5)

        result_record_phase = ResultRecordEntryPhase(PhaseManager.NO_PHASE,RecordGenerator.DESCRIPTION_INIT)
        result_record_basic1 = ResultRecordEntryComponent(basic_1, Status.RUNNING, PhaseManager.NO_PHASE,RecordGenerator.DESCRIPTION_INIT)
        result_record_basic2 = ResultRecordEntryComponent(basic_2, Status.RUNNING, PhaseManager.NO_PHASE,RecordGenerator.DESCRIPTION_INIT)
        result_record_compound = ResultRecordEntryComponent(compound, Status.RUNNING, PhaseManager.NO_PHASE,RecordGenerator.DESCRIPTION_INIT)
        self.assertEqual(simulation_results.occurrence_statistics[result_record_phase].min, 1)
        self.assertEqual(simulation_results.occurrence_statistics[result_record_basic1].min, 1)
        self.assertEqual(simulation_results.occurrence_statistics[result_record_basic2].min, 1)
        self.assertEqual(simulation_results.occurrence_statistics[result_record_compound].min, 1)

        self.assertEqual(simulation_results.duration_statistics[result_record_phase].min, 50)
        self.assertEqual(simulation_results.duration_statistics[result_record_basic1].min, 50)
        self.assertEqual(simulation_results.duration_statistics[result_record_basic2].min, 50)
        self.assertEqual(simulation_results.duration_statistics[result_record_compound].min, 50)

    def test_update_with_des_results_multiple_updates(self):
        phase_first = Phase("phase_test", DeterministicLaw(10), True)
        phase_second = Phase("phase_second", DeterministicLaw(10), False)
        phase_first.set_next_phase(phase_second)
        phase_second.set_next_phase(phase_first)

        basic_1 = Basic(1, "test_basic_1", 0, [], [], [], [])
        basic_2 = Basic(2, "test_basic_2", 0, [], [], [], [])

        component_list = [basic_1, basic_2]
        compound = Compound(3, "test_compound_1", 1, [], ChildrenLogic(), [])
        compound.add_children_list(component_list)
        record_list = [RecordPhase(phase_first,
                                   0,
                                   RecordGenerator.DESCRIPTION_INIT),
                       RecordComponent(basic_1,
                                       Status.RUNNING,
                                       0,
                                       phase_first,
                                       RecordGenerator.DESCRIPTION_INIT),
                       RecordComponent(basic_2,
                                       Status.RUNNING,
                                       0,
                                       phase_first,
                                       RecordGenerator.DESCRIPTION_INIT),
                       RecordComponent(compound,
                                       Status.RUNNING,
                                       0,
                                       phase_first,
                                       RecordGenerator.DESCRIPTION_INIT),
                       RecordPhase(phase_second,
                                   10,
                                   PhaseManager.DEFAULT_PHASE_DESCRIPTION),
                       RecordComponent(basic_1,
                                       Status.RUNNING,
                                       10,
                                       phase_second,
                                       PhaseManager.DEFAULT_PHASE_DESCRIPTION),
                       RecordComponent(basic_2,
                                       Status.RUNNING,
                                       10,
                                       phase_second,
                                       PhaseManager.DEFAULT_PHASE_DESCRIPTION),
                       RecordComponent(compound,
                                       Status.RUNNING,
                                       10,
                                       phase_second,
                                       PhaseManager.DEFAULT_PHASE_DESCRIPTION),
                       RecordPhase(phase_first,
                                   20,
                                   PhaseManager.DEFAULT_PHASE_DESCRIPTION),
                       RecordComponent(basic_1,
                                       Status.RUNNING,
                                       20,
                                       phase_first,
                                       PhaseManager.DEFAULT_PHASE_DESCRIPTION),
                       RecordComponent(basic_2,
                                       Status.RUNNING,
                                       20,
                                       phase_first,
                                       PhaseManager.DEFAULT_PHASE_DESCRIPTION),
                       RecordComponent(compound,
                                       Status.RUNNING,
                                       20,
                                       phase_first,
                                       PhaseManager.DEFAULT_PHASE_DESCRIPTION),
                       RecordComponent(basic_1,
                                       Status.FAILED,
                                       21,
                                       phase_first,
                                       "Failure"),
                       RecordComponent(basic_1,
                                       Status.UNDER_REPAIR,
                                       21,
                                       phase_first,
                                       "Repair"),
                       RecordComponent(basic_1,
                                       Status.RUNNING,
                                       22,
                                       phase_first,
                                       "Repair"),
                       RecordPhase(phase_second,
                                   22,
                                   PhaseManager.DEFAULT_PHASE_IF_FAILURE_DESCRIPTION),
                       RecordComponent(basic_1,
                                       Status.RUNNING,
                                       22,
                                       phase_second,
                                       PhaseManager.DEFAULT_PHASE_DESCRIPTION),
                       RecordComponent(basic_2,
                                       Status.RUNNING,
                                       22,
                                       phase_second,
                                       PhaseManager.DEFAULT_PHASE_DESCRIPTION),
                       RecordComponent(compound,
                                       Status.RUNNING,
                                       22,
                                       phase_second,
                                       PhaseManager.DEFAULT_PHASE_DESCRIPTION),
                       ]

        timeline = Timeline()
        timeline.record_list = record_list
        simulation_results = SimulationResults(5, 25)
        simulation_results.update_with_des_results({'number_of_time_iteration':5}, timeline)
        self.assertEqual(simulation_results.execution_metrics_statistics['number_of_time_iteration'].min, 5)
        self.assertEqual(simulation_results.execution_metrics_statistics['number_of_time_iteration'].max, 5)
        self.assertEqual(simulation_results.execution_metrics_statistics['number_of_time_iteration'].sum, 5)

        result_record_phase_first_init = ResultRecordEntryPhase(phase_first,RecordGenerator.DESCRIPTION_INIT)
        result_record_phase_first = ResultRecordEntryPhase(phase_first,PhaseManager.DEFAULT_PHASE_DESCRIPTION)
        result_record_phase_second = ResultRecordEntryPhase(phase_second,PhaseManager.DEFAULT_PHASE_DESCRIPTION)
        result_record_basic1_running_phase_first_init = ResultRecordEntryComponent(basic_1, Status.RUNNING, phase_first,RecordGenerator.DESCRIPTION_INIT)
        result_record_basic1_running_phase_first = ResultRecordEntryComponent(basic_1, Status.RUNNING, phase_first,"Repair")
        result_record_basic1_failed_phase_first = ResultRecordEntryComponent(basic_1, Status.FAILED, phase_first,"Failure")
        result_record_basic1_under_repair_phase_first = ResultRecordEntryComponent(basic_1, Status.UNDER_REPAIR, phase_first,"Repair")
        result_record_basic2 = ResultRecordEntryComponent(basic_2, Status.RUNNING, phase_first,RecordGenerator.DESCRIPTION_INIT)
        result_record_compound = ResultRecordEntryComponent(compound, Status.RUNNING, phase_first,RecordGenerator.DESCRIPTION_INIT)
        self.assertEqual(simulation_results.occurrence_statistics[result_record_phase_first_init].min, 1)
        self.assertEqual(simulation_results.occurrence_statistics[result_record_phase_first].min, 1)
        self.assertEqual(simulation_results.occurrence_statistics[result_record_phase_second].min, 1)
        self.assertEqual(simulation_results.occurrence_statistics[result_record_basic1_running_phase_first_init].min, 1)
        self.assertEqual(simulation_results.occurrence_statistics[result_record_basic1_running_phase_first].min, 1)
        self.assertEqual(simulation_results.occurrence_statistics[result_record_basic1_failed_phase_first].min, 1)
        self.assertEqual(simulation_results.occurrence_statistics[result_record_basic1_under_repair_phase_first].min, 1)
        self.assertEqual(simulation_results.occurrence_statistics[result_record_basic2].min, 1)
        self.assertEqual(simulation_results.occurrence_statistics[result_record_compound].min, 1)

        self.assertEqual(simulation_results.duration_statistics[result_record_phase_first_init].min, 10)
        self.assertEqual(simulation_results.duration_statistics[result_record_phase_first].min, 2)
        self.assertEqual(simulation_results.duration_statistics[result_record_basic1_running_phase_first_init].min, 10)
        self.assertEqual(simulation_results.duration_statistics[result_record_basic1_failed_phase_first].min, 0)  # immediate repair
        self.assertEqual(simulation_results.duration_statistics[result_record_basic1_under_repair_phase_first].min, 1)
        self.assertEqual(simulation_results.duration_statistics[result_record_basic2].min, 10)
        self.assertEqual(simulation_results.duration_statistics[result_record_compound].min, 10)
