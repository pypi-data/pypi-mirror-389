# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for an the interface InputFileExporter which defines methods for exporters that can be used to copy the inputs.
"""
from abc import ABC, abstractmethod

import pathlib


class InputFileExporter(ABC):
    """
    Interface to define methods of the exporter.
    """

    @abstractmethod
    def export_simulation_to_file(self, file_name: pathlib.Path) -> None:
        """
        Exports the simulation file to a given location.

        Args:
            file_name:
                The file name which will be appended to the path set in the output_folder parameter.
        """

    @abstractmethod
    def export_system_to_file(self, file_name: pathlib.Path) -> pathlib.Path:
        """
        Exports the system file to a given location.

        Args:
            file_name:
                The file name which will be appended to the path set in the output_folder parameter.
        """
