# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for the common functions of all XLSX result exporters.
"""

import pathlib
import pandas

from availsim4core.src.exporter.exporter import Exporter


class XLSXExporter(Exporter):
    """
    Abstract class defining common methods for all result exporters dealing with XLSX files.
    """

    # The output template is the following: simulation_result_[analysis_id]
    OUTPUT_FILENAME_TEMPLATE = "simulation_result_{}_{}.xlsx"

    def get_concrete_filepath(self) -> pathlib.Path:
        """
        This function returns filepath to the output Excel file.
        """
        output_file = self.OUTPUT_FILENAME_TEMPLATE.format(self.analysis.id,
                                                      self.unique_output_file_identifier)
        output_filepath = pathlib.Path(self.output_folder) / output_file
        return output_filepath

    def export_dataframe(self,
                         dataframe: pandas.DataFrame,
                         sheet_name: str) -> pathlib.Path:
        """
        This function adds a new spreadsheet with dataframe contents to the output Excel file.
        """
        output_filepath = self.get_concrete_filepath()
        with self.open_workbook(output_filepath) as writer:
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
        return output_filepath

    @staticmethod
    def open_workbook(output_file: pathlib.Path) -> pandas.ExcelWriter:
        """
        Function provides an ExcelWriter from Pandas library to write or append new spreadsheets.

        :param output_file: path to the output file where data is to be stored
        :return writer: object allowing to write sheets into an excel file using a dataframe as the source of data
        """
        try:
            writer = pandas.ExcelWriter(output_file, engine="openpyxl", mode="a") # pylint: disable=abstract-class-instantiated
        except FileNotFoundError: # the file doesn't exist at first, so we have to create it
            writer = pandas.ExcelWriter(output_file, engine="openpyxl", mode="w") # pylint: disable=abstract-class-instantiated
        return writer
