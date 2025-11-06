# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for the ComponentFactory class
"""

import logging
import pathlib
from typing import List, Optional

from availsim4core.src.context.system.architecture_entry import ArchitectureEntry
from availsim4core.src.context.system.children_logic import children_logic_factory
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.component import Component, ComponentType
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system import sanity_check
from ..minimal_replaceable_unit import MinimalReplaceableUnit
from availsim4core.src.context.system.system_template import SystemTemplate
from availsim4core.src.context.system.system_utils import SystemUtils


class ComponentTypeError(Exception):
    """
    Error returned when a component's type is not conforming to any type defined in the framework
    """


class EmptySystemException(Exception):
    """
    Error raised when the Architecture input sheet is empty (or its represetnation is provided as an
    empty list in the SystemTemplate object)
    """


class ComponentFactory:
    """
    class used to handle components describing a system
    """

    def __init__(self,
                 system_template: SystemTemplate):
        self.system_template = system_template
        self.shared_children_list: List[Component] = []
        self.uniq_id = 0

    def build(self) -> Component:
        """
        Function generating a system from a dictionary describing a system
        :return: the single root node of tree representing the system.
        """
        # checking if tree is empty
        if not self.system_template.architecture_entry_list:
            message_exception = "The system architecture tree is empty."
            logging.exception("The system architecture tree is empty.")
            raise EmptySystemException(message_exception)

        # find root component, root component is the first line of the architecture tab.
        root_architecture_entry = \
            self.system_template.architecture_entry_list[0]

        component_list = self._add_component(root_architecture_entry,
                                             [],
                                             self.system_template.custom_children_logic_path)

        root_node = component_list[0]

        if not sanity_check.run(self.system_template, root_node):
            logging.warning('The input file and simulated tree do not match perfectly,'
                            'please check the warnings.')

        return root_node

    def _add_component(self,
                       architecture_entry: ArchitectureEntry,
                       parents: List[Compound],
                       custom_children_logic_path: pathlib.Path) -> List[Component]:
        """
        Recursive method to build the system graph.
        :param architecture_entry: The architecture_entry of the component to add in the system.
        :param parents: list of component parents of the component to add.
        :param custom_children_logic_path: string defining the path toward an optional python file
        containing custom children logic
        :return: List of the sibling components.
        """
        new_components: List[Component] = []
        if architecture_entry.component_type == ComponentType.BASIC:
            new_components.extend(self._add_basics(architecture_entry, parents))
        elif architecture_entry.component_type == ComponentType.COMPOUND:
            new_components.extend(self._add_compound(architecture_entry,
                                                                 parents,
                                                                 custom_children_logic_path))
        else:
            message_exception = \
                       f"{architecture_entry.component_name} wrong type of component for component."
            logging.exception(message_exception)
            raise ComponentTypeError(message_exception)
        return new_components

    def _add_basics(self,
                    architecture_entry: ArchitectureEntry,
                    parents: List[Compound]) -> List[Basic]:
        """
        Part of the recursive logic from the _add_component.
        This methods creates a list of sibling Basic Components and return it.
        :param architecture_entry
        :param parents: the parents component for each of the basic components.
        :return: a list of Basics.
        """

        list_of_mrus__group = self._get_list_of_mru_from_list_of_strings(self.system_template.mru_list,
                                                                 architecture_entry.in_mru_str_list)

        list_of_mrus__trigger = self._get_list_of_mru_from_list_of_strings(self.system_template.mru_list,
                                                            architecture_entry.trigger_mru_str_list)

        if len(architecture_entry.children_name_list) > 0 or architecture_entry.children_logic != '':
            msg = f"The component {architecture_entry.component_name} is basic, but has children names defined."
            logging.exception(msg)
            raise ComponentTypeError(msg)

        list_of_basic = []
        for component_number in range(0, int(architecture_entry.component_number)):
            self.uniq_id = self.uniq_id + 1
            for failure_mode_assignments in self.system_template.failure_mode_assignments_list:
                if failure_mode_assignments.component_name == architecture_entry.component_name:
                    list_of_basic.append(Basic(self.uniq_id,
                                               architecture_entry.component_name,
                                               component_number,
                                               parents.copy(),
                                               failure_mode_assignments.failure_mode,
                                               list_of_mrus__trigger,
                                               list_of_mrus__group))
        return list_of_basic

    @staticmethod
    def _get_list_of_mru_from_list_of_strings(minimal_replaceable_units: List[MinimalReplaceableUnit],
                                              names_of_minimal_replacable_units: List[str]) \
                                                                                        -> List[MinimalReplaceableUnit]:
        """
        This function returns all MinimalReplaceableUnits that are defined in a list provided as a first argument that
        have names matching any string specified in the list provided as the second argument
        """
        return [mru for mru in minimal_replaceable_units
                    if mru.name in names_of_minimal_replacable_units]



    def _add_component_from_architecture_entry_name(self,
                                                    architecture_entry_name: str,
                                                    parents: List[Compound],
                                                    custom_children_logic_path: pathlib.Path) -> List[Component]:
        architecture_entry = self.system_template.find_architecture_entry(architecture_entry_name)
        if architecture_entry is not None:
            return self._add_component(architecture_entry,
                                       parents,
                                       custom_children_logic_path)

        # skips the child whose name has not been recognized
        logging.warning("child name %s of parents %s not found",
                        architecture_entry_name,
                        parents)
        return []

    def _add_compound(self,
                      architecture_entry: ArchitectureEntry,
                      parents: List[Compound],
                      custom_children_logic_path: pathlib.Path) -> List[Compound]:
        """
        Part of the recursive logic from the _add_component.
        This methods instantiates a new list of Compounds and their associated children.
        If the children are shared with multiple parents, they are created and stored in the
        shared_children_list.
        If the shared children has been created, then the compound is added to the list of parents.
        If the children is not shared (normal), then the children are created by calling the
        _add_component method.
        :param architecture_entry: the line describing the component within the input file
        :param parents: the list of parents.
        :param custom_children_logic_path: string defining the path toward an optional python file
        containing custom
        :return: list of the sibling compounds.
        """

        list_of_mru__trigger = self._get_list_of_mru_from_list_of_strings(self.system_template.mru_list,
                                                            architecture_entry.trigger_mru_str_list)
        if len(architecture_entry.children_name_list) == 0 or architecture_entry.children_logic == '':
                msg = f"The component {architecture_entry.component_name} is compound, but its list of children is " \
                      f"'{architecture_entry.children_name_list}' and its children logic string is "\
                      f"'{architecture_entry.children_logic}'."
                logging.exception(msg)
                raise ComponentTypeError(msg)

        list_compounds: List[Compound] = []
        for component_number in range(0, int(architecture_entry.component_number)):
            self.uniq_id = self.uniq_id + 1

            children_logic = children_logic_factory.build(architecture_entry.children_logic,
                                                        custom_children_logic_path)

            compound = Compound(self.uniq_id,
                                architecture_entry.component_name,
                                component_number,
                                parents,
                                children_logic,
                                list_of_mru__trigger)
            list_compounds.append(compound)

            for child_name in architecture_entry.children_name_list:
                component_children: List[Component] = []
                if SystemUtils.is_string_containing_parenthesis(child_name):
                    # string containing a parenthesis indicates a shared children logic
                    shared_child_list: Optional[List[Component]] = self.find_shared_children(compound,
                                                                                             child_name,
                                                                                             self.shared_children_list)
                    if shared_child_list:
                        # component exists in the shared_child_list of this factory
                        for shared_child in shared_child_list:
                            shared_child.add_parent(compound)
                        component_children = shared_child_list
                    else:
                        # it's the first encounter of the child across the system, so it needs to be created first
                        component_child_name = SystemUtils.extract_name_of_function_from_string(child_name)
                        component_children = self._add_component_from_architecture_entry_name(component_child_name,
                                                                                             [compound],
                                                                                             custom_children_logic_path)
                        self.shared_children_list.extend(component_children)
                else:
                    component_children = self._add_component_from_architecture_entry_name(child_name,
                                                                                          [compound],
                                                                                          custom_children_logic_path)
                compound.add_children_list(component_children)
        return list_compounds

    @classmethod
    def find_shared_children(cls,
                             compound: Compound,
                             shared_child_name: str,
                             shared_children: List[Component]) -> List[Component]:
        """
        Find the shared child from the shared_children_list based on its name and its compound
        parent.
        :param compound: The parent compound of the child.
        :param shared_child_name_str: the name of the shared child (contains parenthesis)
        :param shared_children_list: the list of shared children already instantiated.
        :return: The shared child if is the list. None otherwise.
        """

        # The agument shared_child_name should look like this: SHARED_COMPONENT(ROOT) where ROOT is the name of a
        # component that sets the scope across which the said component is shared
        shared_component_name: str = SystemUtils.extract_name_of_function_from_string(shared_child_name)
        lowest_common_parent_name: str = SystemUtils.extract_arguments_within_parenthesis(shared_child_name)
        lowest_common_parent: Optional[Compound] = SystemUtils.find_first_lowest_level_ancestor_with_name(compound,
                                                                                              lowest_common_parent_name)
        if lowest_common_parent is None:
            logging.warning("Could not set the scope for a shared child %s. Assuming the entire system as the scope",
                            shared_child_name)

        # Looking for other shared children with the same name
        filtered_shared_children = filter(lambda component: component.name == shared_component_name, shared_children)

        # Filtering the list to find ones within the same scope
        shared_children_found: List[Component] = []
        for shared_child in filtered_shared_children:
            shared_child_common_parent = SystemUtils.find_first_lowest_level_ancestor_with_name(shared_child,
                                                                                              lowest_common_parent_name)
            if lowest_common_parent == shared_child_common_parent:
                shared_children_found.append(shared_child)
        return shared_children_found
