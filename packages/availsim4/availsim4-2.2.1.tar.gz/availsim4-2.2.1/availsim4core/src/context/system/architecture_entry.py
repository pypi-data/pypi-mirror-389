# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for ArchitectureEntry
"""

from typing import List, Optional

from availsim4core.src.context.system.system_element import SystemElement


class ArchitectureEntry(SystemElement):
    """
    This class serves as a model of a single row describing the system in the ARCHITECTURE input sheet
    """

    def __init__(self, component_name: str, component_type: str, component_number: int, children_name_list: List[str],
                 children_logic: str, in_mru_str_list: List[str], trigger_mru_str_list: List[str],
                 comments: Optional[str] = ""):
        self.component_name: str = component_name
        self.component_type: str = component_type
        self.component_number: int = component_number
        self.children_name_list: List[str] = children_name_list
        self.children_logic: str = children_logic
        self.in_mru_str_list: List[str] = in_mru_str_list
        self.trigger_mru_str_list: List[str] = trigger_mru_str_list
        super().__init__(comments)

    def __str__(self):
        return (f"name: {self.component_name}; "
                f"type: {self.component_type}; "
                f"number: {self.component_number}; "
                f"children: {self.children_name_list}; "
                f"logic: {self.children_logic}; "
                f"in mru: {self.in_mru_str_list}; "
                f"trigger mru: {self.trigger_mru_str_list}; "
                f"comments: {self.comments}")

    def __eq__(self, other):
        return self.component_name == other.component_name \
               and self.component_type == other.component_type \
               and self.component_number == other.component_number \
               and self.children_name_list == other.children_name_list \
               and self.children_logic == other.children_logic \
               and self.in_mru_str_list == other.in_mru_str_list \
               and self.trigger_mru_str_list == other.trigger_mru_str_list \
               and self.comments == other.comments
