# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.system.children_logic.children_logic import ChildrenLogic
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.system_utils import SystemUtils


class test_SystemUtils(unittest.TestCase):

    def test__is_shared_child_true(self):
        shared_child_name = "A(B)"
        self.assertTrue(SystemUtils.is_string_containing_parenthesis(shared_child_name))

    def test__is_shared_child_false(self):
        shared_child_name = "A"
        self.assertFalse(SystemUtils.is_string_containing_parenthesis(shared_child_name))

    def test__extract_common_parent_name(self):
        shared_child_name = "A(B)"
        self.assertEqual("B", SystemUtils.extract_arguments_within_parenthesis(shared_child_name))

    def test__extract_shared_child_name(self):
        shared_child_name = "A(B)"
        self.assertEqual("A", SystemUtils.extract_name_of_function_from_string(shared_child_name))

    def test_find_first_lowest_level_ancestor_with_name__single_parent(self):
        root_node = Compound(1, "ROOT_NODE", 0, [], ChildrenLogic(), [])
        parent_1 = Compound(2, "A", 1, [root_node], ChildrenLogic(), [])
        component = Compound(3, "C", 2, [parent_1], ChildrenLogic(), [])
        lowest_scope_common_ancestor_name = "ROOT_NODE"

        result = SystemUtils.find_first_lowest_level_ancestor_with_name(component, lowest_scope_common_ancestor_name)

        self.assertEqual(root_node, result)

    def test_find_first_lowest_level_ancestor_with_name__own_ancestor(self):
        root_node = Compound(1, "ROOT_NODE", 0, [], ChildrenLogic(), [])
        lowest_scope_common_ancestor_name = "ROOT_NODE"

        result = SystemUtils.find_first_lowest_level_ancestor_with_name(root_node, lowest_scope_common_ancestor_name)

        self.assertEqual(root_node, result)

    def test_find_first_lowest_level_ancestor_with_name__multiple_parents(self):
        root_node = Compound(1, "ROOT_NODE", 0, [], ChildrenLogic(), [])
        parent_1 = Compound(2, "A", 1, [root_node], ChildrenLogic(), [])
        parent_3 = Compound(3, "B", 2, [root_node], ChildrenLogic(), [])
        component = Compound(4, "C", 3, [parent_1, parent_3], ChildrenLogic(), [])
        lowest_scope_common_ancestor_name = "ROOT_NODE"

        result = SystemUtils.find_first_lowest_level_ancestor_with_name(component, lowest_scope_common_ancestor_name)

        self.assertEqual(root_node, result)

    def test_find_first_lowest_level_ancestor_with_name__check_right_path_tree(self):
        """
                       ROOT_NODE
                       //     \\
         LEVEL 1       A       Z  --> expected
                       |       |
         LEVEL 2       B       D
                       \\     //
                         BASIC
        """
        root_node = Compound(1, "ROOT_NODE", 0, [], ChildrenLogic(), [])
        parent_level_1_left = Compound(2, "A", 1, [root_node], ChildrenLogic(), [])
        parent_level_1_right = Compound(3, "Z", 2, [root_node], ChildrenLogic(), [])
        parent_level_2_left = Compound(4, "B", 2, [parent_level_1_left], ChildrenLogic(), [])
        parent_level_2_right = Compound(5, "D", 2, [parent_level_1_right], ChildrenLogic(), [])
        basic = Compound(6, "BASIC", 2, [parent_level_2_left, parent_level_2_right], ChildrenLogic(), [])
        lowest_scope_common_ancestor_name = "Z"

        result = SystemUtils.find_first_lowest_level_ancestor_with_name(basic, lowest_scope_common_ancestor_name)

        self.assertEqual(parent_level_1_right, result)

    def test_find_first_lowest_level_ancestor_with_name__check_parents_same_name(self):
        """
                        ROOT_NODE
                        //    \\
         LEVEL 1       A       ROOT_NODE  --> expected result
                        \\   //
                         BASIC
        """
        root_node = Compound(1, "ROOT_NODE", 0, [], ChildrenLogic(), [])
        parent_level_1_left = Compound(2, "A", 1, [root_node], ChildrenLogic(), [])
        parent_level_1_right = Compound(3, "ROOT_NODE", 2, [root_node], ChildrenLogic(), [])
        basic = Compound(6, "BASIC", 2, [parent_level_1_left, parent_level_1_right], ChildrenLogic(), [])
        lowest_scope_common_ancestor_name = "ROOT_NODE"

        result = SystemUtils.find_first_lowest_level_ancestor_with_name(basic, lowest_scope_common_ancestor_name)

        self.assertEqual(parent_level_1_right, result)

    def test_find_first_lowest_level_ancestor_with_name__two_nodes_same_name_different_scopes(self):
        root_node = Compound(1, "ROOT_NODE", 0, [], ChildrenLogic(), [])

        lowest_common_parent_1 = Compound(2, "B", 1, [root_node], ChildrenLogic(), [])
        parent_1 = Compound(3, "D", 1, [lowest_common_parent_1], ChildrenLogic(), [])
        parent_2 = Compound(4, "E", 1, [lowest_common_parent_1], ChildrenLogic(), [])
        shared_component_1 = Compound(5, "C", 1, [parent_1, parent_2], ChildrenLogic(), [])

        lowest_common_parent_2 = Compound(6, "B", 2, [root_node], ChildrenLogic(), [])
        parent_3 = Compound(7, "D", 1, [lowest_common_parent_2], ChildrenLogic(), [])
        parent_4 = Compound(8, "E", 1, [lowest_common_parent_2], ChildrenLogic(), [])
        shared_component_2 = Compound(9, "C", 1, [parent_3, parent_4], ChildrenLogic(), [])

        lowest_scope_common_ancestor_name = "B"

        result_shared_component_1 = SystemUtils.find_first_lowest_level_ancestor_with_name(shared_component_1,
                                                                                           lowest_scope_common_ancestor_name)

        self.assertEqual(lowest_common_parent_1, result_shared_component_1)

        result_shared_component_2 = SystemUtils.find_first_lowest_level_ancestor_with_name(shared_component_2,
                                                                                           lowest_scope_common_ancestor_name)

        self.assertEqual(lowest_common_parent_2, result_shared_component_2)
