# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.minimal_replaceable_unit import MinimalReplaceableUnit
from availsim4core.src.context.system.probability_law import probability_law_factory


class test_MinimalReplaceableUnit(unittest.TestCase):

    def test_build_with_one_element(self):
        # GIVEN
        minimal_replaceable_unit_name = "fakeMRU"
        minimal_replaceable_unit_repair_law_name = "FIX"
        minimal_replaceable_unit_repair_parameters = [0]
        minimal_replaceable_repair_schedule = "IMMEDIATE"
        triggering_status_list_of_str = ["FAILED"]
        lowest_common_parent_name_str = "fakeParent"

        # WHEN
        mru_list_generated = MinimalReplaceableUnit.build(minimal_replaceable_unit_name,
                                                                 minimal_replaceable_unit_repair_law_name,
                                                                 minimal_replaceable_unit_repair_parameters,
                                                                 minimal_replaceable_repair_schedule,
                                                                 triggering_status_list_of_str,
                                                                 lowest_common_parent_name_str)

        # THEN
        mru_list_expected = [MinimalReplaceableUnit(minimal_replaceable_unit_name,
                                                    probability_law_factory.build(
                                                        minimal_replaceable_unit_repair_law_name,
                                                        minimal_replaceable_unit_repair_parameters),
                                                    minimal_replaceable_repair_schedule,
                                                    Status.FAILED,
                                                    lowest_common_parent_name_str)]

        self.assertListEqual(mru_list_generated, mru_list_expected)

    def test_build_with_list(self):
        # GIVEN
        minimal_replaceable_unit_name = "fakeMRU"
        minimal_replaceable_unit_repair_law_name = "FIX"
        minimal_replaceable_unit_repair_parameters = [0]
        minimal_replaceable_repair_schedule = "IMMEDIATE"
        triggering_status_list_of_str = ["FAILED", "BLIND_FAILED"]
        lowest_common_parent_name_str = "fakeParent"

        # WHEN
        mru_list_generated = MinimalReplaceableUnit.build(minimal_replaceable_unit_name,
                                                                 minimal_replaceable_unit_repair_law_name,
                                                                 minimal_replaceable_unit_repair_parameters,
                                                                 minimal_replaceable_repair_schedule,
                                                                 triggering_status_list_of_str,
                                                                 lowest_common_parent_name_str)

        # THEN
        mru_list_expected = [MinimalReplaceableUnit(minimal_replaceable_unit_name,
                                                    probability_law_factory.build(
                                                        minimal_replaceable_unit_repair_law_name,
                                                        minimal_replaceable_unit_repair_parameters),
                                                    minimal_replaceable_repair_schedule,
                                                    Status.FAILED,
                                                    lowest_common_parent_name_str),
                             MinimalReplaceableUnit(minimal_replaceable_unit_name,
                                                    probability_law_factory.build(
                                                        minimal_replaceable_unit_repair_law_name,
                                                        minimal_replaceable_unit_repair_parameters),
                                                    minimal_replaceable_repair_schedule,
                                                    Status.BLIND_FAILED,
                                                    lowest_common_parent_name_str)
                             ]

        self.assertListEqual(mru_list_generated, mru_list_expected)
