# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""Module for the HTCondor Runner.

HTCondor Runner is part of the AvailSim4 framework which supports swift deployment of the framework on the nodes of the
HTCondor cluster. HTCondor is a system for managing computing grid's workloads - for more information, see [1].

[1] https://htcondor.org/htcondor/documentation/
"""

import logging
import os
from datetime import datetime
import importlib.resources
import pathlib
from typing import Dict, List, Tuple, Type, Optional
from string import Template

from availsim4core.src.analysis import Analysis
from availsim4core.src.exporter.input_file_exporter import InputFileExporter
from availsim4core.src.exporter.xlsx.analysis.xlsx_analysis_exporter import XLSXAnalysisExporter


class HTCondorRunner:
    """This class contains procedures which support running AvailSim4 on HTCondor nodes in parallel.

    AvailSim4 completes Monte Carlo simulations to obtain the results. Each iteration is a DES simulation, which does
    not depend on other iterations or any shared information. This class of simulations is easily parallelizable --
    multiple iterations differ in just the random number generator seed.

    To facilitate multi-node processing, this module prepares and triggers HTCondor jobs. First, it produces a structure
    of directories which will be used by individual nodes to run separate jobs - and, eventually, to store the results.
    The structure is the following (assuming standard XLSXAnalysisExporter is used for copying the structure):

        - output/
            | - run___*___0/
            | | - run.sh
            | | - sub.sub
            | | - system.xlsx
            | | - simulation .xlsx
            | - run___*___1/
            | | - run.sh
            | | ...
            | - sub.sub
            | - run.sh

    In the top level `output` folder there are two files: sub.sub is a submission script for HTCondor which specifies
    paramaters that will configure all of the jobs on the grid and run.sh which will be the entry point for each
    individual job (specified in `sub.sub` file), making them enter appropriate subdirectories and running individual
    run scripts.

    The number at the end of the `run___*` directories identifies data for each individual job -- since each is assigned
    a consecutive number. Inside them, there is a number of input files:

    - `run.sh` configures Python and starts AvailSim4 with appropriate parameters,
    - 'sub.sub' is an individual submission script which can be used to restart individual jobs.

    After the input/ouptut directory structure is ready, the module proceeds to submit the jobs to the scheduler, by
    submitting the top-level `sub.sub` to the scheduler using `condor_submit` command. Each job will then start running
    by executing the top-level run.sh file, which instructs it to enter the dedicated `run__*` directory - identifying
    the specific one by the ProcId number (each jobs gets a unique number in the range from 0 to the total number of
    jobs) - and running the run.sh file which is there. That script sources required dependencies and starts local
    AvailSim4 instances with the inputs and outputs pointing to the specific `run__*` folder from which it is started.

    Results of the jobs will appear in the `run___*` directories: `simulation_result_*`, `out.txt`, `log.txt` and
    `err.txt`. The latter three files are standard, error and logging outputs copied from each job;
    `simulation_result_*` represents all results produced by the AvailSim4 instance.

    Args:
        root_output_folder_location:
            Identifies the path (pathlib.Path) to the directory which is supposed to store all of the computing results.
        max_runtime:
            A user's expectation of the maximum total time for an individual job to finish. This parameter is passed to
            the HTCondor scheduler, which uses it to determine the queue of jobs to execute. Setting it too low will
            result in cutting the job off prematurely, however a value which is too high might delay scheduling the
            execution (as it will have lower priority). The value eventually passed on to the scheduler is extended by
            10% and additional 10 seconds (accounting for sourcing of CVMFS's Python and other dependencies).
        htcondor_extra_argument:
            HTCondor accepts extra arguments. In principle, this field was put in place to make it possible to pass the
            accounting identifier to the scheduler. However, nothing stands in a way of passing in the same way other
            arguments which will be added to the submission file.
        children_logic: str
        exporter:
            Exporter to be used to save simulation and system files for each job. The module creates a copy of input
            files for each job -- since those are exported from AvailSim4 code, it requires an appropriate exporter to
            save the files.
    """

    def __init__(self, root_output_folder_location: pathlib.Path, max_runtime: int, htcondor_extra_argument: str = "",
                 children_logic: Optional[pathlib.Path] = None, exporter = None) -> None:
        if exporter is None:
            self.exporter: Type[InputFileExporter] = XLSXAnalysisExporter
        else:
            self.exporter: Type[InputFileExporter] = exporter
        self.root_output_folder = root_output_folder_location.resolve()
        self.max_runtime = int(max_runtime * 1.1 + 10)
        self.htcondor_extra_argument = htcondor_extra_argument
        self.python_dependencies_installation_location = pathlib.Path()
        self.date_time_label = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.children_logic = children_logic

    def _realize_template_file(self, resource_file_name: str, output_file_path: pathlib.Path,
                               mappings: Dict[str, str]) -> None:
        """Helper function which can be used to create custom files from templates. It opens a template file identified
        by the first parameter, replaces the placeholders with contents of the mappings parameter and saves the
        resulting file as the output file.

        Args:
            resource_file_name (str): name of the template file.
            output_file_path (pathlib.Path): the path to where the result file (filled in template) will be saved.
            mappings (Dict[str, str]): a dictionary with mappings of all keywords used in a given template.

        Raises:
            KeyError: This error is most likely caused by keywords used in a template but not defined in the mappings
            dictionary.
        """
        with importlib.resources.open_text("availsim4core.resources.script_templates", resource_file_name) as input_file:
            file_template = Template(input_file.read())

        file_content = file_template.substitute(mappings)

        with open(output_file_path, 'w', encoding='UTF-8') as output_file:
            try:
                output_file.writelines(file_content)
            except IOError as exc:
                logging.error("I/O error(%d): %s", exc.errno, exc.strerror )

    def _create_subdirectory(self, analysis_id: int) -> pathlib.Path:
        """Creates an individual job directory.

        Args:
            analysis_id:
                Parameter used to identify the subdirectory. If the parameter is the same across different calls to the
                method, it will attempt to create multiple subdirectories in the same location - accepting that they
                exist. It will not raise any exceptions.

        Returns:
            The path to the newly-created directory.
        """
        output_folder = self.root_output_folder / ("run___" + self.date_time_label + "___" + str(analysis_id))
        os.makedirs(output_folder, exist_ok=True)

        logging.debug("Created HTCondor output folder %s", output_folder)
        return output_folder

    def create_system_simulation_files(self, export_location: pathlib.Path,
                                       analysis: Analysis) -> Tuple[pathlib.Path, pathlib.Path]:
        """Creates system and simulation files for a given analysis object at the specified location.

        Args:
            export_location:
                The path (pathlib.Path) to the location where the simulation and system files are supposed to be created
            analysis:
                An object of the Analysis class which specifies the details of the analysis performed by the job
                corresponding to the selected directory.

        Returns:
            A tuple with two elements: paths to the created simulation and system files.
        """
        exporter = self.exporter(None, analysis, export_location, "")
        simulation_filename = exporter.export_simulation_to_file("simulation.xlsx")
        system_filename = exporter.export_system_to_file("system.xlsx")
        return simulation_filename, system_filename

    def create_jobs_bash_script(self, export_location: pathlib.Path, simulation_filename: pathlib.Path,
                                 system_filename: pathlib.Path):
        """Creates a bash script which will be executed by each HTCondor job to start AvailSim4 instance.

        Args:
            export_location:
                A path to the location where the output of the AvailSim4 instance is supposed to be stored. Generally,
                it should be the unique output directory (usually created with _create_subdirectory method).
            simulation_filename:
                A path to the simulation file to be used as an AvailSim4 parameter.
            system_filename:
                A path to the system file to be used as an AvailSim4 parameter.

        Returns:
            The path (pathlib.Path) to the location of the created file.
        """
        code_directory = pathlib.Path(os.path.dirname(__file__)).parent.parent.parent
        bash_filename = export_location / "run.sh"
        children_logic = "--children_logic " + str(self.children_logic) if self.children_logic is not None else ""

        script_parameters = {
            'path_to_python_dependencies': self.python_dependencies_installation_location,
            'system_file_location': system_filename,
            'simulation_file_location': simulation_filename,
            'code_location': code_directory,
            'output_folder': export_location,
            'other_availsim_arguments': children_logic
        }

        self._realize_template_file("single_job_template.sh", bash_filename, script_parameters)

        os.system(f"chmod +x {bash_filename}")
        return bash_filename

    def create_submission_script(self, export_location: pathlib.Path, bash_script_location: pathlib.Path):
        """Creates a submission file for an individual analysis.

        The script created by this method can be used on its own, e.g., to re-run some individual jobs. It will not be
        triggered automatically in the course of the standard HTCondor procedure.

        Args:
            export_location:
                The path (pathlib.Path) to the location where the AvailSim4 instance results are supposed to be stored.
            bash_script_location:
                The path (pathlib.Path) to the location of the bash script responsible for starting the specific
                AvailSim4 instance within the node.

        Returns:
            The path (pathlib.Path) to the location of the created file.
        """
        submission_file_location = export_location / "sub.sub"

        submission_parameters = {
            'bash_script_location': bash_script_location,
            'output_location': export_location / 'out.txt',
            'error_location': export_location / 'err.txt',
            'log_location': export_location / 'log.txt',
            'max_runtime': self.max_runtime,
            'htcondor_extra_argument': self.htcondor_extra_argument
        }

        self._realize_template_file("single_submission_template.sub", submission_file_location, submission_parameters)

        return submission_file_location

    def create_analysis_folder_structure(self, analysis: Analysis) -> None:
        """This method is an entry point to creating the inputs structure for an individual analysis instance.

        The method essentially calls other methods which: create the subdirectory, create system and simulation files,
        create an individual bash script for starting an individual instance and finally an individual submission file.
        The result of this function should look like this:

            - run___*___0/
                | - run.sh
                | - sub.sub
                | - system.xlsx
                | - simulation .xlsx

        Args:
            analysis:
                Analysis object for which the system and simulation files will be generated.
        """
        folder_location = self._create_subdirectory(analysis.id)
        simulation_filename, system_filename = self.create_system_simulation_files(folder_location, analysis)
        bash_script_location = self.create_jobs_bash_script(folder_location, simulation_filename, system_filename)
        _ = self.create_submission_script(folder_location, bash_script_location)

    def create_master_bash_file(self) -> pathlib.Path:
        """A function to create a master bash script file which will be used as entry point for each individual job on
        the grid.

        The script enters the appropriate directory, which is identified by the location filled in by this method and
        paramter "$1" which is the first argument of the script. In the master submission file, this argument is being
        set to the ProcId - i.e., each job gets a unique, consecutive number. It is used to connect jobs with inputs.

        Returns:
            The path (pathlib.Path) to the location of the created file.
        """
        master_bash_filename = self.root_output_folder / "run.sh"
        script_parameters = {
            'output_location': self.root_output_folder
        }

        self._realize_template_file("master_job_template.sh", master_bash_filename, script_parameters)
        os.system(f"chmod +x {master_bash_filename}")
        return master_bash_filename

    def create_master_submission_file(self, master_bash_filename: pathlib.Path, n_analyses: int) -> pathlib.Path:
        """A function to create a master submission file which will be used to trigger jobs on HTCondor.

        This function fills the master submission tempate with parameters, saves the file and returns the path to its
        location.

        Args:
            master_bash_filename:
                A path (pathlib.Path) to the master bash script which will be submitted as the main executable in the
                master submission file.
            n_analyses:
                Number of analyses which will be run in parallel. It should correspond to the number of output
                directories.

        Returns:
            The path (pathlib.Path) to the location of the created file.
        """
        master_submission_filename = self.root_output_folder / "sub.sub"

        output_folder = self.root_output_folder / ("run___" + self.date_time_label + "___" + "$(ProcId)")
        submission_parameters = {
            'bash_script_location': master_bash_filename,
            'output_location': output_folder / 'out.txt',
            'error_location': output_folder / 'err.txt',
            'log_location': output_folder / 'log.txt',
            'max_runtime': self.max_runtime,
            'htcondor_extra_argument': self.htcondor_extra_argument,
            'n_parallel': n_analyses
        }
        self._realize_template_file("master_submission_template.sub", master_submission_filename, submission_parameters)
        return master_submission_filename

    def submit_request_to_htcondor(self, master_submission_filename: pathlib.Path) -> None:
        """A function to trigger the HTCondor jobs.

        Performs two operations: opens the output directory and submits the submission file (location of which is
        provided as the argument) to the HTCondor scheduler.

        Args:
            master_submission_filename:
                A path (pathlib.Path) to the master submission file which will be submitted to HTCondor.
        """
        command = "cd " + str(self.root_output_folder) + "; condor_submit " + str(master_submission_filename)
        logging.debug("Executing HTCondor command %s", command)
        os.system(command)

    def run(self, analysis_list: List[Analysis]) -> None:
        """This function prepares inputs and triggers the jobs on the HTCondor.

        As its first step, it iterates through the list of analyses and creates a unique output folder for each one.

        Args:
            analysis_list:
                This is a list of Analysis objects which will be run in separate jobs on HTCondor.
        """
        for analysis in analysis_list:
            self.create_analysis_folder_structure(analysis)

        master_bash_filename = self.create_master_bash_file()
        master_submission_filename = self.create_master_submission_file(master_bash_filename, len(analysis_list))
        self.submit_request_to_htcondor(master_submission_filename)
