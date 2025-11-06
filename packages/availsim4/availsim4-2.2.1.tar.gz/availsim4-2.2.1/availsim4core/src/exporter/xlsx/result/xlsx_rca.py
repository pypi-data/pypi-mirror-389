# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for XLSXResultExporterRCA class
"""

import pathlib
from typing import List
import pandas
from availsim4core.src.exporter.xlsx.xlsx_exporter import XLSXExporter
from availsim4core.src.results.simulation_results import SimulationResults


class XLSXRCA(XLSXExporter):
    """
    This class defines an XLSX exporter of root cause analysis - a list of system's snapshots taken in circumstances
    defined by the user in terms of individual component's statuses.
    """

    def export(self, results: SimulationResults) -> List[pathlib.Path]:
        rca_export = []
        for record in results.root_cause_analysis_records:
            record.component_statuses.pop("RUNNING")
            component_statuses = {status_name: ", ".join(components_list)
                                  for status_name, components_list in record.component_statuses.items()}
            rca_export.append({
                "analysis_id": record.simulation_id,
                "timestamp": record.timestamp,
                "rca_component_trigger": record.rca_trigger_component,
                "rca_status_trigger": record.rca_trigger_status,
                "rca_phase_trigger": record.rca_trigger_phase,
                "event_description": record.description,
                "snapshot_root_cause": record.trigger_root_cause,
                **component_statuses
            })
        rca_export_dataframe = pandas.DataFrame(rca_export)
        filepath = self.export_dataframe(rca_export_dataframe, "RESULTS_ROOT_CAUSE_ANALYSIS")
        return [filepath]
