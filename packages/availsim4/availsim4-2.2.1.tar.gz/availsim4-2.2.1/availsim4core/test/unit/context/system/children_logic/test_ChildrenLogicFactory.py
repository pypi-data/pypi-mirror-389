# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for tests of the children_logic_factory module
"""

import unittest

from availsim4core.src.context.system.children_logic.and_ import And
from availsim4core.src.context.system.children_logic import children_logic_factory
from availsim4core.src.context.system.children_logic.oo import Oo
from availsim4core.src.context.system.children_logic.required_component import RequiredComponent
from availsim4core.src.context.system.children_logic.tolerated_fault import ToleratedFault


class test_ChildrenLogicFactory(unittest.TestCase):
    scenario_1 = ["AND", And]
    scenario_2 = ["10RC", RequiredComponent]
    scenario_3 = ["1OO2", Oo]
    scenario_4 = ["10TF", ToleratedFault]
    build_scenario = [scenario_1, scenario_2, scenario_3, scenario_4]

    def test_build(self):
        for children_logic_str, expected_children_logic_instance in self.build_scenario:
            with self.subTest():
                self._build(children_logic_str, expected_children_logic_instance)

    def _build(self, children_logic_str, expected_children_logic_instance):
        result = children_logic_factory.build(children_logic_str,None)
        self.assertIsInstance(result, expected_children_logic_instance)

    def test_build_exception(self):
        self.assertRaises(children_logic_factory.ChildrenLogicFactoryError,
                          children_logic_factory.build,
                          "invalid_children_logic_str",
                          None)


if __name__ == '__main__':
    unittest.main()
