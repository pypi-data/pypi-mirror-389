# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for methods shared between all XLSX-type readers.
"""

import logging
import pathlib
from tkinter import NO
from typing import Any, Dict, List, Optional
import pandas
import numpy


class XLSXReaderError(Exception):
    """
    Error indicating problems in reading an XLSX file.
    """

class XLSXReaderEmptyStringError(XLSXReaderError):
    """
    Error caused by encountering an emtpy string while content is required.
    """

class XLSXReaderInvalidValue(XLSXReaderError):
    """
    Error caused by using an invalid value for a parameter (e.g., using a list where only strings are allowed).
    """


PRAGMA_FOR_EXPRESSION = '#'
KEYWORDS_DEFAULT = ["NONE", ""]
KEYWORDS_NONE = ["NONE"]
KEYWORD_COMMENTS = "COMMENTS"

def read(file_path: pathlib.Path) -> Dict[str, pandas.DataFrame]:
    """
    Read the XLSX files at the location given by the parameter and return its contents as a dictionary of Pandas
    dataframes. Keys of the dictionaries will be set to worksheet names.

    Args:
        file_path
            Location of the xlsx-style file.

    Returns
        A dictionary of the Pandas dataframes created from the given file.
    """
    data = pandas.read_excel(file_path,
                             sheet_name=None,
                             engine='openpyxl',
                             keep_default_na=False,
                             dtype=str)

    dictionary = {}
    for key in data.keys():
        dictionary[key] = data[key].to_dict('index')
    return dictionary

# Functions returning certain types read from cells

def clean_boolean_cell(row, column_name: str, exception_message_hint: str = "", optional: bool = False) -> bool:
    """
    Extracts a unique boolean value from a string, ingnoring unnecessary characters.
    Args:
        entry_str (str): String which is to be validated and cleaned.
        exception_message_hint (str): Hint about where the string comes from to augment the exception message.

    Returns:
        float: The float submitted by the user.

    Raises:
        XLSXReaderInvalidValue: if the user attempts to pass something else than an integer.
        XLSXReaderEmptyStringError: if the output string is empty.
    """
    cleaned_cell_content = read_clean_string_from_cell(row, column_name, exception_message_hint, optional)
    accepted_true_strings = ["TRUE", "1", "YES"]

    return cleaned_cell_content in accepted_true_strings

def clean_int_cell(row, column_name: str, exception_message_hint: str = "", optional: bool = False) -> Optional[int]:
    """
    Extracts a unique number from a string, ingnoring unnecessary characters. Checks if the contents of the cleaned
    {entry_str} contain a list. If any additional restictions are to be put on fields containing strictly individual
    integer, they can be added here.

    Args:
        entry_str (str): String which is to be validated and cleaned.
        exception_message_hint (str): Hint about where the string comes from to augment the exception message.

    Returns:
        int: The integer submitted by the user.

    Raises:
        XLSXReaderInvalidValue: if the user attempts to pass something else than an integer.
        XLSXReaderEmptyStringError: if the output string is empty.
    """
    cleaned_cell_content = read_clean_string_from_cell(row, column_name, exception_message_hint, optional)

    try:
        return int(cleaned_cell_content)
    except ValueError as exc:
        if optional:
            return None
        else:
            message_exception = f"The string {cleaned_cell_content} does not contain an individual integer." \
                                f"Additional information about this error: {exception_message_hint}"
            logging.exception(message_exception)
            raise XLSXReaderInvalidValue(message_exception) from exc

def clean_float_cell(row, column_name: str, exception_message_hint: str = "", optional: bool = False) -> float:
    """
    Extracts a unique number from a string, ingnoring unnecessary characters. Checks if the contents of the cleaned
    {entry_str} contain a list. If any additional restictions are to be put on fields containing strictly individual
    float, they can be added here.

    Args:
        entry_str (str): String which is to be validated and cleaned.
        exception_message_hint (str): Hint about where the string comes from to augment the exception message.

    Returns:
        float: The float submitted by the user.

    Raises:
        XLSXReaderInvalidValue: if the user attempts to pass something else than an integer.
        XLSXReaderEmptyStringError: if the output string is empty.
    """
    cleaned_cell_content = read_clean_string_from_cell(row, column_name, exception_message_hint, optional)

    try:
        return float(cleaned_cell_content)
    except ValueError as exc:
        message_exception = f"The string {cleaned_cell_content} does not contain an individual floating point" \
                            f"number. Additional information about this error: {exception_message_hint}"
        logging.exception(message_exception)
        raise XLSXReaderInvalidValue(message_exception) from exc

def clean_str_cell(row, column_name: str, exception_message_hint: str = "", optional: bool = False) -> str:
    """
    Extracts a unique word within a string, removing unnecessary characters and forcing to uppercase. Tests the
    contents of the cleaned {entry_str} contains a list. If any additional restictions are to be put on fields
    containing strictly individual values (as opposed to lists), they can be added here.

    Args:
        entry_str (str): String which is to be validated and cleaned.
        exception_message_hint (str): Hint about where the string comes from to augment the exception message.

    Returns:
        str: The string without invalid characters.

    Raises:
        XLSXReaderInvalidValue: if the input is a list.
        XLSXReaderEmptyStringError: if the output string is empty.
    """
    ret = read_clean_string_from_cell(row, column_name, exception_message_hint, optional)

    if (ret[0] == "[" and ret[-1] == "]") or ',' in ret:
        message_exception = f"The string {ret} is a list. Lists are not allowed in this parameter." \
                            f"Additional information about this error: {exception_message_hint}"
        logging.exception(message_exception)
        raise XLSXReaderInvalidValue(message_exception)
    return ret

def remove_special_chars(text: str) -> str:
    """Removes all characters (space & quotation marks) as well as makes the text upper case.

    Args:
        text (str): input string.

    Returns:
        str: uppercase string without spaces, quotation marks
    """
    return text.replace(" ", "").replace("'", "").replace('"', '').replace('“', '').replace('”', '').upper()

def read_clean_string_from_cell(row, column_name: str, exception_message_hint: str = "", optional = False) -> str:
    """
    Extracts a unique word within a string, removing spaces, quote marks and making it uppercase.

    Args:
        entry_str (str): Input string.
        exception_message_hint (str): Hint about where the string comes from to augment the exception message.

    Returns:
        str: The string without invalid characters.

    Raises:
        XLSXReaderEmptyStringError: if the output string is empty.
    """
    cell_content = get_cell_text(row, column_name, optional)
    cell_content = remove_special_chars(cell_content)
    if cell_content == "" and not optional:
        message_exception = f"Empty string in one cell, here is an exception_message_hint," \
                            f"maybe: {exception_message_hint}"
        logging.exception(message_exception)
        raise XLSXReaderEmptyStringError(message_exception)
    return cell_content

def clean_list_cell(row, column_name: str, optional=False, exception_message_hint: str = "") -> List[Any]:
    """
    Extracts elements from a given list in the format '[1., 2., 3.]'
    :param cell_entry_str is a string representing either a list of float or a list of string.
    :param exception_message_hint: hint about where does the string comes from in order to
    print a debug information
    """

    def evaluate_cell_expression(cell_entry_str):
        output_list = eval(cell_entry_str[1:])
        if isinstance(output_list,(numpy.ndarray,range)):
            output_list=list(output_list)
        if not isinstance(output_list,list):
            message_exception = f"A string containing {PRAGMA_FOR_EXPRESSION} as " \
                                f"first character has been evaluated to extract a list out " \
                                f"of it but the attempt failed. The content of the string " \
                                f"is {cell_entry_str}, the variable evaluated is " \
                                f"{output_list} of type {type(output_list)}"
            logging.exception(message_exception)
            raise XLSXReaderError(message_exception)
        return output_list

    def evaluate_cell_list(row, column_name, exception_message_hint, optional):
        """This function has to handle manually typed lists

         Example lists: "1", "[1, 2, 3, 4]", "[1], [2], [3]", "graph, summary", "[“graph”, “summary”]",
         "[[1, 2], [3, 4]]", "[1, 2, 3], [4, 5, 6]"
        """
        cell_entry_str = read_clean_string_from_cell(row, column_name, exception_message_hint + "- cleaning string of a list", optional)
        def parse(string):
            lists_pointers = [[]]
            word_buffer = []

            def start_list():
                new_list = []
                lists_pointers[-1].append(new_list)
                lists_pointers.append(new_list)

            def end_list():
                if word_buffer:
                    new_element()
                lists_pointers.pop()

            def new_element():
                if not lists_pointers[0]:
                    start_list()
                if word_buffer:
                    element = "".join(word_buffer)
                    try:
                        element = float(element)
                    except ValueError:
                        pass
                    lists_pointers[-1].append(element)
                    word_buffer.clear()

            actions = {
                '[': start_list,
                ']': end_list,
                ',': new_element
            }

            for char in string:
                actions.get(char, lambda: word_buffer.append(char))()

            if word_buffer:
                new_element()
            return lists_pointers[0][0] if len(lists_pointers[0]) == 1 else lists_pointers[0]

        return parse(cell_entry_str)

    cell_entry_str = get_cell_text(row, column_name, optional)
    # if the string start with a '#', then it's some expression to evaluate
    if len(cell_entry_str) > 0 and cell_entry_str[0] == PRAGMA_FOR_EXPRESSION:
        output_list = evaluate_cell_expression(cell_entry_str)
    else:
        output_list = evaluate_cell_list(row, column_name, exception_message_hint, optional)

    return output_list

def get_cell_text(row, column_name: str, optional=False, default = "") -> str:
    """Fetching the contents of a cell into a string. If optional, then returns default empty string.

    Args:
        row (pd.Series): row of the Pandas DataFrame from which the cell is to be read
        column_name (str): name of the column which identifies the cell in the row
        optional (bool, optional): whether the cell is allowed to be empty or not exist. Defaults to False.

    Raises:
        e (KeyError): when the cell is not optional, raises a KeyError logging the column name of the missing cell.

    Returns:
        str: string from the input cell.
    """
    try:
        entry_string = row[column_name]
        return str(entry_string)
    except KeyError as e:
        if optional:
            return default
        else:
            logging.debug(f"No obligatory {column_name} column found in the input sheet.")
            raise e

def read_cell_str_with_default(row, column_name, exception_message_hint, default = "") -> str:
    """Calling clean_str_cell unless the cell content is one of the default values; in that case returning the default
    string passed on to this method."""
    cell_content = get_cell_text(row, column_name, optional=True, default=default).upper()
    return default if cell_content in KEYWORDS_DEFAULT else clean_str_cell(row, column_name, exception_message_hint)

def read_cell_list_with_default(row, column_name, exception_message_hint, default = None):
    """It's a shorthand function for returning a default value if the input cell is empty (as defined by the parameter)
    or parsing a list from that cell"""
    cell_content = get_cell_text(row, column_name, optional=True, default="").upper()
    default = [] if default is None else default
    return default if cell_content in KEYWORDS_DEFAULT else clean_list_cell(row, column_name, exception_message_hint)
