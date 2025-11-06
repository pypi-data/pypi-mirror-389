# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from collections import Counter, defaultdict

from availsim4core.src.results.results import Results
from availsim4core.src.statistics.statistics import Statistics
from availsim4core.src.timeline.timeline import Timeline


class SimulationResults(Results):
    """
    statistics used to profile the execution of the code
    """

    def __init__(self,
                 maximum_number_of_simulations,
                 duration_of_a_simulation):
        self.maximum_number_of_simulations = maximum_number_of_simulations
        self.duration_of_a_simulation = duration_of_a_simulation

        self.number_of_DES_simulations_executed = {}

        self.execution_metrics_statistics = {}
        self.occurrence_statistics = {}
        self.duration_statistics = {}

        self.last_simulation_timeline = []
        self.root_cause_analysis_records = []

        self.execution_time = 0

    def __str__(self) -> str:
        return str(self.__dict__)

    def update_with_des_results(self,
                                execution_metrics: dict,
                                timeline: Timeline,
                                weight: float = 1):
        """
        Update the results given the metric about the code execution and the full timeline of the discrete event simulation.
        :return:
        """
        self._update_execution_metrics(execution_metrics, weight)
        self._update_occurrence_statistics(timeline, weight)
        self._update_duration_statistics(timeline, weight)

    def _update_execution_metrics(self, execution_metrics, weight):

        for key, value in execution_metrics.items():
            if key not in self.execution_metrics_statistics.keys():
                self.execution_metrics_statistics[key] = Statistics()
            statistics = self.execution_metrics_statistics[key]
            statistics.update(value, weight)

    def _update_occurrence_statistics(self, timeline, weight):

        result_record_entry_list = list(map(lambda record: record.get_result_record_entry(),
                                            timeline.record_list))
        counter = Counter(result_record_entry_list)

        for result_record_entry, occurrence in counter.items():
            if result_record_entry not in self.occurrence_statistics:
                self.occurrence_statistics[result_record_entry] = Statistics()
            statistics = self.occurrence_statistics[result_record_entry]
            statistics.update(occurrence, weight)

    def _update_duration_statistics(self, timeline, weight):
        def full_group_by(l, key=lambda x: x):
            d = defaultdict(list)
            for item in l:
                d[key(item)].append(item)
            return d.values()

        record_list_sorted_by_identifier = [g
                                            for g in full_group_by(timeline.record_list,
                                                                   key=lambda
                                                                       r: r.get_result_record_entry().identifier())]

        result_record_entry_duration_dict = {}
        for record_list in record_list_sorted_by_identifier:
            sorted_record_list = record_list
            for index, record in enumerate(sorted_record_list):
                if index + 1 < len(sorted_record_list):
                    duration = sorted_record_list[index + 1].timestamp - record.timestamp
                else:
                    duration = self.duration_of_a_simulation - record.timestamp

                result_record_entry = record.get_result_record_entry()
                if result_record_entry in result_record_entry_duration_dict:
                    result_record_entry_duration_dict[result_record_entry] += duration
                else:
                    result_record_entry_duration_dict[result_record_entry] = duration

        for result_record_entry, record_duration in result_record_entry_duration_dict.items():
            if result_record_entry not in self.duration_statistics:
                self.duration_statistics[result_record_entry] = Statistics()
            statistics = self.duration_statistics[result_record_entry]
            statistics.update(record_duration, weight)

    def evaluate_result(self, number_of_iterations: int = 1):

        for statistics in self.execution_metrics_statistics.values():
            statistics.evaluate_result(number_of_iterations)

        for statistics in self.occurrence_statistics.values():
            statistics.evaluate_result(number_of_iterations)

        for statistics in self.duration_statistics.values():
            statistics.evaluate_result(number_of_iterations)
