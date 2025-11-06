# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for XLSXResultExporterSummary class
"""
import pathlib
from typing import Dict, List
import pandas

from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.exporter.xlsx.xlsx_exporter import XLSXExporter
from availsim4core.src.results.result_record_entry import ResultRecordEntry
from availsim4core.src.results.simulation_results import SimulationResults
from availsim4core.src.statistics.statistics import Statistics


class XLSXSummary(XLSXExporter):
    """
    class used to export the results of a simulation into an output file
    This exporter is meant to provide a good "summary" of a simulation, not a light report like the exporter LightStudy
    """


    @classmethod
    def parse_statistics(cls, statistics: Dict[ResultRecordEntry, Statistics], type_of_statistics_str: str):
        """
        Function extracting the statistics into a list of dictionaries
        """

        result_list = []

        for result_record_entry, statistics in statistics.items():
            result_record_entry_attributes = dir(result_record_entry)
            component = result_record_entry.identifier()
            phase = result_record_entry.identifier() if "phase" not in result_record_entry_attributes \
                else getattr(result_record_entry, "phase").name
            status = '_' if "status" not in result_record_entry_attributes \
                else getattr(result_record_entry, "status")
            description = '_' if "description" not in result_record_entry_attributes \
                else getattr(result_record_entry, "description")
            occurrences_key_value = {
                "component": component,
                "phase": phase,
                "status": status,
                "description": description,
                # TODO availsim4/availsim4core#62 BUG in the way _MIN is computed
                # "_MIN_" + type_of_statistics_str: statistics.min,
                # the value 0 cannot appear in _MIN_ because we only count what exists
                # one solution is to generate every possible combination of record and check that they appear 0 time.
                "_MEAN_" + type_of_statistics_str: statistics.mean,
                "_MAX_" + type_of_statistics_str: statistics.max,
                "_STD_" + type_of_statistics_str: statistics.std,
                "_BOOLEAN_" + type_of_statistics_str: statistics.boolean
            }
            result_list.append(occurrences_key_value)

        return result_list

    @classmethod
    def root_statistics(cls,
                        result_dataframe: pandas.DataFrame,
                        root_identifier: str):
        """
        This function returns a dataframe with statistics for the root component (identified by the second argument)
        fetched from the dataframe with general results (first parameter).
        """

        root_result_dataframe = result_dataframe.loc[result_dataframe['component'] == root_identifier]

        root_summary_result = {
            "uptime_duration": 0.0,
            "downtime_duration": 0.0,
        }

        list_of_uptime_status = [Status.RUNNING, Status.DEGRADED, Status.BLIND_DEGRADED]
        for status in list_of_uptime_status:
            root_summary_result["uptime_duration"] += root_result_dataframe.loc[
                root_result_dataframe["status"] == status, "_MEAN_DURATION"
            ].sum()

        list_of_downtime_status = [Status.FAILED, Status.BLIND_FAILED, Status.INSPECTION, Status.UNDER_REPAIR]
        for status in list_of_downtime_status:
            root_summary_result["downtime_duration"] += root_result_dataframe.loc[
                root_result_dataframe["status"] == status, "_MEAN_DURATION"
            ].sum()

        root_summary_result["total"] = root_summary_result["uptime_duration"] + root_summary_result["downtime_duration"]
        root_summary_result["availability"] = root_summary_result["uptime_duration"] / root_summary_result["total"]
        root_summary_result_dataframe = pandas.DataFrame(root_summary_result, index=[0])

        return root_summary_result_dataframe

    @classmethod
    def phase_statistics(cls, result_dataframe: pandas.DataFrame, root_identifier: str):
        """
        This function creates and returns a dataframe with summary statistics of all phases.
        """

        list_of_phases_start_ok = ["default", "Init"]
        list_of_phases_start_not_ok = ["default failure", "specific failure"]
        list_of_phases_start_specific = ["specific failure"]

        simulation_duration = result_dataframe.loc[
            (result_dataframe["component"] == "Phase"),
            "_MEAN_DURATION"].sum()

        result_dataframe["start_of_phase_ok"] = result_dataframe.loc[
            (result_dataframe["component"] == "Phase") &
            (result_dataframe["description"].isin(list_of_phases_start_ok)),
            "_MEAN_OCCURRENCES"].fillna(0)

        result_dataframe["start_of_phase_not_ok"] = result_dataframe.loc[
            (result_dataframe["component"] == "Phase") &
            (result_dataframe["description"].isin(list_of_phases_start_not_ok)),
            "_MEAN_OCCURRENCES"].fillna(0)

        result_dataframe["start_of_phase_specific"] = result_dataframe.loc[
            (result_dataframe["component"] == "Phase") &
            (result_dataframe["description"].isin(list_of_phases_start_specific)),
            "_MEAN_OCCURRENCES"].fillna(0)

        result_dataframe["failures_in_phase"] = result_dataframe.loc[
            (result_dataframe["component"] == root_identifier) &
            (result_dataframe["status"] == Status.FAILED),
            "_MEAN_OCCURRENCES"].fillna(0)

        result_dataframe["blind_failures_in_phase"] = result_dataframe.loc[
            (result_dataframe["component"] == root_identifier) &
            (result_dataframe["status"] == Status.BLIND_FAILED),
            "_MEAN_OCCURRENCES"].fillna(0)

        result_dataframe["RUNNING_in_phase"] = result_dataframe.loc[
            (result_dataframe["component"] == root_identifier) &
            (result_dataframe["status"] == Status.RUNNING),
            "_MEAN_DURATION"].fillna(0)

        result_dataframe["UNDER_REPAIR_in_phase"] = result_dataframe.loc[
            (result_dataframe["component"] == root_identifier) &
            (result_dataframe["status"] == Status.UNDER_REPAIR),
            "_MEAN_DURATION"].fillna(0)

        result_dataframe["DEGRADED_in_phase"] = result_dataframe.loc[
            (result_dataframe["component"] == root_identifier) &
            (result_dataframe["status"] == Status.DEGRADED),
            "_MEAN_DURATION"].fillna(0)

        result_dataframe['BLIND_DEGRADED_in_phase'] = result_dataframe.loc[
            (result_dataframe["component"] == root_identifier) &
            (result_dataframe["status"] == Status.BLIND_DEGRADED),
            "_MEAN_DURATION"].fillna(0)

        result_dataframe["FAILED_in_phase"] = result_dataframe.loc[
            (result_dataframe["component"] == root_identifier) &
            (result_dataframe["status"] == Status.FAILED),
            "_MEAN_DURATION"].fillna(0)

        result_dataframe["BLIND_FAILED_in_phase"] = result_dataframe.loc[
            (result_dataframe["component"] == root_identifier) &
            (result_dataframe["status"] == Status.BLIND_FAILED),
            "_MEAN_DURATION"].fillna(0)

        result_dataframe["INSPECTION_in_phase"] = result_dataframe.loc[
            (result_dataframe["component"] == root_identifier) &
            (result_dataframe["status"] == Status.INSPECTION),
            "_MEAN_DURATION"].fillna(0)

        result_dataframe = result_dataframe.set_index("phase")
        phases_data_gby = result_dataframe.loc[result_dataframe["component"] == "Phase"].groupby("phase")

        summary_phases = phases_data_gby["_MEAN_OCCURRENCES"].sum().to_frame("OCCURRENCES")
        summary_phases["TOTAL_DURATION"] = phases_data_gby["_MEAN_DURATION"].sum()
        summary_phases["MEAN_DURATION"] = summary_phases["TOTAL_DURATION"] / summary_phases["OCCURRENCES"]

        summary_phases["NORMAL_START_OF_A_PHASE"] = phases_data_gby["start_of_phase_ok"].sum()
        summary_phases["START_OF_A_PHASE_DUE_TO_A_FAILURE"] = phases_data_gby["start_of_phase_not_ok"].sum()
        summary_phases["START_OF_A_PHASE_DUE_TO_A_SPECIFIC_FAILURE"] = phases_data_gby["start_of_phase_specific"].sum()

        summary_phases["SUM_OF_DETECTABLE_FAILURES_IN_A_PHASE"] = result_dataframe["failures_in_phase"].groupby(
            "phase").sum()
        summary_phases["SUM_OF_BLIND_FAILURES_IN_A_PHASE"] = result_dataframe["blind_failures_in_phase"].groupby(
            "phase").sum()

        summary_phases["TOTAL_DURATION_OF_THE_RUNNING_STATUS"] = result_dataframe["RUNNING_in_phase"].groupby(
            "phase").sum()
        summary_phases["TOTAL_DURATION_OF_THE_UNDER_REPAIR_STATUS"] = result_dataframe["UNDER_REPAIR_in_phase"].groupby(
            "phase").sum()
        summary_phases["TOTAL_DURATION_OF_THE_DEGRADED_STATUS"] = result_dataframe["DEGRADED_in_phase"].groupby(
            "phase").sum()
        summary_phases["TOTAL_DURATION_OF_THE_BLIND_DEGRADED_STATUS"] = result_dataframe[
            "BLIND_DEGRADED_in_phase"].groupby(
            "phase").sum()
        summary_phases["TOTAL_DURATION_OF_THE_FAILED_STATUS"] = result_dataframe["FAILED_in_phase"].groupby(
            "phase").sum()
        summary_phases["TOTAL_DURATION_OF_THE_BLIND_FAILED_STATUS"] = result_dataframe["BLIND_FAILED_in_phase"].groupby(
            "phase").sum()
        summary_phases["TOTAL_DURATION_OF_THE_INSPECTION_STATUS"] = result_dataframe["INSPECTION_in_phase"].groupby(
            "phase").sum()

        summary_phases["RATIO_OF_PHASE_WITHOUT_DETECTABLE_FAILURES"] = (summary_phases["OCCURRENCES"] - summary_phases[
            "SUM_OF_DETECTABLE_FAILURES_IN_A_PHASE"]) / summary_phases["OCCURRENCES"]
        summary_phases["FRACTION_OF_UPTIME_WITHIN_THE_PHASE"] = (
            summary_phases["TOTAL_DURATION_OF_THE_RUNNING_STATUS"] +
            summary_phases["TOTAL_DURATION_OF_THE_DEGRADED_STATUS"] +
            summary_phases["TOTAL_DURATION_OF_THE_BLIND_DEGRADED_STATUS"]
            ) / summary_phases["TOTAL_DURATION"]

        summary_phases["FRACTION_OF_UPTIME_WITHIN_THE_TOTAL_DURATION"] = (
            summary_phases["TOTAL_DURATION_OF_THE_RUNNING_STATUS"] +
            summary_phases["TOTAL_DURATION_OF_THE_DEGRADED_STATUS"] +
            summary_phases["TOTAL_DURATION_OF_THE_BLIND_DEGRADED_STATUS"]
            ) / simulation_duration

        summary_phases = summary_phases.reset_index()

        tmp = pandas.DataFrame(summary_phases.sum()).T
        tmp["phase"] = "__SUM_OVER_EVERY_PHASE__"
        summary_phases = pandas.concat([summary_phases, tmp])

        summary_phases = summary_phases.rename(columns={"phase": "PHASE"})

        return summary_phases

    def export(self, results: SimulationResults) -> List[pathlib.Path]:

        result_list_occurrence = self.parse_statistics(results.occurrence_statistics, "OCCURRENCES")
        result_list_duration = self.parse_statistics(results.duration_statistics, "DURATION")
        result_dataframe_occurrence = pandas.DataFrame(result_list_occurrence)
        result_dataframe_duration = pandas.DataFrame(result_list_duration)
        result_dataframe = pandas.merge(result_dataframe_occurrence, result_dataframe_duration,
                                        on=["component", "phase", "status", "description"])
        filepath = self.export_dataframe(result_dataframe, "RESULTS")

        # computing some simple and useful stat
        root_identifier = f"{self.root_component.name}_{self.root_component.local_id}_{self.root_component.global_id}"
        # computing some simple and useful stat of the root component
        root_statistics_dataframe = self.root_statistics(result_dataframe.copy(), root_identifier)
        self.export_dataframe(root_statistics_dataframe, "RESULTS_ROOT_SUMMARY")

        # computing some simple and useful stat on the phases
        phase_statistics_dataframe = self.phase_statistics(result_dataframe.copy(), root_identifier)
        self.export_dataframe(phase_statistics_dataframe, "RESULTS_PHASE_SUMMARY")

        return [filepath]
