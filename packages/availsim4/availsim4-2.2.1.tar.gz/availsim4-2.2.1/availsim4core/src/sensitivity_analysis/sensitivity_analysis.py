# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module for the Sensitivity Analysis class which handles creation of Analysis objects for sensitivity analysis
feature."""

import copy
import logging
from typing import Set, Tuple

from availsim4core.src.analysis import Analysis
from availsim4core.resources import excel_strings
from availsim4core.src.reader.xlsx.sensitivity_analysis_reader import SensitivityAnalysisReader
from availsim4core.resources.excel_strings import SystemTemplateArchitectureColumn, \
    SystemTemplateFailureModeColumn, SystemTemplateMinimalReplaceableUnitColumn, SystemTemplateInspectionsColumn


class ParameterOfSensitivityAnalysisNotFoundError(Exception):
    """Failed to identify the parameter specified in the sensitivity analysis"""



class OverlappingSeedsError(Exception):
    """Error thrown when seeds defined by the sensitivity analysis are leading to overlapping simulations"""


class NegativeSeedsError(Exception):
    """Error thrown when any of the seeds specified by the user are negative"""


class SensitivityAnalysis:
    """
    Manages the sensitivity analysis from the initial simulation and initial system.
    """

    def __init__(self,
                 initial_simulation,
                 initial_system_template):
        self.initial_simulation = initial_simulation
        self.initial_system_template = initial_system_template
        self.seed_intervals: Set[Tuple[int, int]] = set()

    def _confirm_no_seed_overlaps(self) -> None:
        if any(x < 0 for x, _ in self.seed_intervals):
            logging.error("One or more of the seeds specified in the sensitivity analysis are negative.")
            raise NegativeSeedsError()

        sorted_tuples = sorted(self.seed_intervals, key=lambda x: x[0])
        reached_seed = -1

        for starting_seed, no_iterations in sorted_tuples:
            if starting_seed <= reached_seed:
                logging.error("The seeds defined in the sensitivity analysis are leading to overlapping simulations."\
                              "Check the sensitivity analysis file")
                raise OverlappingSeedsError()
            reached_seed = starting_seed + no_iterations - 1

    def generate_analysis_list(self,
                               path_sensitivity_analysis):
        """
        From the given path of the sensitivity analysis it reads the file and returns a list of Analysis to perform.
        :param path_sensitivity_analysis path of the configuration file for the sensitivity analysis.
        :return List[Analysis]
        :see Analysis
        """

        system_modifier_combination_list = SensitivityAnalysisReader.generate_system_modifier_combination_list(
            path_sensitivity_analysis)

        analysis_list = []
        for idx, system_modifier_combination in enumerate(system_modifier_combination_list):
            analysis = self._generate_analysis(idx,
                                               system_modifier_combination)
            analysis_list.append(analysis)

        self._confirm_no_seed_overlaps()
        return analysis_list

    def _generate_analysis(self,
                           idx,
                           system_modifier_combination):
        """
        Given a combination {SystemModifierCombination} and based of the initial simulation and system,
        it generates the corresponding analysis.
        :param idx the id of the analysis to generate
        :param system_modifier_combination the SystemModifierCombination to apply on initial simulation and system.
        :returns Corresponding Analysis {Analysis}
        """

        new_simulation = self._apply_combination_modifier_on_simulation(system_modifier_combination)
        new_system_template = self._apply_combination_modifier_on_system(system_modifier_combination)
        return Analysis(idx, new_system_template, new_simulation)

    def _apply_combination_modifier_on_system(self,
                                              system_modifier_combination):
        """
        Given a {SystemModifierCombination} it applies the modification to the copy of the initial system template.
        :param system_modifier_combination the combination with the system modifier to apply on the initial system
        template.
        """
        modified_initial_system_template = copy.deepcopy(self.initial_system_template)

        for system_modifier in system_modifier_combination.system_modifier_list:

            modification_applied = False

            column_name, name = system_modifier.parameter_name.partition("/")[::2]

            if column_name=="SEED":
                # modification applied in another function
                modification_applied = True

            architecture_entry = modified_initial_system_template.find_architecture_entry(name)
            if architecture_entry is not None:
                if column_name == SystemTemplateArchitectureColumn.COMPONENT_NUMBER:
                    architecture_entry.component_number = int(system_modifier.value)
                    modification_applied = True
                if column_name == SystemTemplateArchitectureColumn.CHILDREN_LOGIC:
                    architecture_entry.children_logic = system_modifier.value
                    modification_applied = True

            failure_mode = modified_initial_system_template.find_failure_mode(name)
            if failure_mode is not None:
                if column_name == SystemTemplateFailureModeColumn.FAILURE_PARAMETERS:
                    failure_mode.failure_law.set_parameters(system_modifier.value)
                    modification_applied = True
                if column_name == SystemTemplateFailureModeColumn.REPAIR_PARAMETERS:
                    failure_mode.repair_law.set_parameters(system_modifier.value)
                    modification_applied = True

            mru = modified_initial_system_template.find_mru(name)
            if mru is not None:
                if column_name == SystemTemplateMinimalReplaceableUnitColumn.REPAIR_PARAMETERS:
                    mru.repair_law.set_parameters(system_modifier.value)
                    modification_applied = True
                if column_name == SystemTemplateMinimalReplaceableUnitColumn.REPAIR_SCHEDULE:
                    mru.repair_schedule = system_modifier.value
                    modification_applied = True

            inspection = modified_initial_system_template.find_inspection(name)
            if inspection is not None:
                if column_name == SystemTemplateInspectionsColumn.INSPECTION_DURATION:
                    inspection.duration = float(system_modifier.value)
                    modification_applied = True
                if column_name == SystemTemplateInspectionsColumn.INSPECTION_PERIOD:
                    inspection.periodicity = float(system_modifier.value)
                    modification_applied = True

            if not modification_applied:
                exception_message = f"System_modifier {system_modifier} could not be applied:"\
                                    f"wrong parameter name={name}"
                logging.exception(exception_message)
                raise ParameterOfSensitivityAnalysisNotFoundError(exception_message)

        return modified_initial_system_template

    def _apply_combination_modifier_on_simulation(self, system_modifier_combination):
        """
        Given a {SystemModifierCombination} it applies the modification to the copy of the initial simulation.
        :param system_modifier_combination the combination with the system modifier to apply on the initial simulation.
        Note: Because the simulation has only one line entry, only the column name of the system modifier is taken into
        account.
        """
        modified_initial_simulation = copy.deepcopy(self.initial_simulation)

        for system_modifier in system_modifier_combination.system_modifier_list:
            column_name, *_ = system_modifier.parameter_name.split("/")

            if column_name == excel_strings.SimulationMonteCarloColumn.SEED:
                modified_initial_simulation.seed = int(system_modifier.value)
                number_of_simulations = max(modified_initial_simulation.minimum_number_of_simulations,
                                            modified_initial_simulation.maximum_number_of_simulations)
                self.seed_intervals.add((modified_initial_simulation.seed, number_of_simulations))

        return modified_initial_simulation
