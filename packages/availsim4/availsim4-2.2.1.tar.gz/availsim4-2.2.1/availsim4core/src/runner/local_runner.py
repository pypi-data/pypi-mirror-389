# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import logging
from datetime import datetime
import pathlib

from availsim4core.src.analysis import Analysis
from availsim4core.src.context.context import Context
from availsim4core.src.context.phase.phase_manager import PhaseManager
from availsim4core.src.context.rca.rca_manager import RootCauseAnalysisManager
from availsim4core.src.context.system.component_tree.component_factory import ComponentFactory
from availsim4core.src.exporter import ExportManager


class LocalRunner:
    """
    class used to run simulation on the local machine (where the code is called)
    """

    @staticmethod
    def run(output_folder: pathlib.Path, analysis: Analysis):
        start_time = datetime.now()
        logging.info("Starting Analysis %d", analysis.id)

        component_factory = ComponentFactory(analysis.system_template)
        root_component = component_factory.build()

        rca_manager = None
        if analysis.system_template.root_cause_analysis_trigger_set:
            rca_manager = RootCauseAnalysisManager(analysis.system_template.root_cause_analysis_trigger_set,
                                                   root_component.to_set())


        # run a simulation on a given system
        context = Context(root_component,
                          PhaseManager(analysis.system_template.phase_set,
                                       analysis.system_template.phase_jump_trigger_set),
                          rca_manager)
        exporter = ExportManager(context.root_component, analysis, output_folder)

        logging.debug("Simulation: %s", str(analysis.simulation))
        logging.info("System tree: \n%s", str(root_component))
        logging.debug("PhaseManager: %s", str(context.phase_manager))

        completed_iterations = 0
        while completed_iterations < analysis.simulation.maximum_number_of_simulations:
            simulation_results = analysis.simulation.run(context)
            completed_iterations = simulation_results.maximum_number_of_simulations
            execution_time = (datetime.now() - start_time).total_seconds()
            logging.info("Analysis execution time = %.2f s", execution_time)

            # export results
            exporter.export(simulation_results)

        logging.info("Definite stop of the analysis. Time = %.2f s", execution_time)
