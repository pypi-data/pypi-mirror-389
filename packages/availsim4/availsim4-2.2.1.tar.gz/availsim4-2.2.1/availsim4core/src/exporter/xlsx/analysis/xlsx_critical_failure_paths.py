# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for XLSXResultsExporterCriticalFailurePaths class
"""

import logging
import pathlib
from typing import List, Optional
import pandas as pd
from availsim4core.src.context.system.system_utils import SystemUtils

from availsim4core.src.exporter.xlsx.xlsx_exporter import XLSXExporter
from availsim4core.src.results.simulation_results import SimulationResults
from availsim4core.src.statistics.critical_failure_paths import CriticalFailurePaths


class XLSXCriticalFailurePaths(XLSXExporter):
    """
    This class defines an XLSX exporter of critical failure paths (combinations of components which failures result in a
    failure of the overall system.
    """


    def export(self, _: Optional[SimulationResults] = None) -> List[pathlib.Path]:
        """
        Exports critical failure paths.
        """

        # For critical failure paths, we need additional parameter to know where to start
        # looking for critical failure paths. By default, the component is the root of the
        # tree (stored in context.root_component.name). Alternatively, users may choose a
        # different component specifying its name as an argument to the diagnostic:
        # e.g., for CFP_ROOT component, the command is: "CRITICAL_FAILURE_PATHS(CFP_ROOT)"
        export_root = self.root_component.name
        for diagnostic_user_command in self.analysis.simulation.get_list_of_diagnosis():
            if "CRITICAL_FAILURE_PATHS" in diagnostic_user_command:
                if SystemUtils.is_string_containing_parenthesis(diagnostic_user_command):
                    export_root = SystemUtils.extract_arguments_within_parenthesis(diagnostic_user_command)

        logging.info("Exporting the critical failure path from the node %s", export_root)
        cfp = CriticalFailurePaths(self.root_component, export_root)
        critical_failure_paths_names = []
        for path in cfp.critical_failure_paths:
            path_names = []
            for component in path:
                #TODO add some information about the failure mode ? (blind, dectable etc ?) or forcing an additional
                # export with this information, like the list of component export ?
                path_names.append(f"{component.name}_{component.local_id}_{component.global_id}")
            critical_failure_paths_names.append(path_names)

        cfp_df = pd.DataFrame(critical_failure_paths_names)
        filepath = self.export_dataframe(cfp_df, "RESULTS_CRITICAL_FAILURE_PATHS")
        return [filepath]
