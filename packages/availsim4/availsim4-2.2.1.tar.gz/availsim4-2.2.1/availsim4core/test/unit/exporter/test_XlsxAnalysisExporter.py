# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for testing analysis exporter code
"""

import os
import unittest
import pathlib
import pandas as pd

from availsim4core.src.analysis import Analysis
from availsim4core.src.context.phase.phase import Phase
from availsim4core.src.context.system.architecture_entry import ArchitectureEntry
from availsim4core.src.context.system.component_tree.basic import Basic
from availsim4core.src.context.system.component_tree.status import Status
from availsim4core.src.context.system.failure import Failure, FailureType
from availsim4core.src.context.system.failure_mode import FailureMode
from availsim4core.src.context.system.failure_mode_assignments import FailureModeAssignments
from availsim4core.src.context.system.inspection import Inspection
from availsim4core.src.context.system.minimal_replaceable_unit import MinimalReplaceableUnit
from availsim4core.src.context.system.phase_jump_trigger import PhaseJumpTrigger
from availsim4core.src.context.system.probability_law.probability_law import ProbabilityLaw
from availsim4core.src.context.system.rca_trigger import RootCauseAnalysisTrigger
from availsim4core.src.context.system.system_template import SystemTemplate

from availsim4core.src.exporter.xlsx.analysis.xlsx_analysis_exporter import XLSXAnalysisExporter
from availsim4core.src.simulation.monte_carlo import MonteCarlo


class test_XlsxAnalysisExporter(unittest.TestCase):
    """
    Class testing the XLSX exporter of the analysis. This exporter should rewrite the description of the system and save
    it in the output file.
    """

    def test_regenerate_system_template(self):
        """
        Test if the exporter generates a file
        """


        inspection1 = Inspection("Inspection 1", 10, 10)
        phase1 = Phase("Phase 1", ProbabilityLaw("DeterministicLaw", [1], False), True)
        phase2 = Phase("Phase 2", ProbabilityLaw("DeterministicLaw", [1], False), False)
        architecture_entry_list = [ArchitectureEntry(component_name = "ROOT",
                                                     component_type = "BASIC",
                                                     component_number = 1,
                                                     children_name_list = [],
                                                     children_logic = "and",
                                                     in_mru_str_list = [],
                                                     trigger_mru_str_list = [])]
        failure_mode = FailureMode(name = "ROOT failure",
                                   failure_law = ProbabilityLaw("DeterministicLaw", [1], False),
                                   repair_law = ProbabilityLaw("DeterministicLaw", [1], False),
                                   failure = Failure(FailureType.BLIND),
                                   held_after_repair_phase_set=set(),
                                   held_before_repair_phase_set=set(),
                                   inspection=inspection1,
                                   phase_change_trigger="NEVER",
                                   failure_mode_next_phase_if_failure=None,
                                   phase_set=set([phase1]))
        failure_mode_assignments_list = [FailureModeAssignments(component_name = "ROOT", failure_mode = failure_mode)]
        failure_mode_list = [failure_mode]
        mru_list = [MinimalReplaceableUnit("MRU1",
                                           ProbabilityLaw("DeterministicLaw", [1], False),
                                           "",
                                           Status.FAILED,
                                           ["ROOT"])]
        inspection_list = []

        phase1 = Phase("Phase 1", ProbabilityLaw("DeterministicLaw", [1], False), True)
        phase2 = Phase("Phase 2", ProbabilityLaw("DeterministicLaw", [1], False), False)
        phase1.set_next_phase(phase2)
        phase1.set_next_phase_if_failure(phase2)
        phase2.set_next_phase(phase1)
        phase2.set_next_phase_if_failure(phase1)
        phase_set = set([phase1, phase2])

        root_cause_analysis_trigger_set = set([RootCauseAnalysisTrigger("ROOT", "BLIND_FAILED", "Phase 1")])
        phase_jump_trigger_set = set([PhaseJumpTrigger("ROOT", "BLIND_FAILED", phase1, phase2)])
        custom_children_logic_path = pathlib.Path("")
        system_template = SystemTemplate(architecture_entry_list, failure_mode_assignments_list, failure_mode_list,
                                         mru_list, inspection_list, phase_set, root_cause_analysis_trigger_set,
                                         phase_jump_trigger_set, custom_children_logic_path)

        root_component = Basic(0, "ROOT", 0, [], failure_mode, [], [])
        analysis = Analysis(0, system_template, MonteCarlo(10, 10, 2.0, 700, 10, ["SUMMARY"], 10.0))
        analysis_exporter = XLSXAnalysisExporter(root_component, analysis, "./availsim4core/test/unit/exporter/")

        exported_file = analysis_exporter.export()
        try:
            file_model = pd.read_excel("./availsim4core/test/unit/exporter/model_output_regenerate_system_template.xlsx")
            file_answer = pd.read_excel(exported_file[0])
            assert file_model.equals(file_answer)
        finally:
            os.remove(exported_file[0])
