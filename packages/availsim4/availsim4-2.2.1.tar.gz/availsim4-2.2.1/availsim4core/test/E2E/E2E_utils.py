# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import pathlib
import pandas
import os


class Result:
    """
    class used to defined a results to compare with the results in the results sheet of the output file.
    an expected result is defined by its expected value plus where it is standing in the sheet.
    also if a sensitivity analysis is performed, an id of the output file has to be defined.
    """

    def __init__(self,
                 expected_result,
                 component_name,
                 phase_name,
                 status_name,
                 column_name,
                 file_number=0,
                 tolerance=-1):
        self.expected_result = expected_result
        self.component_name = component_name
        self.phase_name = phase_name
        self.status_name = status_name
        self.column_name = column_name
        self.file_number = file_number
        self.tolerance = tolerance

    def __str__(self):
        return (
            f"file {self.file_number}; {self.component_name}, {self.phase_name}, {self.status_name}, {self.column_name} = "
            f"= {self.expected_result} up to {self.tolerance}th digit")

    def extract_result(self,
                       result_simulation_file_list):

        for result_simulation_file in result_simulation_file_list:
            result_simulation_file_path = pathlib.Path(result_simulation_file)
            # result_simulation_file_number = int(result_simulation_file.split("/")[-1].split("_")[2])
            result_simulation_file_number = int(result_simulation_file_path.stem.split("_")[2])


            if self.file_number == result_simulation_file_number:
                data = pandas.read_excel(result_simulation_file_path,
                                         sheet_name="RESULTS",
                                         engine='openpyxl')

                if self.component_name == "*":
                    data_loc = data.copy()
                else:
                    data_loc = data.loc[(data.component == self.component_name)]

                if not self.phase_name == "*":
                    data_loc = data_loc.loc[(data.phase == self.phase_name)]

                if not self.status_name == "*":
                    data_loc = data_loc.loc[(data.status == self.status_name)]

                result = float(data_loc[self.column_name].sum())

        return result


class RCAResult:
    """
    class defining a result to compare with the results in the RCA results sheet of the output file.
    """

    def __init__(self,
                 expected_result,
                 component_name,
                 phase_name,
                 status_name,
                 file_number=0,
                 tolerance=-1):
        self.expected_result = expected_result
        self.component_name = component_name
        self.phase_name = phase_name
        self.status_name = status_name
        self.file_number = file_number
        self.tolerance = tolerance

    def __str__(self):
        return (
            f"file {self.file_number}; {self.component_name}, {self.phase_name}, {self.status_name} = "
            f"= {self.expected_result} up to {self.tolerance}th digit")

    def extract_result(self,
                       result_simulation_file_list):

        for result_simulation_file in result_simulation_file_list:
            result_simulation_file_number = int(result_simulation_file.split("/")[-1].split("_")[2])

            if self.file_number == result_simulation_file_number:
                data = pandas.read_excel(result_simulation_file,
                                         sheet_name="RESULTS_ROOT_CAUSE_ANALYSIS",
                                         engine='openpyxl')

                if len(data)>0:

                    if self.component_name == "*":
                        data_loc = data.copy()
                    else:
                        data_loc = data.loc[(data.rca_component_trigger == self.component_name)]

                    if not self.phase_name == "*":
                       data_loc = data_loc.loc[(data.rca_phase_trigger == self.phase_name)]

                    if not self.status_name == "*":
                        data_loc = data_loc.loc[(data.rca_status_trigger == self.status_name)]

                    result = len(data_loc)

                else:

                    result = 0

        return result
