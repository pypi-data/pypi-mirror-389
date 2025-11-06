# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.timeline.timeline import Timeline


class Results:
    """
    The interface for the simulation results.
    """

    def update_with_des_results(self,
                                execution_metrics: dict,
                                timeline: Timeline):
        """
        Update the results given the metric about the code execution and the full timeline of the discrete event simulation.
        :return:
        """
        pass

    def evaluate_result(self):
        """
        Evaluates the results at the end of all the simulation process, when all the des have been proceed.
        :return:
        """
        pass
