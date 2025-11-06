# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for class XLSXAnalysisExporter.
"""

import logging
import pathlib
from typing import List, Optional, Set

import pandas

from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.failure_mode_assignments import FailureModeAssignments
from availsim4core.src.context.system.inspection import Inspection
from availsim4core.src.context.system.minimal_replaceable_unit import MinimalReplaceableUnit
from availsim4core.src.context.system.phase_jump_trigger import PhaseJumpTrigger
from availsim4core.src.context.system.rca_trigger import RootCauseAnalysisTrigger
from availsim4core.src.context.system.system_template import SystemTemplate
from availsim4core.src.exporter.xlsx.xlsx_exporter import XLSXExporter
from availsim4core.resources import excel_strings
from availsim4core.src.results.simulation_results import SimulationResults
from availsim4core.src.simulation.monte_carlo import MonteCarlo
from availsim4core.src.simulation.simulation import Simulation
from availsim4core.src.exporter.input_file_exporter import InputFileExporter


class XLSXAnalysisExporter(XLSXExporter, InputFileExporter):
    """
    An exporter of all sheets describing the performed simulation and the system.
    """

    def export(self, _: Optional[SimulationResults] = None) -> List[pathlib.Path]:
        """
        Function to export all system and simulation sheets describing the simulation runs.
        """
        output_filepath = self.get_concrete_filepath()
        logging.info(output_filepath)
        with self.open_workbook(output_filepath) as writer:
            self.export_system(writer, self.analysis.system_template)
            self.export_simulation(writer, self.analysis.simulation)
        return [output_filepath]

    def export_system_to_file(self, file_name: str = "system.xlsx") -> pathlib.Path:
        filepath = self.output_folder / file_name
        with self.open_workbook(filepath) as writer:
            self.export_system(writer, self.analysis.system_template)
        return filepath

    def export_simulation_to_file(self, file_name: str = "simulation.xlsx") -> pathlib.Path:
        filepath = self.output_folder / file_name
        with self.open_workbook(filepath) as writer:
            self.export_simulation(writer, self.analysis.simulation)
        return filepath

    @classmethod
    def export_system(cls,
                      writer,
                      system_template:SystemTemplate):
        """
        Function to export system sheets to xlsx file.
        """

        dataframe = cls._export_architecture_entry_to_dataframe(system_template.architecture_entry_list)
        dataframe.to_excel(writer, sheet_name=excel_strings.SystemTemplateSheet.ARCHITECTURE, index=False)

        dataframe = cls._export_failure_mode_to_dataframe(system_template.failure_mode_list)
        dataframe.to_excel(writer, sheet_name=excel_strings.SystemTemplateSheet.FAILURE_MODES, index=False)

        dataframe = cls._export_failure_mode_assignments_to_dataframe(system_template.failure_mode_assignments_list)
        dataframe.to_excel(writer,
                           sheet_name=excel_strings.SystemTemplateSheet.FAILURE_MODE_ASSIGNMENTS,
                           index=False)

        dataframe = cls._export_mru_to_dataframe(system_template.mru_list)
        dataframe.to_excel(writer,
                           sheet_name=excel_strings.SystemTemplateSheet.MINIMAL_REPLACEABLE_UNIT,
                           index=False)

        dataframe = cls._export_inspection_to_dataframe(system_template.inspection_list)
        dataframe.to_excel(writer, sheet_name=excel_strings.SystemTemplateSheet.INSPECTIONS, index=False)

        dataframe = cls._export_phase_to_dataframe(system_template.phase_set)
        dataframe.to_excel(writer, sheet_name=excel_strings.SystemTemplateSheet.PHASES, index=False)

        dataframe = cls._export_rca_to_dataframe(system_template.root_cause_analysis_trigger_set)
        dataframe.to_excel(writer, sheet_name=excel_strings.SystemTemplateSheet.ROOT_CAUSE_ANALYSIS, index=False)

        dataframe = cls._export_phase_jump_to_dataframe(system_template.phase_jump_trigger_set)
        dataframe.to_excel(writer, sheet_name=excel_strings.SystemTemplateSheet.PHASE_JUMP, index=False)

    @classmethod
    def export_simulation(cls, writer, simulation: Simulation):
        """
        Function to export simulation sheet to Xlsx file
        """
        dataframe = cls._export_simulation_to_dataframe(simulation)
        dataframe.to_excel(writer, sheet_name=excel_strings.SimulationSheet.SHEET, index=False)

    @classmethod
    def _export_architecture_entry_to_dataframe(cls, architecture_entry_list):
        data = []
        for architecture_entry in architecture_entry_list:
            data_architecture = [architecture_entry.component_name,
                                 architecture_entry.component_type,
                                 architecture_entry.component_number,
                                 architecture_entry.children_name_list
                                    if architecture_entry.children_name_list
                                    else excel_strings.SystemTemplateField.NONE,
                                 architecture_entry.children_logic
                                    if architecture_entry.children_logic
                                    else excel_strings.SystemTemplateField.NONE,
                                 architecture_entry.in_mru_str_list
                                    if architecture_entry.in_mru_str_list
                                    else excel_strings.SystemTemplateField.NONE,
                                 architecture_entry.trigger_mru_str_list
                                    if architecture_entry.trigger_mru_str_list
                                    else excel_strings.SystemTemplateField.NONE,
                                 architecture_entry.comments]
            data.append(data_architecture)

        column_names = cls.extract_value_list_from_class_public_attributes(excel_strings.SystemTemplateArchitectureColumn)
        dataframe = pandas.DataFrame(data, columns=column_names)
        return dataframe

    @staticmethod
    def extract_value_list_from_class_public_attributes(class_name):
        """
        Utility method to extract values from public attributes for a given class.
        Useful for constant global classes.
        """
        return [getattr(class_name, name)
                for name in vars(class_name).keys()
                if not name.startswith("__")]

    @classmethod
    def _export_failure_mode_to_dataframe(cls, failure_mode_list:List[FailureMode]):
        data = []
        for failure_mode in failure_mode_list:
            data_failure = [
                failure_mode.name,
                failure_mode.failure_law.name,
                failure_mode.failure_law.parameters,
                failure_mode.repair_law.name,
                failure_mode.repair_law.parameters,
                failure_mode.failure.type_of_failure,
                str(sorted([phase.name
                            for phase in failure_mode.held_before_repair_phase_set])),
                excel_strings.SystemTemplateField.NONE
                            if not failure_mode.inspection
                            else failure_mode.inspection.name,
                str(sorted([phase.name for phase in failure_mode.phase_set])),
                excel_strings.SystemTemplateField.NONE
                            if failure_mode.failure_mode_next_phase_if_failure is None
                            else failure_mode.failure_mode_next_phase_if_failure.name,
                failure_mode.phase_change_trigger,
                str(sorted([phase.name for phase in failure_mode.held_after_repair_phase_set])),
                failure_mode.repair_strategy,
                failure_mode.comments
            ]
            data.append(data_failure)

        column_names = cls.extract_value_list_from_class_public_attributes(excel_strings.SystemTemplateFailureModeColumn)
        dataframe = pandas.DataFrame(data, columns=column_names)
        return dataframe

    @classmethod
    def _export_failure_mode_assignments_to_dataframe(cls,
                                    failure_mode_assignments_list: List[FailureModeAssignments]):
        data = []
        for failure_mode_assignments in failure_mode_assignments_list:
            data_failure_assignments = [failure_mode_assignments.component_name,
                                        failure_mode_assignments.failure_mode.name,
                                        failure_mode_assignments.comments]
            data.append(data_failure_assignments)

        column_names = cls \
        .extract_value_list_from_class_public_attributes(excel_strings.SystemTemplateFailureModeAssignmentsColumn)
        dataframe = pandas.DataFrame(data, columns=column_names)
        return dataframe

    @classmethod
    def _export_mru_to_dataframe(cls, mru_list:List[MinimalReplaceableUnit]):
        data = []
        for mru in mru_list:
            data_mru = [mru.name,
                        mru.repair_law.name,
                        mru.repair_law.parameters,
                        mru.repair_schedule,
                        mru.scope_common_ancestor,
                        mru.status,
                        mru.comments]
            data.append(data_mru)

        column_names = cls.extract_value_list_from_class_public_attributes(
                                                        excel_strings.SystemTemplateMinimalReplaceableUnitColumn)
        dataframe = pandas.DataFrame(data, columns=column_names)
        return dataframe

    @classmethod
    def _export_inspection_to_dataframe(cls, inspection_list:List[Inspection]):
        data = []
        for inspection in inspection_list:
            data_inspection = [inspection.name,
                               inspection.periodicity,
                               inspection.duration,
                               inspection.comments]
            data.append(data_inspection)

        column_names = cls.extract_value_list_from_class_public_attributes(excel_strings.SystemTemplateInspectionsColumn)
        dataframe = pandas.DataFrame(data, columns=column_names)
        return dataframe

    @classmethod
    def _export_simulation_to_dataframe(cls, simulation:Simulation):
        data = []
        # TODO: If a simulation is not an instance of Monte Carlo, this code will fail
        # (data_simulation referenced before assignment)
        if isinstance(simulation, MonteCarlo):
            column_names = [excel_strings.SimulationSheet.TYPE]
            column_names.extend([excel_strings.SimulationMonteCarloColumn.MINIMUM_NUMBER_OF_SIMULATION,
                                 excel_strings.SimulationMonteCarloColumn.MAXIMUM_NUMBER_OF_SIMULATION,
                                 excel_strings.SimulationMonteCarloColumn.CONVERGENCE_MARGIN,
                                 excel_strings.SimulationMonteCarloColumn.MAXIMUM_EXECUTION_TIME,
                                 excel_strings.SimulationMonteCarloColumn.SEED,
                                 excel_strings.SimulationMonteCarloColumn.DIAGNOSTICS,
                                 excel_strings.SimulationMonteCarloColumn.DURATION])
            data_simulation = [
                simulation.SIMULATION_TYPE,
                simulation.minimum_number_of_simulations,
                simulation.maximum_number_of_simulations,
                simulation.convergence_margin,
                simulation.maximum_execution_time,
                simulation.seed,
                simulation.list_of_diagnosis,
                simulation.duration_of_simulation
            ]
        data.append(data_simulation)

        dataframe = pandas.DataFrame(data, columns=column_names)
        return dataframe

    @classmethod
    def _export_phase_to_dataframe(cls, phase_set:Set[Phase]):
        data: List[List[str]] = []
        column_names = cls \
                        .extract_value_list_from_class_public_attributes(excel_strings.SystemTemplatePhasesColumn)

        for phase in phase_set:
            assert phase.next is not None
            next_phase_if_failure = "None"
            if phase.next_phase_if_failure:
                next_phase_if_failure = phase.next_phase_if_failure.name
            data_phase = [phase.name,
                          phase.law.name,
                          phase.law.parameters,
                          phase.next.name,
                          phase.is_first_phase,
                          next_phase_if_failure,
                          phase.comments]
            data.append(data_phase)

        dataframe = pandas.DataFrame(data, columns=column_names)
        return dataframe

    @classmethod
    def _export_rca_to_dataframe(cls, rca_triggers_set:Set[RootCauseAnalysisTrigger]):
        data = []
        column_names = cls \
            .extract_value_list_from_class_public_attributes(excel_strings.SystemTemplateRootCauseAnalysisColumn)

        for trigger in rca_triggers_set:
            data_trigger = [trigger.component_name,
                            trigger.component_status,
                            trigger.phase,
                            trigger.comments]
            data.append(data_trigger)

        dataframe = pandas.DataFrame(data, columns=column_names)
        return dataframe

    @classmethod
    def _export_phase_jump_to_dataframe(cls, phase_jump_trigger_set:Set[PhaseJumpTrigger]):
        data = []
        column_names = cls \
            .extract_value_list_from_class_public_attributes(excel_strings.SystemTemplatePhaseJumpColumn)

        for phase_jump in phase_jump_trigger_set:
            data_phase_jump = [
                phase_jump.component_name,
                phase_jump.component_status,
                phase_jump.from_phase.name,
                phase_jump.to_phase.name,
                phase_jump.comments
            ]
            data.append(data_phase_jump)

        dataframe = pandas.DataFrame(data, columns=column_names)
        return dataframe
