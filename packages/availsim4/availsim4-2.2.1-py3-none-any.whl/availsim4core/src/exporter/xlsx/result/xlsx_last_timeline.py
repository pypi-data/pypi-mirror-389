# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for XLSXResultExporterLastTimeline class
"""

import pathlib
from typing import List
import pandas
from availsim4core.src.exporter.xlsx.xlsx_exporter import XLSXExporter
from availsim4core.src.results.simulation_results import SimulationResults

class XLSXLastTimeline(XLSXExporter):
    """
    This class defines an XLSX exporter of the last timeline (record of sequence of events in the last DES iteration)
    """

    def export(self, results: SimulationResults) -> List[pathlib.Path]:
        # convert the last timeline for the conversion into a pandas dataframe
        timeline_export = []
        for record in results.last_simulation_timeline:
            record_status = "" if not record.status else record.status
            timeline_export.append(
                {"timestamp": record.timestamp,
                 "phase": record.phase.name,
                 "component": record.get_result_record_entry(),
                 "description": record.description,
                 "status": record_status}
            )
        timeline_export_dataframe = pandas.DataFrame(timeline_export)
        filepath = self.export_dataframe(timeline_export_dataframe, "RESULTS_LAST_TIMELINE")
        return [filepath]
