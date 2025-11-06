# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for an abstract class ResultExporter which defines interface of all exporters.
"""

from __future__ import annotations
from abc import ABC, abstractmethod

from datetime import datetime
import pathlib
from typing import TYPE_CHECKING, List

from availsim4core.src.results.simulation_results import SimulationResults

if TYPE_CHECKING:
    from availsim4core.src.analysis import Analysis
    from availsim4core.src.context.system.component_tree.component import Component


class Exporter(ABC):
    """
    Interface to define methods of the exporter.
    """

    def __init__(self,
                 root_component: Component,
                 analysis: Analysis,
                 output_folder: pathlib.Path,
                 unique_output_file_identifier: str = "") -> None:
        self.root_component = root_component
        self.output_folder = output_folder
        self.analysis = analysis
        if unique_output_file_identifier == "":
            self.unique_output_file_identifier = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        else:
            self.unique_output_file_identifier = unique_output_file_identifier

    @abstractmethod
    def export(self, results: SimulationResults) -> List[pathlib.Path]:
        """
        Exports results.
        :param results {Results} the simulation results.

        The method is expected to return a list paths to files it created or modified.
        """
