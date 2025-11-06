# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest

from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.system.architecture_entry import ArchitectureEntry
from availsim4core.src.context.system.failure import Failure, FailureType
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.failure_mode_assignments import FailureModeAssignments
from availsim4core.src.context.system.inspection import Inspection
from availsim4core.src.context.system.minimal_replaceable_unit import MinimalReplaceableUnit

from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw
from availsim4core.src.reader.xlsx.system_template.architecture_sheet_reader import ArchitectureSheetReader
from availsim4core.src.reader.xlsx.system_template.failure_mode_assignments_sheet_reader import FailureModesAssignmentSheetReader
from availsim4core.src.reader.xlsx.system_template.failure_modes_sheet_reader import FailureModesSheetReader
from availsim4core.src.reader.xlsx.system_template.inspection_sheet_reader import InspectionSheetReader
from availsim4core.src.reader.xlsx.system_template.mru_sheet_reader import MinimalReplaceableUnitSheetReader
from availsim4core.src.reader.xlsx.system_template.sheet_reader import SheetReader


class test_SystemTemplateReader(unittest.TestCase):

    def test_generate_failure_mode_assignments(self):
        system_dictionary_assignments = {
            0: {"COMPONENT_NAME": 'ACCELERATORCONTROLS', "FAILURE_MODE_NAME": 'ACCELERATORCONTROLSFAILURE'},
            1: {"COMPONENT_NAME": 'ACCESSMANAGEMENT', "FAILURE_MODE_NAME": 'ACCESSMANAGEMENTFAILURE'}
        }

        failure_mode_1 = FailureMode("ACCELERATORCONTROLSFAILURE",
                                     ProbabilityLaw("", 0, False),
                                     ProbabilityLaw("", 0, False),
                                     Failure(FailureType.DETECTABLE),
                                     "[]",
                                     None,
                                     [],
                                     None,
                                     'AFTER_REPAIR',
                                     [])

        failure_mode_2 = FailureMode("ACCESSMANAGEMENTFAILURE",
                                     ProbabilityLaw("", 0, False),
                                     ProbabilityLaw("", 0, False),
                                     Failure(FailureType.DETECTABLE),
                                     "[]",
                                     None,
                                     [],
                                     None,
                                     'AFTER_REPAIR',
                                     [])

        failure_mode_assignment_1 = FailureModeAssignments("ACCELERATORCONTROLS", failure_mode_1)
        failure_mode_assignment_2 = FailureModeAssignments("ACCESSMANAGEMENT", failure_mode_2)

        expected_results = [failure_mode_assignment_1, failure_mode_assignment_2]

        results = FailureModesAssignmentSheetReader().generate_failure_mode_assignments(system_dictionary_assignments,
                                                                         [failure_mode_1, failure_mode_2])

        self.assertEqual(expected_results, results)

    def test_generate_failure_modes(self):
        failure_mode_dict = {
            0: {"FAILURE_MODE_NAME": 'ACCELERATORCONTROLSFAILURE',
                "FAILURE_LAW": "EXP",
                "FAILURE_PARAMETERS": "300.0",
                "REPAIR_LAW": "FIX",
                "REPAIR_PARAMETERS": "1.5436",
                "TYPE_OF_FAILURE": "DETECTABLE",
                "HELD_BEFORE_REPAIR": "HELD_FOREVER",
                "INSPECTION_NAME": 'none',
                "PHASE_NAME": 'A',
                "NEXT_PHASE_IF_FAILURE": 'B',
                "PHASE_CHANGE_TRIGGER": "AFTER_FAILURE",
                "HELD_AFTER_REPAIR":"HELD_FOREVER"},
            1: {"FAILURE_MODE_NAME": 'ACCESSMANAGEMENTFAILURE',
                "FAILURE_LAW": "EXP",
                "FAILURE_PARAMETERS": "859.74",
                "TYPE_OF_FAILURE": "DETECTABLE",
                "HELD_BEFORE_REPAIR": "HELD_FOREVER",
                "REPAIR_LAW": "FIX",
                "REPAIR_PARAMETERS": "3.6167",
                "INSPECTION_NAME": 'none',
                "PHASE_NAME": 'B',
                "NEXT_PHASE_IF_FAILURE": 'none',
                "PHASE_CHANGE_TRIGGER": "AFTER_FAILURE",
                "HELD_AFTER_REPAIR":"HELD_FOREVER"},
        }

        phase_a = Phase('A', ProbabilityLaw("FIX", 1., False), True)
        phase_b = Phase('B', ProbabilityLaw("FIX", 1., False), False)
        phase_a.set_next_phase(phase_b)
        phase_b.set_next_phase(phase_a)

        failure_mode_1 = FailureMode("ACCELERATORCONTROLSFAILURE",
                                     ProbabilityLaw("ExponentialLaw", [300.0], False),
                                     ProbabilityLaw("DeterministicLaw", [1.5436], False),
                                     Failure(FailureType.DETECTABLE),
                                     set([PhaseManager.HELD_FOREVER]),
                                     None,
                                     {phase_a},
                                     phase_b,
                                     "AFTER_FAILURE",
                                     set([PhaseManager.HELD_FOREVER]))
        failure_mode_2 = FailureMode("ACCESSMANAGEMENTFAILURE",
                                     ProbabilityLaw("ExponentialLaw", [859.74], False),
                                     ProbabilityLaw("DeterministicLaw", [3.6167], False),
                                     Failure(FailureType.DETECTABLE),
                                     set([PhaseManager.HELD_FOREVER]),
                                     None,
                                     {phase_b},
                                     None,
                                     "AFTER_FAILURE",
                                     set([PhaseManager.HELD_FOREVER]))

        expected_results = [failure_mode_1, failure_mode_2]

        results = FailureModesSheetReader().generate_failure_modes(failure_mode_dict, {}, {phase_a, phase_b})

        self.assertEqual(expected_results, results)

    def test_generate_architecture_entry_list(self):
        architecture_dict = {
            0: {"COMPONENT_NAME": 'ROOT',
                "COMPONENT_TYPE": 'COMPOUND',
                "COMPONENT_NUMBER": "1",
                "CHILDREN_NAME": 'ACCELERATORCONTROLS,ACCESSMANAGEMENT,BEAMLOSSES',
                "CHILDREN_LOGIC": "AND",
                "IN_MRU": 'none',
                "TRIGGER_MRU": 'none'},
            1: {"COMPONENT_NAME": 'ACCELERATORCONTROLS',
                "COMPONENT_TYPE": 'basic',
                "COMPONENT_NUMBER": "2",
                "CHILDREN_NAME": 'none',
                "CHILDREN_LOGIC": 'none',
                "IN_MRU": 'none',
                "TRIGGER_MRU": 'none'}
        }

        expected_architecture_entry_root = ArchitectureEntry('ROOT', "COMPOUND", 1,
                                                             ['ACCELERATORCONTROLS', 'ACCESSMANAGEMENT', 'BEAMLOSSES'],
                                                             "AND",
                                                             [], [])
        expected_architecture_entry_basic = ArchitectureEntry('ACCELERATORCONTROLS', "BASIC", 2, [], '', [], [])

        architecture_list_result = ArchitectureSheetReader().generate_architecture_entry_list(architecture_dict)

        self.assertEqual(architecture_list_result,
                         [expected_architecture_entry_root, expected_architecture_entry_basic])

    def test_generate_architecture_entry_list_with_duplicated_entries(self):
        architecture_dict = {
            0: {"COMPONENT_NAME": 'ROOT',
                "COMPONENT_TYPE": 'COMPOUND',
                "COMPONENT_NUMBER": "1",
                "CHILDREN_NAME": 'ACCELERATORCONTROLS,ACCESSMANAGEMENT,BEAMLOSSES',
                "CHILDREN_LOGIC": "AND",
                "IN_MRU": 'none',
                "TRIGGER_MRU": 'none'},
            1: {"COMPONENT_NAME": 'ACCELERATORCONTROLS',
                "COMPONENT_TYPE": 'basic',
                "COMPONENT_NUMBER": "2",
                "CHILDREN_NAME": 'none',
                "CHILDREN_LOGIC": 'none',
                "IN_MRU": 'none',
                "TRIGGER_MRU": 'none'},
            2: {"COMPONENT_NAME": 'ACCELERATORCONTROLS',
                "COMPONENT_TYPE": 'basic',
                "COMPONENT_NUMBER": "2",
                "CHILDREN_NAME": 'none',
                "CHILDREN_LOGIC": 'none',
                "IN_MRU": 'none',
                "TRIGGER_MRU": 'none'}
        }

        with self.assertRaises(SheetReader.DuplicatedEntry) as context:
            ArchitectureSheetReader().generate_architecture_entry_list(architecture_dict)

        self.assertTrue("The component name ACCELERATORCONTROLS is duplicated in the sheet ARCHITECTURE" in str(context.exception))

    def test_generate_minimal_replaceable_units(self):
        system_dictionary_minimal_replaceable_unit = {
            0: {'MRU_NAME': 'CLIQ',
                "MRU_LAW": "FIX",
                "MRU_PARAMETERS": "0.001",
                "MRU_SCHEDULE": "IMMEDIATE",
                "LOWEST_COMMON_ANCESTOR_SCOPE": 'CLIQ',
                "TRIGGERING_STATUS": 'FAILED'},
            1: {'MRU_NAME': 'SHUTDOWN',
                "MRU_LAW": "FIX",
                "MRU_PARAMETERS": "0.001",
                "MRU_SCHEDULE": "IMMEDIATE",
                "LOWEST_COMMON_ANCESTOR_SCOPE": 'ITS',
                "TRIGGERING_STATUS": 'UNDER_REPAIR'},
            2: {'MRU_NAME': 'REPAIRALL',
                "MRU_LAW": "FIX",
                "MRU_PARAMETERS": "0.675",
                "MRU_SCHEDULE": "IMMEDIATE",
                "LOWEST_COMMON_ANCESTOR_SCOPE": 'IT',
                "TRIGGERING_STATUS": 'FAILED,BLIND_FAILED'}
        }

        result =  MinimalReplaceableUnitSheetReader().generate_mrus(system_dictionary_minimal_replaceable_unit, "")

        expected_result = \
            MinimalReplaceableUnit.build("CLIQ",
                                                "FIX",
                                                [0.001],
                                                "IMMEDIATE",
                                                ["FAILED"],
                                                ["CLIQ"]) + \
            MinimalReplaceableUnit.build("SHUTDOWN",
                                                "FIX",
                                                [0.001],
                                                "IMMEDIATE",
                                                ["UNDER_REPAIR"],
                                                ["ITS"]) + \
            MinimalReplaceableUnit.build('REPAIRALL',
                                                "FIX",
                                                [0.675],
                                                "IMMEDIATE",
                                                ['FAILED', 'BLIND_FAILED'],
                                                ["IT"])

        self.assertListEqual(result, expected_result)

    def test_generate_minimal_replaceable_units_with_multiple_lca(self):
        system_dictionary_minimal_replaceable_unit = {
            0: {'MRU_NAME': 'CLIQ',
                "MRU_LAW": "FIX",
                "MRU_PARAMETERS": 0.001,
                "MRU_SCHEDULE": "IMMEDIATE",
                "LOWEST_COMMON_ANCESTOR_SCOPE": '[CLIQ,QH]',
                "TRIGGERING_STATUS": 'FAILED'},
            1: {'MRU_NAME': 'SHUTDOWN',
                "MRU_LAW": "FIX",
                "MRU_PARAMETERS": 0.001,
                "MRU_SCHEDULE": "IMMEDIATE",
                "LOWEST_COMMON_ANCESTOR_SCOPE": 'ITS',
                "TRIGGERING_STATUS": 'UNDER_REPAIR'},
            2: {'MRU_NAME': 'REPAIRALL',
                "MRU_LAW": "FIX",
                "MRU_PARAMETERS": 0.675,
                "MRU_SCHEDULE": "IMMEDIATE",
                "LOWEST_COMMON_ANCESTOR_SCOPE": '[IT1,IT2]',
                "TRIGGERING_STATUS": 'FAILED,BLIND_FAILED'}
        }

        result = MinimalReplaceableUnitSheetReader().generate_mrus(system_dictionary_minimal_replaceable_unit, "")

        expected_result = \
            MinimalReplaceableUnit.build("CLIQ",
                                                "FIX",
                                                [0.001],
                                                "IMMEDIATE",
                                                ["FAILED"],
                                                ["CLIQ","QH"]) + \
            MinimalReplaceableUnit.build("SHUTDOWN",
                                                "FIX",
                                                [0.001],
                                                "IMMEDIATE",
                                                ["UNDER_REPAIR"],
                                                ["ITS"]) + \
            MinimalReplaceableUnit.build('REPAIRALL',
                                                "FIX",
                                                [0.675],
                                                "IMMEDIATE",
                                                ['FAILED', 'BLIND_FAILED'],
                                                ["IT1","IT2"])

        self.assertListEqual(result, expected_result)

    def test_generate_inspections(self):
        system_dictionary_inspections = \
            {
                0: {"INSPECTION_NAME": 'ITINSPECTION',
                    "INSPECTION_PERIOD": "4.999",
                    "INSPECTION_DURATION": "0.001"}
            }

        result = InspectionSheetReader().generate_inspections(system_dictionary_inspections)

        expected_result = [
            Inspection("ITINSPECTION",
                       4.999,
                       0.001)
        ]

        self.assertListEqual(result, expected_result)
