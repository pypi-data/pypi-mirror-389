# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import copy
import unittest

from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.architecture_entry import ArchitectureEntry
from availsim4core.src.context.system.children_logic.and_ import And
from availsim4core.src.context.system.children_logic.children_logic import ChildrenLogic
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.component_factory import ComponentFactory
from availsim4core.src.context.system.component_tree.compound import Compound
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.failure import Failure, FailureType
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.failure_mode_assignments import FailureModeAssignments
from availsim4core.src.context.system.inspection import Inspection
from availsim4core.src.context.system.minimal_replaceable_unit import MinimalReplaceableUnit
from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw
from availsim4core.src.context.system import sanity_check
from availsim4core.src.context.system.system_template import SystemTemplate
from availsim4core.src.reader.xlsx.system_template.architecture_sheet_reader import ArchitectureSheetReader
from availsim4core.src.reader.xlsx.system_template.failure_mode_assignments_sheet_reader import FailureModesAssignmentSheetReader
from availsim4core.src.reader.xlsx.system_template.failure_modes_sheet_reader import FailureModesSheetReader
from availsim4core.src.reader.xlsx.system_template.inspection_sheet_reader import InspectionSheetReader
from availsim4core.src.reader.xlsx.system_template.mru_sheet_reader import MinimalReplaceableUnitSheetReader
from availsim4core.src.reader.xlsx.system_template.phases_sheet_reader import PhasesSheetReader
from availsim4core.src.reader.xlsx.system_template_reader import SystemTemplateSheet, SystemTemplateReader


class test_ComponentFactory(unittest.TestCase):

    def test_build(self):
        root_name = "ROOT_NODE"
        basic_name = "test"
        expected_mru = MinimalReplaceableUnit("test_mru",
                                              ProbabilityLaw("", 0, False),
                                              "IMMEDIATE",
                                              Status.FAILED,
                                              root_name)

        NO_PHASE = PhaseManager.NO_PHASE

        expected_inspection = Inspection("inspection_test", 1, 2)

        failure_mode_1 = FailureMode("TEST_FAILURE",
                                     ProbabilityLaw("", 0, False),
                                     ProbabilityLaw("", 0, False),
                                     Failure(FailureType.DETECTABLE),
                                     {NO_PHASE},
                                     expected_inspection,
                                     {NO_PHASE},
                                     NO_PHASE,
                                     'AFTER_REPAIR',
                                     {NO_PHASE})

        failure_mode_assignment_1 = FailureModeAssignments(basic_name, failure_mode_1)
        expected_root_node = Compound(1, root_name, 0, [], And(), [])
        expected_basic_1 = Basic(2,
                                 basic_name,
                                 0,
                                 [expected_root_node],
                                 failure_mode_1,
                                 [expected_mru],
                                 [expected_mru])

        architecture_entry_root = ArchitectureEntry(root_name, "COMPOUND", 1, [basic_name], "AND", [], [])
        architecture_entry_basic = ArchitectureEntry(basic_name,
                                                     "BASIC", 1, [], "",
                                                     ["test_mru"], ["test_mru"])
        system_template = SystemTemplate([architecture_entry_root, architecture_entry_basic],
                                         [failure_mode_assignment_1],
                                         [failure_mode_1],
                                         [expected_mru],
                                         [expected_inspection],
                                         {NO_PHASE},
                                         set(),
                                         set(),
                                         None)

        result_root_node = ComponentFactory(system_template).build()

        self.assertEqual(result_root_node, expected_root_node)
        result_basic = result_root_node._children[0]
        self.assertEqual(result_basic, expected_basic_1)
        self.assertEqual(result_basic.failure_mode, expected_basic_1.failure_mode)
        self.assertEqual(result_basic.list_of_mru_trigger, expected_basic_1.list_of_mru_trigger)
        self.assertEqual(result_basic.list_of_mru_group, expected_basic_1.list_of_mru_group)

    def test_add_component(self):

        failure_mode_1 = FailureMode("ACCELERATOR_CONTROLS_FAILURE",
                                     ProbabilityLaw("", 0, False),
                                     ProbabilityLaw("", 0, False),
                                     Failure(FailureType.DETECTABLE),
                                     "[]",
                                     None,
                                     [],
                                     None,
                                     'AFTER_REPAIR',
                                     [])

        failure_mode_assignment_1 = FailureModeAssignments("ACCELERATOR_CONTROLS", [failure_mode_1])

        component_name: str = "ACCELERATOR_CONTROLS"

        architecture_entry_root = ArchitectureEntry("ROOT_NODE", "COMPOUND", 1, [component_name], "AND", [], [])
        architecture_entry_basic = ArchitectureEntry(component_name, "BASIC", 1, [], "", [], [])
        system_template = SystemTemplate([architecture_entry_root, architecture_entry_basic],
                                         [failure_mode_assignment_1],
                                         [failure_mode_1],
                                         [],
                                         [],
                                         None,
                                         set(),
                                         set(),
                                         None)

        component_factory = ComponentFactory(system_template)

        result_list = component_factory._add_component(architecture_entry_root, [], None)

        expected_result = Compound(1, "LINAC4", 0, [], And(), [])
        expected_basic = Basic(2, "ACCELERATOR_CONTROLS", 0, [expected_result], failure_mode_1, [], [])
        expected_result.add_children_list([expected_basic])
        expected_result_list = [expected_result]

        for result in result_list:
            for expected_result in expected_result_list:
                self.assertEqual(result, expected_result)
                self.assertEqual(result._children, expected_result._children)

    def test_add_basics(self):

        parents = [Compound(0, "ROOT_NODE", 0, [], ChildrenLogic(), [])]

        failure_mode_1 = FailureMode("ACCELERATOR_CONTROLS_FAILURE",
                                     ProbabilityLaw("", 0, False),
                                     ProbabilityLaw("", 0, False),
                                     Failure(FailureType.DETECTABLE),
                                     "[]",
                                     None,
                                     [],
                                     None,
                                     'AFTER_REPAIR',
                                     [])
        failure_mode_assignment_1 = FailureModeAssignments("test", [failure_mode_1])

        expected_basic_1 = Basic(1, "test", 0, parents, failure_mode_1, [], [])
        expected_basic_2 = Basic(2, "test", 1, parents, failure_mode_1, [], [])
        expected_results = [expected_basic_1, expected_basic_2]

        architecture_entry_root = ArchitectureEntry("ROOT_NODE", "COMPOUND", 1, ["test"], "", [], [])
        architecture_entry_basic = ArchitectureEntry("test", "BASIC", 2, [], "", [], [])

        system_template = SystemTemplate([architecture_entry_root, architecture_entry_basic],
                                         [failure_mode_assignment_1],
                                         [failure_mode_1],
                                         [],
                                         [],
                                         None,
                                         set(),
                                         set(),
                                         None)
        component_factory = ComponentFactory(system_template)

        result_basic_list = component_factory._add_basics(architecture_entry_basic,
                                                          parents)

        self.assertListEqual(expected_results, result_basic_list)

    def test_add_compound(self):
        failure_mode_1 = FailureMode("ACCELERATOR_CONTROLS_FAILURE",
                                     ProbabilityLaw("", 0, False),
                                     ProbabilityLaw("", 0, False),
                                     Failure(FailureType.DETECTABLE),
                                     "[]",
                                     None,
                                     [],
                                     None,
                                     'AFTER_REPAIR',
                                     [])

        failure_mode_assignment_1 = FailureModeAssignments("ACCELERATOR_CONTROLS", [failure_mode_1])

        architecture_entry_root = ArchitectureEntry("LINAC4", "COMPOUND", 1, ["ACCELERATOR_CONTROLS"], "AND", [], [])
        architecture_entry_basic = ArchitectureEntry("ACCELERATOR_CONTROLS", "BASIC", 1, [], "", [], [])

        system_template = SystemTemplate([architecture_entry_root, architecture_entry_basic],
                                         [failure_mode_assignment_1],
                                         [failure_mode_1],
                                         [],
                                         [],
                                         None,
                                         set(),
                                         set(),
                                         None)
        component_factory = ComponentFactory(system_template)

        result_list = component_factory._add_compound(architecture_entry_root, [], None)

        expected_result = Compound(1, "LINAC4", 0, [], And(), [])
        expected_basic = Basic(2, "ACCELERATOR_CONTROLS", 0, [expected_result], failure_mode_1, [], [])
        expected_result.add_children_list([expected_basic])
        expected_result_list = [expected_result]

        for result in result_list:
            for expected_result in expected_result_list:
                self.assertEqual(result, expected_result)
                self.assertTrue(result, expected_result)

    def test_add_shared_children_compound(self):

        failure_mode_1 = FailureMode("test_shared_childFailure",
                                     ProbabilityLaw("", 0, False),
                                     ProbabilityLaw("", 0, False),
                                     Failure(FailureType.DETECTABLE),
                                     "[]",
                                     None,
                                     [],
                                     None,
                                     'AFTER_REPAIR',
                                     [])

        failure_mode_assignment_1 = FailureModeAssignments("test_shared_child", [failure_mode_1])

        architecture_entry_root = ArchitectureEntry("LINAC4", "COMPOUND", 1, ["test_compound_1", "test_compound_2"],
                                                    "AND", [], [])
        architecture_entry_compound_1 = ArchitectureEntry("test_compound_1", "COMPOUND", 1,
                                                          ["test_shared_child(LINAC4)"], "AND", [], [])
        architecture_entry_compound_2 = ArchitectureEntry("test_compound_2", "COMPOUND", 1,
                                                          ["test_shared_child(LINAC4)"], "AND", [], [])
        architecture_entry_basic = ArchitectureEntry("test_shared_child", "BASIC", 1, [], "", [], [])

        architecture_entry_list = [architecture_entry_root, architecture_entry_compound_1,
                                   architecture_entry_compound_2,
                                   architecture_entry_basic]

        system_template = SystemTemplate(architecture_entry_list,
                                         [failure_mode_assignment_1],
                                         [failure_mode_1],
                                         [],
                                         [],
                                         None,
                                         set(),
                                         set(),
                                         None)
        component_factory = ComponentFactory(system_template)

        result_list = component_factory._add_compound(architecture_entry_root, [], None)

        expected_root_node = Compound(1, "LINAC4", 0, [], And(), [])
        expected_result_compound_1 = Compound(2, "test_compound_1", 0, [expected_root_node], And(), [])
        expected_result_compound_2 = Compound(3, "test_compound_2", 0, [expected_root_node], And(), [])
        expected_result_basic = Basic(4, "test_shared_child", 0,
                                      [expected_result_compound_1, expected_result_compound_2],
                                      [failure_mode_1], [], [])
        expected_result_compound_1.add_children_list([expected_result_basic])
        expected_result_compound_2.add_children_list([expected_result_basic])
        expected_root_node.add_children_list([expected_result_compound_1, expected_result_compound_2])

        expected_result_list = [expected_root_node]

        for result in result_list:
            for expected_result in expected_result_list:
                # TODO since we test only the uniq id, the full tree is not tested here as it should
                self.assertEqual(result, expected_result)

    def test_add_shared_children_compound__multiple_shared_children(self):

        failure_mode_1 = FailureMode("test_shared_childFailure",
                                     ProbabilityLaw("", 0, False),
                                     ProbabilityLaw("", 0, False),
                                     Failure(FailureType.DETECTABLE),
                                     "[]",
                                     None,
                                     [],
                                     None,
                                     'AFTER_REPAIR',
                                     [])

        failure_mode_assignment_1 = FailureModeAssignments("test_shared_child_1", [failure_mode_1])
        failure_mode_assignment_2 = FailureModeAssignments("test_shared_child_2", [failure_mode_1])

        architecture_entry_root = ArchitectureEntry("LINAC4", "COMPOUND", 1, ["test_compound_1", "test_compound_2"],
                                                    "AND", [], [])
        architecture_entry_compound_1 = ArchitectureEntry("test_compound_1", "COMPOUND", 1,
                                                          ["test_shared_child_1(LINAC4)",
                                                           "test_shared_child_2(LINAC4)"],
                                                          "AND", [], [])
        architecture_entry_compound_2 = ArchitectureEntry("test_compound_2", "COMPOUND", 1,
                                                          ["test_shared_child_1(LINAC4)",
                                                           "test_shared_child_2(LINAC4)"],
                                                          "AND", [], [])
        architecture_entry_shared_basic_1 = ArchitectureEntry("test_shared_child_1", "BASIC", 1, [], "", [], [])
        architecture_entry_shared_basic_2 = ArchitectureEntry("test_shared_child_2", "BASIC", 1, [], "", [], [])

        architecture_entry_list = [architecture_entry_root,
                                   architecture_entry_compound_1, architecture_entry_compound_2,
                                   architecture_entry_shared_basic_1, architecture_entry_shared_basic_2]

        system_template = SystemTemplate(architecture_entry_list,
                                         [failure_mode_assignment_1, failure_mode_assignment_2],
                                         [failure_mode_1],
                                         [],
                                         [],
                                         None,
                                         set(),
                                         set(),
                                         None)
        component_factory = ComponentFactory(system_template)

        result_list = component_factory._add_compound(architecture_entry_root, [], None)

        expected_root_node = Compound(1, "LINAC4", 0, [], And(), [])
        expected_result_compound_1 = Compound(2, "test_compound_1", 0, [expected_root_node], And(), [])
        expected_result_compound_2 = Compound(5, "test_compound_2", 0, [expected_root_node], And(), [])
        expected_result_shared_basic_1 = Basic(3, "test_shared_child_1", 0,
                                               [expected_result_compound_1, expected_result_compound_2],
                                               [failure_mode_1], [], [])
        expected_result_shared_basic_2 = Basic(4, "test_shared_child_2", 0,
                                               [expected_result_compound_1, expected_result_compound_2],
                                               [failure_mode_1], [], [])

        result_root = result_list[0]
        self.assertEqual(result_root, expected_root_node)
        for root_child in result_root._children:
            self.assertEqual(root_child._children, [expected_result_shared_basic_1, expected_result_shared_basic_2])

    def test_add_shared_children_compound__many_instances_of_shared_children(self):

        failure_mode_1 = FailureMode("test_shared_childFailure",
                                     ProbabilityLaw("", 0, False),
                                     ProbabilityLaw("", 0, False),
                                     Failure(FailureType.DETECTABLE),
                                     "[]",
                                     None,
                                     [],
                                     None,
                                     'AFTER_REPAIR',
                                     [])

        failure_mode_assignment_1 = FailureModeAssignments("test_shared_child_1", [failure_mode_1])

        architecture_entry_root = ArchitectureEntry("LINAC4", "COMPOUND", 1, ["test_compound_1", "test_compound_2"],
                                                    "AND", [], [])
        architecture_entry_compound_1 = ArchitectureEntry("test_compound_1", "COMPOUND", 1,
                                                          ["test_shared_child_1(LINAC4)"],
                                                          "AND", [], [])
        architecture_entry_compound_2 = ArchitectureEntry("test_compound_2", "COMPOUND", 1,
                                                          ["test_shared_child_1(LINAC4)"],
                                                          "AND", [], [])
        architecture_entry_shared_basic_1 = ArchitectureEntry("test_shared_child_1", "BASIC", 3, [], "", [], [])

        architecture_entry_list = [architecture_entry_root,
                                   architecture_entry_compound_1, architecture_entry_compound_2,
                                   architecture_entry_shared_basic_1]

        system_template = SystemTemplate(architecture_entry_list,
                                         [failure_mode_assignment_1],
                                         [failure_mode_1],
                                         [],
                                         [],
                                         None,
                                         set(),
                                         set(),
                                         None)
        component_factory = ComponentFactory(system_template)

        result_list = component_factory._add_compound(architecture_entry_root, [], None)

        expected_root_node = Compound(1, "LINAC4", 0, [], And(), [])
        expected_result_compound_1 = Compound(2, "test_compound_1", 0, [expected_root_node], And(), [])
        expected_result_compound_2 = Compound(6, "test_compound_2", 0, [expected_root_node], And(), [])
        expected_result_shared_basic_1 = Basic(3, "test_shared_child_1", 0,
                                               [expected_result_compound_1, expected_result_compound_2],
                                               [failure_mode_1], [], [])
        expected_result_shared_basic_2 = Basic(4, "test_shared_child_1", 0,
                                               [expected_result_compound_1, expected_result_compound_2],
                                               [failure_mode_1], [], [])
        expected_result_shared_basic_3 = Basic(5, "test_shared_child_1", 0,
                                               [expected_result_compound_1, expected_result_compound_2],
                                               [failure_mode_1], [], [])

        result_root = result_list[0]
        self.assertEqual(result_root, expected_root_node)
        for root_child in result_root._children:
            self.assertEqual(root_child._children, [expected_result_shared_basic_1,
                                                    expected_result_shared_basic_2,
                                                    expected_result_shared_basic_3])

    def test_find_shared_children(self):
        root_node = Compound(1, "ROOT_NODE", 0, [], ChildrenLogic(), [])
        parent_1 = Compound(2, "A", 1, [root_node], ChildrenLogic(), [])
        shared_child_compound = Compound(3, "C", 3, [parent_1], ChildrenLogic(), [])
        parent_2 = Compound(4, "B", 2, [root_node], ChildrenLogic(), [])

        shared_child_name_str = "C(ROOT_NODE)"
        shared_children_list = [shared_child_compound]

        result = ComponentFactory.find_shared_children(parent_2,
                                                       shared_child_name_str,
                                                       shared_children_list)
        self.assertEqual([shared_child_compound], result)

    def test_find_shared_children__multiple_shared_children(self):
        root_node = Compound(1, "ROOT_NODE", 0, [], ChildrenLogic(), [])
        parent_1 = Compound(2, "A", 1, [root_node], ChildrenLogic(), [])
        shared_child_compound0 = Compound(3, "C", 0, [parent_1], ChildrenLogic(), [])
        shared_child_compound1 = Compound(4, "C", 1, [parent_1], ChildrenLogic(), [])
        parent_2 = Compound(5, "B", 2, [root_node], ChildrenLogic(), [])

        shared_child_name_str = "C(ROOT_NODE)"
        shared_children_list = [shared_child_compound0, shared_child_compound1]

        result = ComponentFactory.find_shared_children(parent_2,
                                                       shared_child_name_str,
                                                       shared_children_list)
        self.assertEqual(result, [shared_child_compound0, shared_child_compound1])

    def test_compare_and_log_diff__lists_matching(self):

        list_one = ['A','A','A','A','B','C']
        list_two = ['A','B','C']

        matching = sanity_check._compare_and_log_diff(list_one, list_two, "test")

        self.assertEqual(matching,True)

    def test_compare_and_log_diff__lists_not_matching_v1(self):

        list_one = ['A','A','A','A','B','C']
        list_two = ['A','B','C','D']

        matching = sanity_check._compare_and_log_diff(list_one, list_two, "test")

        self.assertEqual(matching,False)


    def test_compare_and_log_diff__lists_not_matching_v2(self):
        list_one = ['A', 'A', 'A', 'A', 'B', 'C','D']
        list_two = ['A', 'B', 'C']

        matching = sanity_check._compare_and_log_diff(list_one, list_two, "test")

        self.assertEqual(matching,False)


    def test_sanity_check_of_the_tree(self):

        # defining a dictionary similar to a reader output

        default_dictionary = {
            "ARCHITECTURE":{
                0: {"COMPONENT_NAME": 'ROOT',
                    "COMPONENT_TYPE": 'COMPOUND',
                    "COMPONENT_NUMBER": "1",
                    "CHILDREN_NAME": 'ACCELERATORCONTROLS,ACCESSMANAGEMENT',####,BEAMLOSSES',
                    "CHILDREN_LOGIC": "AND",
                    "IN_MRU": 'none',
                    "TRIGGER_MRU": 'none'},
                1: {"COMPONENT_NAME": 'ACCELERATORCONTROLS',
                    "COMPONENT_TYPE": 'basic',
                    "COMPONENT_NUMBER": "2",
                    "CHILDREN_NAME": 'none',
                    "CHILDREN_LOGIC": 'none',
                    "IN_MRU": 'LHC_MRU',
                    "TRIGGER_MRU": 'none'},
                2: {"COMPONENT_NAME": 'ACCESSMANAGEMENT',
                    "COMPONENT_TYPE": 'basic',
                    "COMPONENT_NUMBER": "1",
                    "CHILDREN_NAME": 'none',
                    "CHILDREN_LOGIC": 'none',
                    "IN_MRU": 'none',
                    "TRIGGER_MRU": 'LHC_MRU'}
            },
            "FAILURE_MODE_ASSIGNMENTS": {
                0: {"COMPONENT_NAME": 'ACCELERATORCONTROLS', "FAILURE_MODE_NAME": 'ACCELERATORCONTROLSFAILURE'},
                1: {"COMPONENT_NAME": 'ACCESSMANAGEMENT', "FAILURE_MODE_NAME": 'ACCESSMANAGEMENTFAILURE'}
            },
            "FAILURE_MODES": {
                0: {"FAILURE_MODE_NAME": 'ACCELERATORCONTROLSFAILURE',
                    "FAILURE_LAW": "EXP",
                    "FAILURE_PARAMETERS": "300.0",
                    "REPAIR_LAW": "FIX",
                    "REPAIR_PARAMETERS": "1.5436",
                    "TYPE_OF_FAILURE": "DETECTABLE",
                    "HELD_BEFORE_REPAIR": "NEVER_HELD",
                    "INSPECTION_NAME": 'none',
                    "PHASE_NAME": 'OPERATION',
                    "NEXT_PHASE_IF_FAILURE": 'OPERATION',
                    "PHASE_CHANGE_TRIGGER": "AFTER_FAILURE",
                    "HELD_AFTER_REPAIR":"NEVER_HELD"},
                1: {"FAILURE_MODE_NAME": 'ACCESSMANAGEMENTFAILURE',
                    "FAILURE_LAW": "EXP",
                    "FAILURE_PARAMETERS": "859.74",
                    "TYPE_OF_FAILURE": "DETECTABLE",
                    "HELD_BEFORE_REPAIR": "NEVER_HELD",
                    "REPAIR_LAW": "FIX",
                    "REPAIR_PARAMETERS": "3.6167",
                    "INSPECTION_NAME": 'INSPECT',
                    "PHASE_NAME": 'OPERATION',
                    "NEXT_PHASE_IF_FAILURE": 'none',
                    "PHASE_CHANGE_TRIGGER": "AFTER_FAILURE",
                    "HELD_AFTER_REPAIR":"NEVER_HELD"},
            },
            "MRU":{
                0: {'MRU_NAME': 'LHC_MRU',
                    "MRU_LAW": "FIX",
                    "MRU_PARAMETERS": "0.001",
                    "MRU_SCHEDULE": "IMMEDIATE",
                    "LOWEST_COMMON_ANCESTOR_SCOPE": 'ROOT',
                    "TRIGGERING_STATUS": 'FAILED'}
            },
            "INSPECTIONS":{
                0: {"INSPECTION_NAME": 'INSPECT',
                    "INSPECTION_PERIOD":"5",
                    "INSPECTION_DURATION": "2"}
            },
            "PHASES":{
                0: {"PHASE_NAME": 'OPERATION',
                    "PHASE_LAW": 'FIX',
                    "PHASE_PARAMETERS": "1",
                    "FIRST_PHASE":"True",
                    "NEXT_DEFAULT_PHASE":'OPERATION',
                    "NEXT_DEFAULT_PHASE_IF_FAILURE":'OPERATION'
                    }
            }
        }

        def comparing_a_dictionary_to_its_tree(system_dictionary):

            # creating a system template

            architecture_entry_list = ArchitectureSheetReader().generate_architecture_entry_list(
                system_dictionary[SystemTemplateSheet.ARCHITECTURE])

            mru_list = MinimalReplaceableUnitSheetReader().generate_mrus(
                system_dictionary[SystemTemplateSheet.MINIMAL_REPLACEABLE_UNIT], "")

            inspections_list = InspectionSheetReader().generate_inspections(
                system_dictionary[SystemTemplateSheet.INSPECTIONS])

            phases_list = PhasesSheetReader().generate_phases(
                system_dictionary[SystemTemplateSheet.PHASES])

            failure_modes_list = FailureModesSheetReader().generate_failure_modes(
                system_dictionary[SystemTemplateSheet.FAILURE_MODES],
                inspections_list,
                phases_list)

            failure_mode_assignments_list = FailureModesAssignmentSheetReader().generate_failure_mode_assignments(
                system_dictionary[SystemTemplateSheet.FAILURE_MODE_ASSIGNMENTS],
                failure_modes_list)

            system_template = SystemTemplate(architecture_entry_list,
                                             failure_mode_assignments_list,
                                             failure_modes_list,
                                             mru_list,
                                             inspections_list,
                                             phases_list,
                                             set(),
                                             set(),
                                             None)

            # building a system

            component_factory = ComponentFactory(system_template)
            component_list = component_factory._add_component(system_template.architecture_entry_list[0], [], None)

            matching = sanity_check.run(system_template, component_list[0])

            return matching

        matching = comparing_a_dictionary_to_its_tree(default_dictionary)
        self.assertTrue(matching)

        # modifying some entries but still matching dictionary and tree

        modified_dictionary = copy.deepcopy(default_dictionary)
        modified_dictionary['ARCHITECTURE'][0]["COMPONENT_NAME"]="root"
        matching = comparing_a_dictionary_to_its_tree(modified_dictionary)
        self.assertTrue(matching)

        modified_dictionary = copy.deepcopy(default_dictionary)
        modified_dictionary['ARCHITECTURE'][0]["CHILDREN_LOGIC"] = "and"
        matching = comparing_a_dictionary_to_its_tree(modified_dictionary)
        self.assertTrue(matching)

        modified_dictionary = copy.deepcopy(default_dictionary)
        modified_dictionary['ARCHITECTURE'][0]["CHILDREN_LOGIC"] = " and "
        matching = comparing_a_dictionary_to_its_tree(modified_dictionary)
        self.assertTrue(matching)

        modified_dictionary = copy.deepcopy(default_dictionary)
        modified_dictionary['FAILURE_MODES'][0]["FAILURE_MODE_NAME"]='AccELERATORCONTROLSFAILURE'
        matching = comparing_a_dictionary_to_its_tree(modified_dictionary)
        self.assertTrue(matching)

        modified_dictionary = copy.deepcopy(default_dictionary)
        modified_dictionary['FAILURE_MODES'][0]["FAILURE_MODE_NAME"]=' ACCELERATORCONTROLSFAILURE'
        matching = comparing_a_dictionary_to_its_tree(modified_dictionary)
        self.assertTrue(matching)

        modified_dictionary = copy.deepcopy(default_dictionary)
        modified_dictionary['ARCHITECTURE'][1]["COMPONENT_NUMBER"] = ' 2'
        matching = comparing_a_dictionary_to_its_tree(modified_dictionary)
        self.assertTrue(matching)

        modified_dictionary = copy.deepcopy(default_dictionary)
        modified_dictionary['ARCHITECTURE'][1]["COMPONENT_NUMBER"] = "2 "
        matching = comparing_a_dictionary_to_its_tree(modified_dictionary)
        self.assertTrue(matching)

        # modifying some entries, dictionary and tree don't match

        modified_dictionary = copy.deepcopy(default_dictionary)
        modified_dictionary['ARCHITECTURE'][3] = \
            {"COMPONENT_NAME": 'DUMMY_COMPONENT_NOT_USED',
             "COMPONENT_TYPE": 'basic',
             "COMPONENT_NUMBER": "1",
             "CHILDREN_NAME": 'none',
             "CHILDREN_LOGIC": 'none',
             "IN_MRU": 'none',
             "TRIGGER_MRU": 'LHC_MRU'}
        matching = comparing_a_dictionary_to_its_tree(modified_dictionary)
        self.assertFalse(matching)

        modified_dictionary = copy.deepcopy(default_dictionary)
        modified_dictionary['FAILURE_MODE_ASSIGNMENTS'] = {
            0: {"COMPONENT_NAME": 'ACCELERATORCONTROLS', "FAILURE_MODE_NAME": 'ACCELERATORCONTROLSFAILURE'}
        }
        matching = comparing_a_dictionary_to_its_tree(modified_dictionary)
        self.assertFalse(matching)

        # modifying some entries, dictionary and tree don't match explicitly but still the test is passed
        # the phase added "DOWNTIME" is defined but never explicitly used in the input file, still it's present in the
        # tree because of the never_held option which uses every phases described

        modified_dictionary = copy.deepcopy(default_dictionary)
        modified_dictionary['PHASES'][1] = \
            {"PHASE_NAME": 'DOWNTIME',
             "PHASE_LAW": 'FIX',
             "PHASE_PARAMETERS": "1",
             "FIRST_PHASE": "False",
             "NEXT_DEFAULT_PHASE": 'OPERATION',
             "NEXT_DEFAULT_PHASE_IF_FAILURE": 'OPERATION'
             }
        matching = comparing_a_dictionary_to_its_tree(modified_dictionary)
        self.assertTrue(matching)
