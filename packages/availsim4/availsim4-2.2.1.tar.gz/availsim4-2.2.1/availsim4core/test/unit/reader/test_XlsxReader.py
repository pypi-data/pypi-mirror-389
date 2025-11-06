# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for testing functions of the XLSX Reader class.
"""

import unittest
import pandas as pd

from availsim4core.src.reader.xlsx import xlsx_utils

class test_XlsxReader(unittest.TestCase):
    """
    This class tests utility functions used to read and clean strings read from the XLSX files.
    """

    def test_clean_str_cell(self):
        """
        Checking if the string cleaning works properly by removing brackets, spaces and making all letters uppercase
        """
        test_cases = [pd.Series({"ROW": "[1, 2, 3]"}), pd.Series({"ROW": "[“1.“, “2.“, “3.“]"}), pd.Series({"ROW": "[\"aBa\", \"CCC\", \"tte\"]"})]
        test_answers = ["[1,2,3]", "[1.,2.,3.]", "[ABA,CCC,TTE]"]
        for row, answer in zip(test_cases, test_answers):
            self.assertEqual(xlsx_utils.read_clean_string_from_cell(row, "ROW", ""), answer)

    def test_clean_str_cell_empty(self):
        """
        Ensuring that the funtion cleaning string raises an exception when provided empty string
        """
        row = pd.Series({"COLUMN_NAME": ""})
        self.assertRaises(xlsx_utils.XLSXReaderEmptyStringError, xlsx_utils.clean_str_cell, row, column_name="COLUMN_NAME")

    def test_clean_list_cell(self):
        """
        Tests of the function extracting elements from lists
        """
        test_case_answer_tuples = [(pd.Series({"ROW": "1.0"}), [1.0]),
                                   (pd.Series({"ROW": "8"}), [8.0]),
                                   (pd.Series({"ROW": "11, 22, 33, 44"}), [11.0, 22.0, 33.0, 44.0]),
                                   (pd.Series({"ROW": "[10, 20, 30, 40]"}), [10.0, 20.0, 30.0, 40.0]),
                                   (pd.Series({"ROW": "[graph, summary, rca]"}), ["GRAPH", "SUMMARY", "RCA"]),
                                   (pd.Series({"ROW": "[[1.], [2.], [3.]]"}), [[1.0], [2.0], [3.0]]),
                                   (pd.Series({"ROW": "[4], [5], [6]"}), [[4.0], [5.0], [6.0]]),
                                   (pd.Series({"ROW": "[[1., 9.], [2., 8.], [3., 7.]]"}), [[1.0, 9.0], [2.0, 8.0], [3.0, 7.0]]),
                                   ]
        for row, answer in test_case_answer_tuples:
            self.assertEqual(xlsx_utils.clean_list_cell(row, "ROW"), answer)
