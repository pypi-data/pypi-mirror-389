# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Main entry point for AvailSim4
"""

import logging
from datetime import datetime
from functools import partial
from multiprocessing import Pool

from availsim4core import configuration
from availsim4core.src.analysis import Analysis
from availsim4core.src.reader.xlsx.simulation_reader import SimulationReader
from availsim4core.src.reader.xlsx.system_template_reader import SystemTemplateReader
from availsim4core.src.runner.htcondor_runner import HTCondorRunner
from availsim4core.src.runner.local_runner import LocalRunner
from availsim4core.src.sensitivity_analysis.sensitivity_analysis import SensitivityAnalysis


def start(path_simulation: str,
          path_system: str,
          output_folder: str,
          path_sensitivity_analysis: str = "",
          htcondor: bool = False,
          htcondor_extra_argument: str = "",
          nb_processes: int = 1,
          custom_children_logic_path: str = "",
          stages_number: int = 1):
    """
    Starts the availsim simulation.
    If `HTCondor` is true it starts the software on the HTCondor cluster.
    """

    user_defined_paths = {
        "simulation": path_simulation,
        "system": path_system,
        "sensitivity_analysis": path_sensitivity_analysis,
        "output_folder": output_folder,
        "children_logic": custom_children_logic_path
    }

    paths = configuration.parse_user_paths(user_defined_paths)

    initial_simulation = SimulationReader().read(paths["simulation"], stages_number)
    initial_system_template = SystemTemplateReader(paths["children_logic"]).read(paths["system"])

    analysis_list = [Analysis(0, initial_system_template, initial_simulation)]

    if paths["sensitivity_analysis"]:
        # init the list of systems to be simulated

        sensitivity_analysis = SensitivityAnalysis(initial_simulation, initial_system_template)
        analysis_list = sensitivity_analysis.generate_analysis_list(paths["sensitivity_analysis"])

    if htcondor:
        HTCondorRunner(paths["output_folder"],
                       analysis_list[0].simulation.maximum_execution_time,
                       htcondor_extra_argument,
                       paths["children_logic"]).run(analysis_list)
    else:
        if nb_processes == 1:
            for analysis in analysis_list:
                LocalRunner.run(paths["output_folder"], analysis)
        else:
            partial_function = partial(LocalRunner.run, paths["output_folder"])
            with Pool(processes=nb_processes) as pool:
                pool.map(partial_function, analysis_list)


def main():
    """
    Entry point of Availsim.
    """

    (simulation,
     system,
     sensitivity_analysis,
     output_folder,
     htcondor,
     htcondor_extra_argument,
     nb_processes,
     custom_children_logic_path,
     stages_number) = configuration.init()

    logging.info("- Start simulating -")

    start_time = datetime.now()

    start(simulation,
          system,
          output_folder,
          sensitivity_analysis,
          htcondor,
          htcondor_extra_argument,
          nb_processes,
          custom_children_logic_path,
          stages_number)

    execution_time = (datetime.now() - start_time).total_seconds()
    logging.info("Total Availsim execution time: %.2f s", execution_time)
