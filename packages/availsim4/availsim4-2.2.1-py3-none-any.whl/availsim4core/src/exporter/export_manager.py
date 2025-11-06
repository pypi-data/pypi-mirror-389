# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for AggregateExporter class
"""

import logging
import os
import pathlib
import shutil
from typing import Dict, List, Optional, Set, Type

from _datetime import datetime

from availsim4core.src.analysis import Analysis
from availsim4core.src.context.system.component_tree.component import Component
from availsim4core.src.exporter.exporter import Exporter
from availsim4core.src.context.system.system_utils import SystemUtils
from availsim4core.src.exporter.xlsx.analysis.xlsx_analysis_exporter import XLSXAnalysisExporter
from availsim4core.src.results.simulation_results import SimulationResults

from availsim4core.src.exporter.xlsx.result.xlsx_execution_metrics import XLSXExecutionMetrics
from availsim4core.src.exporter.xlsx.result.xlsx_last_timeline import XLSXLastTimeline
from availsim4core.src.exporter.xlsx.result.xlsx_summary import XLSXSummary
from availsim4core.src.exporter.xlsx.result.xlsx_rca import XLSXRCA
from availsim4core.src.exporter.xlsx.analysis.xlsx_critical_failure_paths import XLSXCriticalFailurePaths

from availsim4core.src.exporter.xlsx.analysis.xlsx_component_listing import XLSXComponentListing
from availsim4core.src.exporter.xlsx.analysis.xlsx_component_tree_extented import XLSXComponentTreeExtended
from availsim4core.src.exporter.xlsx.analysis.xlsx_component_tree_simple import XLSXComponentTreeSimple
from availsim4core.src.exporter.xlsx.analysis.xlsx_connectivity_matrix import XLSXConnectivityMatrix


class DiagnosticType:
    """
    Mapping exporters to diagnostic names users may use to specify information to be stored.
    """

    DIAGNOSTIC_EXPORTER: Dict[str, Optional[Type[Exporter]]] = {
        "EXECUTION_METRICS": XLSXExecutionMetrics,
        "SUMMARY": XLSXSummary,
        "LAST_TIMELINE": XLSXLastTimeline,
        "RCA": XLSXRCA,
        "COMPONENT_TREE_SIMPLE": XLSXComponentTreeSimple,
        "COMPONENT_TREE_EXTENDED": XLSXComponentTreeExtended,
        "CONNECTIVITY_MATRIX": XLSXConnectivityMatrix,
        "COMPONENT_LISTING": XLSXComponentListing,
        "CRITICAL_FAILURE_PATHS": XLSXCriticalFailurePaths,
        "GRAPH": None # Imported and handled separately, to avoid global import of graph's dependencies when not needed
    }


class ExportManager(Exporter):
    """
    TODO: refactoring of selecting diagnostics. Critical failure paths already require an argument
    and it is handled in an unnecessarily complex way. Optimally all diagnosticts should be able to
    handle arguments - which will make this export function much more smooth.

    Note: Subsequent calls of the export method of the same object will cause removal of the previous export.
    """

    def __init__(self,
                 root_component: Component,
                 analysis: Analysis,
                 output_folder: pathlib.Path,
                 unique_output_file_identifier: str = "") -> None:

        if unique_output_file_identifier == "":
            unique_output_file_identifier = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        super().__init__(root_component, analysis, output_folder, unique_output_file_identifier)
        os.makedirs(self.output_folder, exist_ok=True)

        self.previously_created_file_paths: Set[pathlib.Path] = set()
        self.results: Optional[SimulationResults] = None
        self.exporters: List[Exporter] = [XLSXAnalysisExporter(root_component, analysis, output_folder,
                                                               unique_output_file_identifier)] # adding default exporter

        exporter_names = self.analysis.simulation.get_list_of_diagnosis().copy()
        exporter_names = [SystemUtils.extract_name_of_function_from_string(name) for name in exporter_names]

        if "GRAPH" in exporter_names:
            # avoiding unnecessary import of that module when not needed (additional optional requirements)
            from availsim4core.src.exporter.graph_exporter import GraphExporter #pylint: disable=import-outside-toplevel
            self.exporters.append(GraphExporter(root_component, analysis, output_folder, unique_output_file_identifier))
            exporter_names.remove("GRAPH")
        exporters_to_create: List[Optional[Type[Exporter]]] = [DiagnosticType.DIAGNOSTIC_EXPORTER[exporter_name]
                                                     for exporter_name in exporter_names]

        self.exporters.extend([exporter_type(root_component, analysis, output_folder, unique_output_file_identifier)
                               for exporter_type in exporters_to_create
                               if exporter_type])

        if analysis.system_template.custom_children_logic_path:
            custom_children_path = analysis.system_template.custom_children_logic_path
            custom_children_logic_copy_name = f"{custom_children_path.stem}_{unique_output_file_identifier}" \
                                              f"{custom_children_path.suffix}"
            shutil.copy(analysis.system_template.custom_children_logic_path,
                        output_folder / custom_children_logic_copy_name)

    def export(self, results: SimulationResults) -> List[pathlib.Path]:
        # clean previous exports
        for filepath in self.previously_created_file_paths:
            os.remove(filepath)
        self.previously_created_file_paths = set()

        for exporter in self.exporters:
            logging.debug("Exporting with %s", exporter.__str__)
            created_filepath = exporter.export(results)
            self.previously_created_file_paths.update(created_filepath)
        return list(self.previously_created_file_paths)
