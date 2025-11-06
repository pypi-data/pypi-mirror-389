# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.context import Context
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.children_logic.and_ import And
from availsim4core.src.context.system.children_logic.children_logic import ChildrenLogic
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.timeline.record_component import RecordComponent


class test_Component(unittest.TestCase):

    def test__eq__(self):
        compound_1 = Compound(1, "test_compound_1", 0, [], ChildrenLogic(), [])
        compound_2 = Compound(1, "test_compound_1", 0, [], ChildrenLogic(), [])

        self.assertEqual(compound_1, compound_2)

    def test_update_status__single_new_status(self):

        context = Context(None, None, None)

        component = Basic(1, "test_compound_1", 1, [], [], [], [])

        new_status = Status.FAILED
        timestamp = 916
        phase = PhaseManager.NO_PHASE
        description = "test"

        result = component._update_status(new_status, timestamp, phase, description, context)
        expected_result = [RecordComponent(component, new_status, timestamp, phase, description)]
        self.assertEqual(result, expected_result)
        self.assertEqual(component.status, new_status)

    def test_update_status__single_same_status(self):

        context = Context(None, None, None)

        component = Basic(1, "test_compound_1", 1, [], [], [], [])

        new_status = Status.RUNNING
        timestamp = 916
        phase = PhaseManager.NO_PHASE
        description = "test"

        result = component._update_status(new_status, timestamp, phase, description, context)
        # new_status of the component is the same as the previous one, no record.
        expected_result_not_in = RecordComponent(component, new_status, timestamp, phase, description)
        self.assertEqual(component.status, new_status)
        self.assertNotIn(expected_result_not_in, result)

    def test_update_status__multiple_status_sorted_by_timestamp(self):

        context = Context(None, None, None)

        component = Basic(1, "test_compound_1", 1, [], [], [], [])

        new_status_1 = Status.FAILED
        timestamp_1 = 996
        phase = PhaseManager.NO_PHASE
        description_1 = "test_failed"
        record1 = component.update_status(new_status_1, timestamp_1, phase, description_1, context)

        new_status_2 = Status.UNDER_REPAIR
        timestamp_2 = 998
        phase = PhaseManager.NO_PHASE
        description_2 = "test_repair"
        record2 = component._update_status(new_status_2, timestamp_2, phase, description_2, context)

        new_status_3 = Status.RUNNING
        timestamp_3 = 1098
        phase = PhaseManager.NO_PHASE
        description_3 = "test_running"
        record3 = component._update_status(new_status_3, timestamp_3, phase, description_3, context)

        self.assertEqual(component.status, new_status_3)
        expected_record_1 = RecordComponent(component, new_status_1, timestamp_1, phase, description_1)
        expected_record_2 = RecordComponent(component, new_status_2, timestamp_2, phase, description_2)
        expected_record_3 = RecordComponent(component, new_status_3, timestamp_3, phase, description_3)
        self.assertIn(expected_record_1, record1)
        self.assertIn(expected_record_2, record2)
        self.assertIn(expected_record_3, record3)

    def test_update_status__multiple_parents__shared_child(self):
        """
        one child is shared by two parents with and logic
        the status of the child is updated (set and propagate) to FAILED
        the status of the parents has to change too
        """

        context = Context(None, None, None)

        parent0 = Compound(1, "parent", 0, [], And(), [])
        parent1 = Compound(2, "parent", 1, [], And(), [])
        parent2 = Compound(3, "parent", 2, [], And(), [])

        shared_child = Basic(4, "shared_child", 1, [parent0, parent1, parent2], [], [], [])

        parent0.add_children_list([shared_child])
        parent1.add_children_list([shared_child])
        parent2.add_children_list([shared_child])

        shared_child._update_status(Status.FAILED, PhaseManager.NO_PHASE, 3.14, "anything", context)

        self.assertEqual(parent0.status, Status.FAILED)
        self.assertEqual(parent1.status, Status.FAILED)
        self.assertEqual(parent2.status, Status.FAILED)

    def test_update_status__multiple_parents__shared_child__extra_child(self):
        """
        one child is shared by two parents with and logic, and one extra child has only one parent (parent1)
        the status of the extra child is updated (set and propagate) to FAILED
        only the status of the parent1 has to change
        """

        context = Context(None, None, None)

        parent0 = Compound(1, "parent", 0, [], And(), [])
        parent1 = Compound(2, "parent", 1, [], And(), [])

        shared_child = Basic(3, "shared_child", 1, [parent0, parent1], [], [], [])
        child_of_parent1 = Basic(4, "child_of_parent1", 1, [parent1], [], [], [])

        parent0.add_children_list([shared_child])
        parent1.add_children_list([shared_child, child_of_parent1])

        child_of_parent1._update_status(Status.FAILED, PhaseManager.NO_PHASE, 3.14, "anything", context)

        self.assertEqual(parent0.status, Status.RUNNING)
        self.assertEqual(parent1.status, Status.FAILED)

    def test_update_status__multiple_parents__shared_children__extra_child(self):
        """
        one child is shared by two parents with and logic, and one extra child has only one parent (parent1)
        the status of the extra child is updated (set and propagate) to FAILED
        only the status of the parent1 has to change
        """

        context = Context(None, None, None)

        parent0 = Compound(1, "parent", 0, [], And(), [])
        parent1 = Compound(2, "parent", 1, [], And(), [])
        parent2 = Compound(3, "parent", 2, [], And(), [])

        shared_child0 = Basic(4, "shared_child", 0, [parent0, parent1, parent2], [], [], [])
        shared_child1 = Basic(5, "shared_child", 1, [parent0, parent1, parent2], [], [], [])
        child_of_parent1 = Basic(6, "child_of_parent1", 0, [parent1], [], [], [])

        parent0.add_children_list([shared_child0, shared_child1])
        parent1.add_children_list([shared_child0, shared_child1, child_of_parent1])
        parent2.add_children_list([shared_child0, shared_child1])

        child_of_parent1._update_status(Status.FAILED, PhaseManager.NO_PHASE, 3.14, "anything", context)
        self.assertEqual(parent0.status, Status.RUNNING)
        self.assertEqual(parent1.status, Status.FAILED)
        self.assertEqual(parent2.status, Status.RUNNING)

        shared_child0._update_status(Status.FAILED, PhaseManager.NO_PHASE, 3.14, "anything", context)
        self.assertEqual(parent0.status, Status.FAILED)
        self.assertEqual(parent1.status, Status.FAILED)
        self.assertEqual(parent2.status, Status.FAILED)


if __name__ == '__main__':
    unittest.main()
