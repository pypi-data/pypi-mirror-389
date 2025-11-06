# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for XLSXResultExporterExecutionMetrics class
"""

import pathlib
from typing import List
import pandas
from availsim4core.src.exporter.xlsx.xlsx_exporter import XLSXExporter
from availsim4core.src.results.simulation_results import SimulationResults


class XLSXExecutionMetrics(XLSXExporter):
    """
    class used to export the results of a simulation into an output file
    This exporter is meant to provide a good "summary" of a simulation, not a light report like the exporter LightStudy
    """

    def export(self, results: SimulationResults) -> List[pathlib.Path]:
        execution_metrics_dict = {"execution_time": results.execution_time,
                                  "number_of_DES_simulations_executed": str(results.number_of_DES_simulations_executed)}
        for key, statistics in results.execution_metrics_statistics.items():
            execution_metrics_dict[key + "_MEAN"] = statistics.mean
            execution_metrics_dict[key + "_MAX"] = statistics.max
            execution_metrics_dict[key + "_STD"] = statistics.std

        number_of_compound_components = 0
        number_of_basic_components = 0

        for component in self.root_component.to_set():
            if component.get_children():
                # if that component has children (then it is a Compound type)
                number_of_compound_components += 1
            else:
                number_of_basic_components += 1

        execution_metrics_dict["number_of_compound_components"] = number_of_compound_components
        execution_metrics_dict["number_of_basic_components"] = number_of_basic_components

        # exporting the execution time and other metric
        execution_metrics_dataframe = pandas.DataFrame(
            execution_metrics_dict,
            index=[0])

        filepath = self.export_dataframe(execution_metrics_dataframe, "RESULTS_EXECUTION_METRICS")
        return [filepath]
