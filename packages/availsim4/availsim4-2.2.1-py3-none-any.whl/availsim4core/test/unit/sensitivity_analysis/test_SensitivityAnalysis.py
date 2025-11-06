# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import unittest
from unittest.mock import patch

from availsim4core.src.analysis import Analysis
from availsim4core.src.context.system.architecture_entry import ArchitectureEntry
from availsim4core.src.context.system.failure import Failure, FailureType
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.failure_mode_assignments import FailureModeAssignments
from availsim4core.src.context.system.probability_law.deterministic_law import DeterministicLaw
from availsim4core.src.context.system.probability_law.exponential_law import ExponentialLaw
from availsim4core.src.context.system.system_template import SystemTemplate
from availsim4core.src.reader.xlsx import xlsx_utils
from availsim4core.src.sensitivity_analysis.sensitivity_analysis import SensitivityAnalysis
from availsim4core.src.reader.xlsx.sensitivity_analysis_reader import SensitivityAnalysisReader
from availsim4core.src.sensitivity_analysis.sensitivity_analysis import OverlappingSeedsError, SensitivityAnalysis
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier import SystemModifier
from availsim4core.src.sensitivity_analysis.system_modifier.system_modifier_combination import SystemModifierCombination
from availsim4core.src.simulation.monte_carlo import MonteCarlo


class test_SensitivityAnalysis(unittest.TestCase):

    def test_generate_analysis_list_1(self):
        SENSITIVITY_SEED_1 = 10
        SENSITIVITY_SEED_2 = 100

        # Initial simulation / Systems
        initial_simulation = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   [],
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        initial_system_template = SystemTemplate(architecture_entry_list,
                                                 failure_mode_assignment_list,
                                                 [failure_mode],
                                                 mru_list,
                                                 inspection_list,
                                                 phase_manager,
                                                 set(),
                                                 set(),
                                                 None)

        # Analysis 1 -> SENSITIVITY_SEED_1
        analysis_simulation_1 = MonteCarlo(10, 10, 2., 120, SENSITIVITY_SEED_1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   [],
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_1 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_1 = Analysis(0, analysis_system_template_1, analysis_simulation_1)

        # Analysis 2 -> SENSITIVITY_SEED_2
        analysis_simulation_2 = MonteCarlo(10, 10, 2., 120, SENSITIVITY_SEED_2, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   [],
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_2 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_2 = Analysis(1, analysis_system_template_2, analysis_simulation_2)

        expected_result = [analysis_1, analysis_2]
        sensitivity_analysis_dictionary = {'SENSITIVITY_ANALYSIS':
            {
                0: {"PARAMETER_NAME": 'SEED',
                    "VALUES": f'[{SENSITIVITY_SEED_1}, {SENSITIVITY_SEED_2}]',
                    "EXPLORATION_STRATEGY": "INNER"}
            }
        }

        with patch.object(xlsx_utils, "read", return_value=sensitivity_analysis_dictionary):
            # Making sure that the method throws OverlappingSeedsError
            sensitivity_analysis = SensitivityAnalysis(initial_simulation, initial_system_template)
            self.assertRaises(OverlappingSeedsError, sensitivity_analysis.generate_analysis_list, "fake_path")

            # Changing the number of iterations per instance
            initial_simulation.minimum_number_of_simulations = 10
            initial_simulation.maximum_number_of_simulations = 10
            sensitivity_analysis = SensitivityAnalysis(initial_simulation, initial_system_template)
            result = sensitivity_analysis.generate_analysis_list("fake_path")

        self.assertEqual(expected_result, result)

    def test_generate_analysis_list_2(self):
        SENSITIVITY_FAILURE_1 = [8.]
        SENSITIVITY_FAILURE_2 = [9.]

        # Initial simulation / Systems
        initial_simulation = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        initial_system_template = SystemTemplate(architecture_entry_list,
                                                 failure_mode_assignment_list,
                                                 [failure_mode],
                                                 mru_list,
                                                 inspection_list,
                                                 phase_manager,
                                                 set(),
                                                 set(),
                                                 None)

        # Analysis 3 -> SENSITIVITY_FAILURE_1
        analysis_simulation_3 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw(SENSITIVITY_FAILURE_1),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_3 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_3 = Analysis(0, analysis_system_template_3, analysis_simulation_3)

        # Analysis 4 -> SENSITIVITY_FAILURE_2
        analysis_simulation_4 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw(SENSITIVITY_FAILURE_2),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_4 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_4 = Analysis(1, analysis_system_template_4, analysis_simulation_4)

        expected_result = [analysis_3, analysis_4]
        sensitivity_analysis_dictionary = {'SENSITIVITY_ANALYSIS':
            {
                0: {"PARAMETER_NAME": 'FAILURE_PARAMETERS/DUMBERFAILURE',
                    "VALUES": f'[{SENSITIVITY_FAILURE_1}, {SENSITIVITY_FAILURE_2}]',
                    "EXPLORATION_STRATEGY": "OUTER"}
            }
        }

        with patch.object(xlsx_utils, "read", return_value=sensitivity_analysis_dictionary):
            sensitivity_analysis = SensitivityAnalysis(initial_simulation,
                                                       initial_system_template)
            result = sensitivity_analysis.generate_analysis_list("fake_path")

        self.assertEqual(expected_result, result)

    def test_generate_analysis_list_3(self):
        SENSITIVITY_COMPONENT_NUMBER_1 = 4
        SENSITIVITY_COMPONENT_NUMBER_2 = 5

        # Initial simulation / Systems
        initial_simulation = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        initial_system_template = SystemTemplate(architecture_entry_list,
                                                 failure_mode_assignment_list,
                                                 [failure_mode],
                                                 mru_list,
                                                 inspection_list,
                                                 phase_manager,
                                                 set(),
                                                 set(),
                                                 None)

        # Analysis 3 -> SENSITIVITY_COMPONENT_NUMBER_1
        analysis_simulation_3 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", SENSITIVITY_COMPONENT_NUMBER_1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_3 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_3 = Analysis(0, analysis_system_template_3, analysis_simulation_3)

        # Analysis 5 -> SENSITIVITY_COMPONENT_NUMBER_2
        analysis_simulation_5 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", SENSITIVITY_COMPONENT_NUMBER_2, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_5 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_5 = Analysis(1, analysis_system_template_5, analysis_simulation_5)

        expected_result = [analysis_3, analysis_5]
        sensitivity_analysis_dictionary = {'SENSITIVITY_ANALYSIS':
            {
                0: {"PARAMETER_NAME": 'COMPONENT_NUMBER/DUMBER',
                    "VALUES": f'[{SENSITIVITY_COMPONENT_NUMBER_1}, {SENSITIVITY_COMPONENT_NUMBER_2}]',
                    "EXPLORATION_STRATEGY": "OUTER"},
            }
        }

        with patch.object(xlsx_utils, "read", return_value=sensitivity_analysis_dictionary):
            sensitivity_analysis = SensitivityAnalysis(initial_simulation,
                                                       initial_system_template)
            result = sensitivity_analysis.generate_analysis_list("fake_path")

        self.assertEqual(expected_result, result)

    def test_generate_analysis_list_4(self):

        def get_system_template_and_simulation(SEED,
                                               FAILURE,
                                               COMPONENT_NUMBER,
                                               CHILDREN_LOGIC):

            initial_simulation = MonteCarlo(1, 1, 2., 120, SEED, ['SUMMARY'], 1)

            architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], CHILDREN_LOGIC, [], []),
                                       ArchitectureEntry("DUMBER", "BASIC", COMPONENT_NUMBER, [], '', [], [])]
            failure_mode = FailureMode("DUMBERFAILURE",
                                       ExponentialLaw(FAILURE),
                                       DeterministicLaw([1000]),
                                       Failure(FailureType.BLIND),
                                       "[]",
                                       None,
                                       [],
                                       None,
                                       'NEVER',
                                       []
                                       )

            failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
            mru_list = []
            inspection_list = []
            phase_manager = None

            initial_system_template = SystemTemplate(architecture_entry_list,
                                                     failure_mode_assignment_list,
                                                     [failure_mode],
                                                     mru_list,
                                                     inspection_list,
                                                     phase_manager,
                                                     set(),
                                                     set(),
                                                     None)

            return initial_system_template, initial_simulation

        def get_new_analysis(id_analysis,
                             SEED,
                             FAILURE,
                             COMPONENT_NUMBER,
                             CHILDREN_LOGIC):

            system_template, simulation = get_system_template_and_simulation(SEED,
                                                                             FAILURE,
                                                                             COMPONENT_NUMBER,
                                                                             CHILDREN_LOGIC)

            return Analysis(id_analysis, system_template, simulation)

        SEED = 1
        SENSITIVITY_SEED_1 = 10
        SENSITIVITY_SEED_2 = 100

        FAILURE = [7.]
        SENSITIVITY_FAILURE_1 = [8.]
        SENSITIVITY_FAILURE_2 = [9.]

        COMPONENT_NUMBER = 3
        SENSITIVITY_COMPONENT_NUMBER_1 = 4
        SENSITIVITY_COMPONENT_NUMBER_2 = 5

        CHILDREN_LOGIC = 'AND'
        SENSITIVITY_CHILDREN_LOGIC_1 = '1RC'
        SENSITIVITY_CHILDREN_LOGIC_2 = '1TF'

        initial_system_template, initial_simulation = get_system_template_and_simulation(SEED,
                                                                                         FAILURE,
                                                                                         COMPONENT_NUMBER,
                                                                                         CHILDREN_LOGIC)

        expected_result = [

            get_new_analysis(0,
                             SENSITIVITY_SEED_1,
                             SENSITIVITY_FAILURE_1,
                             SENSITIVITY_COMPONENT_NUMBER_1,
                             CHILDREN_LOGIC),
            get_new_analysis(1,
                             SENSITIVITY_SEED_2,
                             SENSITIVITY_FAILURE_1,
                             SENSITIVITY_COMPONENT_NUMBER_1,
                             CHILDREN_LOGIC),
            get_new_analysis(2,
                             SENSITIVITY_SEED_1,
                             SENSITIVITY_FAILURE_2,
                             SENSITIVITY_COMPONENT_NUMBER_1,
                             CHILDREN_LOGIC),
            get_new_analysis(3,
                             SENSITIVITY_SEED_2,
                             SENSITIVITY_FAILURE_2,
                             SENSITIVITY_COMPONENT_NUMBER_1,
                             CHILDREN_LOGIC),

            get_new_analysis(4,
                             SENSITIVITY_SEED_1,
                             SENSITIVITY_FAILURE_1,
                             SENSITIVITY_COMPONENT_NUMBER_2,
                             CHILDREN_LOGIC),
            get_new_analysis(5,
                             SENSITIVITY_SEED_2,
                             SENSITIVITY_FAILURE_1,
                             SENSITIVITY_COMPONENT_NUMBER_2,
                             CHILDREN_LOGIC),
            get_new_analysis(6,
                             SENSITIVITY_SEED_1,
                             SENSITIVITY_FAILURE_2,
                             SENSITIVITY_COMPONENT_NUMBER_2,
                             CHILDREN_LOGIC),
            get_new_analysis(7,
                             SENSITIVITY_SEED_2,
                             SENSITIVITY_FAILURE_2,
                             SENSITIVITY_COMPONENT_NUMBER_2,
                             CHILDREN_LOGIC),


            get_new_analysis(8,
                             SENSITIVITY_SEED_1,
                             SENSITIVITY_FAILURE_1,
                             COMPONENT_NUMBER,
                             SENSITIVITY_CHILDREN_LOGIC_1),
            get_new_analysis(9,
                             SENSITIVITY_SEED_2,
                             SENSITIVITY_FAILURE_1,
                             COMPONENT_NUMBER,
                             SENSITIVITY_CHILDREN_LOGIC_1),
            get_new_analysis(10,
                             SENSITIVITY_SEED_1,
                             SENSITIVITY_FAILURE_2,
                             COMPONENT_NUMBER,
                             SENSITIVITY_CHILDREN_LOGIC_1),
            get_new_analysis(11,
                             SENSITIVITY_SEED_2,
                             SENSITIVITY_FAILURE_2,
                             COMPONENT_NUMBER,
                             SENSITIVITY_CHILDREN_LOGIC_1),

            get_new_analysis(12,
                             SENSITIVITY_SEED_1,
                             SENSITIVITY_FAILURE_1,
                             COMPONENT_NUMBER,
                             SENSITIVITY_CHILDREN_LOGIC_2),
            get_new_analysis(13,
                             SENSITIVITY_SEED_2,
                             SENSITIVITY_FAILURE_1,
                             COMPONENT_NUMBER,
                             SENSITIVITY_CHILDREN_LOGIC_2),
            get_new_analysis(14,
                             SENSITIVITY_SEED_1,
                             SENSITIVITY_FAILURE_2,
                             COMPONENT_NUMBER,
                             SENSITIVITY_CHILDREN_LOGIC_2),
            get_new_analysis(15,
                             SENSITIVITY_SEED_2,
                             SENSITIVITY_FAILURE_2,
                             COMPONENT_NUMBER,
                             SENSITIVITY_CHILDREN_LOGIC_2)
        ]


        sensitivity_analysis_dictionary = {'SENSITIVITY_ANALYSIS':
            {
                0: {"PARAMETER_NAME": 'COMPONENT_NUMBER/DUMBER',
                    "VALUES": f'[{SENSITIVITY_COMPONENT_NUMBER_1}, {SENSITIVITY_COMPONENT_NUMBER_2}]',
                    "EXPLORATION_STRATEGY": "INNER"},
                1: {"PARAMETER_NAME": 'CHILDREN_LOGIC/DUMB',
                    "VALUES": f'[{SENSITIVITY_CHILDREN_LOGIC_1}, {SENSITIVITY_CHILDREN_LOGIC_2}]',
                    "EXPLORATION_STRATEGY": "INNER"},
                2: {"PARAMETER_NAME": 'FAILURE_PARAMETERS/DUMBERFAILURE',
                    "VALUES": f'[{SENSITIVITY_FAILURE_1}, {SENSITIVITY_FAILURE_2}]',
                    "EXPLORATION_STRATEGY": "OUTER"},
                3: {"PARAMETER_NAME": 'SEED',
                    "VALUES": f'[{SENSITIVITY_SEED_1}, {SENSITIVITY_SEED_2}]',
                    "EXPLORATION_STRATEGY": "OUTER"}
            }
        }

        with patch.object(xlsx_utils, "read", return_value=sensitivity_analysis_dictionary):
            sensitivity_analysis = SensitivityAnalysis(initial_simulation,
                                                       initial_system_template)
            result = sensitivity_analysis.generate_analysis_list("fake_path")

        self.assertEqual(expected_result, result)

    def test_generate_analysis_list_5(self):
        CHILDREN_LOGIC_1 = "3OO4"
        CHILDREN_LOGIC_2 = "2OO4"

        # Initial simulation / Systems
        initial_simulation = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 4, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        initial_system_template = SystemTemplate(architecture_entry_list,
                                                 failure_mode_assignment_list,
                                                 [failure_mode],
                                                 mru_list,
                                                 inspection_list,
                                                 phase_manager,
                                                 set(),
                                                 set(),
                                                 None)

        # Analysis 1 -> CHILDREN_LOGIC_1
        analysis_simulation_1 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], CHILDREN_LOGIC_1, [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 4, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_1 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_1 = Analysis(0, analysis_system_template_1, analysis_simulation_1)

        # Analysis 2 -> CHILDREN_LOGIC_2
        analysis_simulation_2 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], CHILDREN_LOGIC_2, [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 4, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_2 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_2 = Analysis(1, analysis_system_template_2, analysis_simulation_2)

        expected_result = [analysis_1, analysis_2]
        sensitivity_analysis_dictionary = {'SENSITIVITY_ANALYSIS':
            {
                0: {"PARAMETER_NAME": 'CHILDREN_LOGIC/DUMB',
                    "VALUES": f'[{CHILDREN_LOGIC_1}, {CHILDREN_LOGIC_2}]',
                    "EXPLORATION_STRATEGY": "INNER"}
            }
        }

        with patch.object(xlsx_utils, "read", return_value=sensitivity_analysis_dictionary):
            sensitivity_analysis = SensitivityAnalysis(initial_simulation,
                                                       initial_system_template)
            result = sensitivity_analysis.generate_analysis_list("fake_path")

        self.assertEqual(expected_result, result)

    def test_generate_analysis_list_6(self):
        CHILDREN_LOGIC_1 = "3OO4"
        CHILDREN_LOGIC_2 = "2OO4"

        # Initial simulation / Systems
        initial_simulation = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 4, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        initial_system_template = SystemTemplate(architecture_entry_list,
                                                 failure_mode_assignment_list,
                                                 [failure_mode],
                                                 mru_list,
                                                 inspection_list,
                                                 phase_manager,
                                                 set(),
                                                 set(),
                                                 None)

        # Analysis 1 -> CHILDREN_LOGIC_1
        analysis_simulation_1 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], CHILDREN_LOGIC_1, [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 4, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_1 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_1 = Analysis(0, analysis_system_template_1, analysis_simulation_1)

        # Analysis 2 -> CHILDREN_LOGIC_2
        analysis_simulation_2 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], CHILDREN_LOGIC_2, [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 4, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_2 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_2 = Analysis(1, analysis_system_template_2, analysis_simulation_2)

        expected_result = [analysis_1, analysis_2]
        sensitivity_analysis_dictionary = {'SENSITIVITY_ANALYSIS':
            {
                0: {"PARAMETER_NAME": 'CHILDREN_LOGIC/DUMB',
                    "VALUES": f'[{CHILDREN_LOGIC_1}, {CHILDREN_LOGIC_2}]',
                    "EXPLORATION_STRATEGY": "OUTER"}
            }
        }

        with patch.object(xlsx_utils, "read", return_value=sensitivity_analysis_dictionary):
            sensitivity_analysis = SensitivityAnalysis(initial_simulation,
                                                       initial_system_template)
            result = sensitivity_analysis.generate_analysis_list("fake_path")

        self.assertEqual(expected_result, result)

    def test_generate_analysis_list_7(self):
        # only outer strategy

        SENSITIVITY_FAILURE_1 = [8.]
        SENSITIVITY_FAILURE_2 = [9.]
        SENSITIVITY_COMPONENT_NUMBER_1 = 4
        SENSITIVITY_COMPONENT_NUMBER_2 = 5

        # Initial simulation / Systems
        initial_simulation = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        initial_system_template = SystemTemplate(architecture_entry_list,
                                                 failure_mode_assignment_list,
                                                 [failure_mode],
                                                 mru_list,
                                                 inspection_list,
                                                 phase_manager,
                                                 set(),
                                                 set(),
                                                 None)

        # Analysis 3 -> SENSITIVITY_COMPONENT_NUMBER_1 / SENSITIVITY_FAILURE_1
        analysis_simulation_3 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", SENSITIVITY_COMPONENT_NUMBER_1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw(SENSITIVITY_FAILURE_1),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_3 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_3 = Analysis(0, analysis_system_template_3, analysis_simulation_3)

        # Analysis 4 -> SENSITIVITY_COMPONENT_NUMBER_1 / SENSITIVITY_FAILURE_2
        analysis_simulation_4 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", SENSITIVITY_COMPONENT_NUMBER_1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw(SENSITIVITY_FAILURE_2),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_4 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_4 = Analysis(1, analysis_system_template_4, analysis_simulation_4)

        # Analysis 5 -> SENSITIVITY_COMPONENT_NUMBER_2 / SENSITIVITY_FAILURE_1
        analysis_simulation_5 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", SENSITIVITY_COMPONENT_NUMBER_2, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw(SENSITIVITY_FAILURE_1),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_5 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_5 = Analysis(2, analysis_system_template_5, analysis_simulation_5)

        # Analysis 6 -> SENSITIVITY_COMPONENT_NUMBER_2 / SENSITIVITY_FAILURE_2
        analysis_simulation_6 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", SENSITIVITY_COMPONENT_NUMBER_2, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw(SENSITIVITY_FAILURE_2),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_6 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_6 = Analysis(3, analysis_system_template_6, analysis_simulation_6)

        expected_result = [analysis_3, analysis_4, analysis_5, analysis_6]
        sensitivity_analysis_dictionary = {'SENSITIVITY_ANALYSIS':
            {
                0: {"PARAMETER_NAME": 'COMPONENT_NUMBER/DUMBER',
                    "VALUES": f'[{SENSITIVITY_COMPONENT_NUMBER_1}, {SENSITIVITY_COMPONENT_NUMBER_2}]',
                    "EXPLORATION_STRATEGY": "OUTER"},
                1: {"PARAMETER_NAME": 'FAILURE_PARAMETERS/DUMBERFAILURE',
                    "VALUES": f'[{SENSITIVITY_FAILURE_1}, {SENSITIVITY_FAILURE_2}]',
                    "EXPLORATION_STRATEGY": "OUTER"}
            }
        }

        with patch.object(xlsx_utils, "read", return_value=sensitivity_analysis_dictionary):
            sensitivity_analysis = SensitivityAnalysis(initial_simulation,
                                                       initial_system_template)
            result = sensitivity_analysis.generate_analysis_list("fake_path")

        self.assertEqual(expected_result, result)

    def test_generate_analysis_list_8(self):
        # only zip strategy
        # two elements in the sensitivity analysis

        SENSITIVITY_FAILURE_1 = [8.]
        SENSITIVITY_FAILURE_2 = [9.]
        SENSITIVITY_COMPONENT_NUMBER_1 = 4
        SENSITIVITY_COMPONENT_NUMBER_2 = 5

        # Initial simulation / Systems
        initial_simulation = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        initial_system_template = SystemTemplate(architecture_entry_list,
                                                 failure_mode_assignment_list,
                                                 [failure_mode],
                                                 mru_list,
                                                 inspection_list,
                                                 phase_manager,
                                                 set(),
                                                 set(),
                                                 None)

        # Analysis 0 -> SENSITIVITY_COMPONENT_NUMBER_1 / SENSITIVITY_FAILURE_1
        analysis_simulation_0 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", SENSITIVITY_COMPONENT_NUMBER_1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw(SENSITIVITY_FAILURE_1),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_0 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_0 = Analysis(0, analysis_system_template_0, analysis_simulation_0)

        # Analysis 1 -> SENSITIVITY_COMPONENT_NUMBER_2 / SENSITIVITY_FAILURE_2
        analysis_simulation_1 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", SENSITIVITY_COMPONENT_NUMBER_2, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw(SENSITIVITY_FAILURE_2),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_1 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_1 = Analysis(1, analysis_system_template_1, analysis_simulation_1)

        expected_result = [analysis_0, analysis_1]
        sensitivity_analysis_dictionary = {'SENSITIVITY_ANALYSIS':
            {
                0: {"PARAMETER_NAME": 'COMPONENT_NUMBER/DUMBER',
                    "VALUES": f'[{SENSITIVITY_COMPONENT_NUMBER_1}, {SENSITIVITY_COMPONENT_NUMBER_2}]',
                    "EXPLORATION_STRATEGY": "ZIP"},
                1: {"PARAMETER_NAME": 'FAILURE_PARAMETERS/DUMBERFAILURE',
                    "VALUES": f'[{SENSITIVITY_FAILURE_1}, {SENSITIVITY_FAILURE_2}]',
                    "EXPLORATION_STRATEGY": "ZIP"}
            }
        }

        with patch.object(xlsx_utils, "read", return_value=sensitivity_analysis_dictionary):
            sensitivity_analysis = SensitivityAnalysis(initial_simulation,
                                                       initial_system_template)
            result = sensitivity_analysis.generate_analysis_list("fake_path")

        self.assertEqual(expected_result, result)

    def test_generate_analysis_list_9(self):
        # only zip strategy
        # one element in the sensitivity analysis

        SENSITIVITY_FAILURE_1 = [8.]
        SENSITIVITY_COMPONENT_NUMBER_1 = 4

        # Initial simulation / Systems
        initial_simulation = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        initial_system_template = SystemTemplate(architecture_entry_list,
                                                 failure_mode_assignment_list,
                                                 [failure_mode],
                                                 mru_list,
                                                 inspection_list,
                                                 phase_manager,
                                                 set(),
                                                 set(),
                                                 None)

        # Analysis 0 -> SENSITIVITY_COMPONENT_NUMBER_1 / SENSITIVITY_FAILURE_1
        analysis_simulation_0 = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", SENSITIVITY_COMPONENT_NUMBER_1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw(SENSITIVITY_FAILURE_1),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_0 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        analysis_0 = Analysis(0, analysis_system_template_0, analysis_simulation_0)

        expected_result = [analysis_0]

        sensitivity_analysis_dictionary = {'SENSITIVITY_ANALYSIS':
            {
                0: {"PARAMETER_NAME": 'COMPONENT_NUMBER/DUMBER',
                    "VALUES": f'[{SENSITIVITY_COMPONENT_NUMBER_1}]',
                    "EXPLORATION_STRATEGY": "ZIP"},
                1: {"PARAMETER_NAME": 'FAILURE_PARAMETERS/DUMBERFAILURE',
                    "VALUES": f'[{SENSITIVITY_FAILURE_1}]',
                    "EXPLORATION_STRATEGY": "ZIP"}
            }
        }

        with patch.object(xlsx_utils, "read", return_value=sensitivity_analysis_dictionary):
            sensitivity_analysis = SensitivityAnalysis(initial_simulation,
                                                       initial_system_template)
            result = sensitivity_analysis.generate_analysis_list("fake_path")

        self.assertEqual(expected_result, result)

    def test_generate_analysis__system(self):
        SENSITIVITY_FAILURE_1 = [8.]
        SENSITIVITY_COMPONENT_NUMBER_1 = 4

        # Initial simulation / Systems
        initial_simulation = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        initial_system_template = SystemTemplate(architecture_entry_list,
                                                 failure_mode_assignment_list,
                                                 [failure_mode],
                                                 mru_list,
                                                 inspection_list,
                                                 phase_manager,
                                                 set(),
                                                 set(),
                                                 None)

        # Analysis -> SENSITIVITY_FAILURE_1 / SENSITIVITY_COMPONENT_NUMBER_1
        analysis_simulation = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", SENSITIVITY_COMPONENT_NUMBER_1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw(SENSITIVITY_FAILURE_1),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   "[]",
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        analysis_system_template_2 = SystemTemplate(architecture_entry_list,
                                                    failure_mode_assignment_list,
                                                    [failure_mode],
                                                    mru_list,
                                                    inspection_list,
                                                    phase_manager,
                                                    set(),
                                                    set(),
                                                    None)
        expected_analysis = Analysis(1, analysis_system_template_2, analysis_simulation)

        system_modifier_failure_1 = SystemModifier("FAILURE_PARAMETERS/DUMBERFAILURE", SENSITIVITY_FAILURE_1)
        system_modifier_component_number_1 = SystemModifier("COMPONENT_NUMBER/DUMBER", SENSITIVITY_COMPONENT_NUMBER_1)

        sensitivity_analysis = SensitivityAnalysis(initial_simulation,
                                                   initial_system_template)

        result_analysis = sensitivity_analysis._generate_analysis(1,
                                                                  SystemModifierCombination(
                                                                      [system_modifier_failure_1,
                                                                       system_modifier_component_number_1]))

        self.assertEqual(expected_analysis, result_analysis)

    def test_apply_combination_modifier_on_system(self):
        # Initial simulation / Systems
        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 1, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   [],
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        initial_system_template = SystemTemplate(architecture_entry_list,
                                                 failure_mode_assignment_list,
                                                 [failure_mode],
                                                 mru_list,
                                                 inspection_list,
                                                 phase_manager,
                                                 set(),
                                                 set(),
                                                 None)

        # Expected
        architecture_entry_list = [ArchitectureEntry("DUMB", "COMPOUND", 1, ['DUMBER'], "AND", [], []),
                                   ArchitectureEntry("DUMBER", "BASIC", 100, [], '', [], [])]
        failure_mode = FailureMode("DUMBERFAILURE",
                                   ExponentialLaw([1.]),
                                   DeterministicLaw([1000]),
                                   Failure(FailureType.BLIND),
                                   [],
                                   None,
                                   [],
                                   None,
                                   'NEVER',
                                   []
                                   )

        failure_mode_assignment_list = [FailureModeAssignments("DUMBER", failure_mode)]
        mru_list = []
        inspection_list = []
        phase_manager = None

        expected_result = SystemTemplate(architecture_entry_list,
                                         failure_mode_assignment_list,
                                         [failure_mode],
                                         mru_list,
                                         inspection_list,
                                         phase_manager,
                                         set(),
                                         set(),
                                         None)

        system_modifier_failure_1 = SystemModifier("COMPONENT_NUMBER/DUMBER", 100)
        system_modifier_combination = SystemModifierCombination([system_modifier_failure_1])

        sensitivity_analysis = SensitivityAnalysis(None,
                                                   initial_system_template)
        result = sensitivity_analysis._apply_combination_modifier_on_system(system_modifier_combination)

        self.assertEqual(expected_result, result)

    def test_apply_combination_modifier_on_simulation(self):
        SENSITIVITY_SEED = 100

        expected_result = MonteCarlo(1000, 1000, 2., 120, SENSITIVITY_SEED, ['SUMMARY'], 1)

        # Initial simulation / Systems
        initial_simulation = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        system_modifier_failure_1 = SystemModifier("SEED", SENSITIVITY_SEED)
        system_modifier_combination = SystemModifierCombination([system_modifier_failure_1])

        sensitivity_analysis = SensitivityAnalysis(initial_simulation,
                                                   None)
        result = sensitivity_analysis._apply_combination_modifier_on_simulation(system_modifier_combination)

        self.assertEqual(expected_result, result)

    def test_generate_analysis__simulation(self):
        SENSITIVITY_SEED_1 = 100

        # Initial simulation / Systems
        initial_simulation = MonteCarlo(1000, 1000, 2., 120, 1, ['SUMMARY'], 1)

        initial_system_template = SystemTemplate([], [], [], [], [], None, set(),set(),None)

        # Analysis -> SENSITIVITY_SEED_1
        analysis_simulation = MonteCarlo(1000, 1000, 2., 120, SENSITIVITY_SEED_1, ['SUMMARY'], 1)

        analysis_1 = Analysis(0, initial_system_template, analysis_simulation)

        system_modifier_seed = SystemModifier("SEED", SENSITIVITY_SEED_1)

        sensitivity_analysis = SensitivityAnalysis(initial_simulation,
                                                   initial_system_template)

        result_analysis_1 = sensitivity_analysis._generate_analysis(0,
                                                                    SystemModifierCombination([system_modifier_seed]))

        self.assertEqual(analysis_1, result_analysis_1)
