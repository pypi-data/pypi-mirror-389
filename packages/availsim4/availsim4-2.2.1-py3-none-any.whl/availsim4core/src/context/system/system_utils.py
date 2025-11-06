# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

from availsim4core.src.context.system.component_tree.component import Component


class SystemUtils:
    # TODO: use regexp instead of manipulating the string ourselves

    @staticmethod
    def is_string_containing_parenthesis(input_text: str):
        return "(" in input_text and ")" in input_text

    @staticmethod
    def extract_arguments_within_parenthesis(input_text: str):
        """
        format of the string: X(Y)
        X = name of function
        Y = list of arguments
        """
        return input_text.split("(")[1].split(")")[0]

    @staticmethod
    def extract_name_of_function_from_string(str_input: str):
        """
        format of the string: X(Y)
        X = name of function
        Y = list of arguments
        """
        return str_input.split("(")[0]

    @classmethod
    def find_first_lowest_level_ancestor_with_name(cls,
                                                   component: Component,
                                                   ancestor_name: str):
        """
        Find the lowest level first ancestor parent from the given the component parents and based on the given ancestor name.
        None otherwise.
        :param component: The component to inspect.
        :param ancestor_name: the name of the lowest common parent.
        :return: the ancestor parent of the given component with the name, None otherwise.
        """

        found_ancestor_tuple_list = cls._find_ancestors_and_treelevel_with_name(component,
                                                                                ancestor_name,
                                                                                0)
        return None if not found_ancestor_tuple_list \
            else sorted(found_ancestor_tuple_list, key=lambda ancestor: ancestor[1])[0][0]

    @classmethod
    def _find_ancestors_and_treelevel_with_name(cls,
                                                component: Component,
                                                ancestor_name: str,
                                                tree_level: int):
        if component.name == ancestor_name:
            return [(component, tree_level)]
        found_ancestor_tuple_list = []
        tree_level += 1
        for parent in component.get_parents():
            found_ancestors = cls._find_ancestors_and_treelevel_with_name(parent,
                                                                          ancestor_name,
                                                                          tree_level)
            found_ancestor_tuple_list.extend(found_ancestors)
        return found_ancestor_tuple_list
