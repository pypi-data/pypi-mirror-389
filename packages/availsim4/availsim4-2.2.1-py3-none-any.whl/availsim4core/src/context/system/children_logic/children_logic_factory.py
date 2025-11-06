# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module containing the methods to build objects of ChildrenLogic class.
"""

import importlib.util
import sys
import logging
import pathlib
import re
from typing import Optional

from availsim4core.src.context.system.children_logic.and_ import And
from availsim4core.src.context.system.children_logic.children_logic import ChildrenLogic
from availsim4core.src.context.system.children_logic.oo import Oo
from availsim4core.src.context.system.children_logic.required_component import RequiredComponent
from availsim4core.src.context.system.children_logic.tolerated_fault import ToleratedFault


class ChildrenLogicFactoryError(Exception):
    """Error raised when no children logic was found to be applicable with the specific user input.
    """

def _and_children_logic(_: str) -> And:
    return And()

def _oo_children_logic(children_logic_str: str) -> Oo:
    minimum_number_of_required_component = int(children_logic_str.split('OO')[0])
    total_number_of_component = int(children_logic_str.split('OO')[1])
    return Oo(minimum_number_of_required_component, total_number_of_component)

def _tf_children_logic(children_logic_str: str) -> ToleratedFault:
    fault_tolerance = int(children_logic_str.split('TF')[0])
    return ToleratedFault(fault_tolerance)

def _rc_children_logic(children_logic_str: str) -> RequiredComponent:
    required_component = int(children_logic_str.split('RC')[0])
    return RequiredComponent(required_component)

def _custom_children_logic(children_logic_str: str,
                           custom_children_logic_path: pathlib.Path) -> ChildrenLogic:
    module_name = "user_defined." + custom_children_logic_path.stem

    if module_name not in sys.modules:
        logging.debug("Children logic file %s has not yet been loaded to sys.modules")
        spec = importlib.util.spec_from_file_location(module_name, custom_children_logic_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
    mod = sys.modules[module_name]
    mod.__spec__.loader.exec_module(mod)

    cc_logic = getattr(mod, children_logic_str)
    return cc_logic()

def build(children_logic_str: str, custom_children_logic_path: Optional[pathlib.Path]) -> ChildrenLogic:
    """
    Given a string children logic word, this method instantiates the corresponding children_logic
    class.
    :param children_logic_str: word to analyse from (not case sensitive.)
    :param custom_children_logic_path: string defining the path toward an optional python file
    containing custom
    :return: the children_logic instance corresponding to the given string.
    """

    # this list contains all supported children logic options except for custom logic
    children_logic_patterns = [(r"^AND$", _and_children_logic),
                                (r"^[0-9]*OO[0-9]*$", _oo_children_logic),
                                (r"^[0-9]*TF$", _tf_children_logic),
                                (r"^[0-9]*RC$", _rc_children_logic)]

    # checking if the user-defined string specifies any children logic from the list above
    for pattern, function in children_logic_patterns:
        if re.search(pattern, children_logic_str):
            return function(children_logic_str)

    # case of custom children logic
    if custom_children_logic_path:
        return _custom_children_logic(children_logic_str, custom_children_logic_path)

    # if the function has not returned any value at this point, raise an exception
    exception_message = f"{children_logic_str} not supported type of children logic."
    logging.exception(exception_message)
    raise ChildrenLogicFactoryError(exception_message)
