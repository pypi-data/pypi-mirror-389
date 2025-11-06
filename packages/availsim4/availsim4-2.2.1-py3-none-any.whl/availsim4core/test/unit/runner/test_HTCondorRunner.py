# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for testing the code of HTCondorRunner class.
"""

import glob
import os
import pathlib
import unittest
from shutil import rmtree
from unittest.mock import MagicMock

import pytest
from availsim4core.src.runner.htcondor_runner import HTCondorRunner

class test_HTCondorRunner(unittest.TestCase):
    """Class for testing the individual methods of the HTCondorRunner class. Primarily checking the correctness of the
    generated files and structure of catalogues."""
    TEST_MAX_RUNTIME_VALUE = 10

    def setUp(self) -> None:
        self.temp_dir = "./temp"
        os.makedirs(self.temp_dir, exist_ok = True)

    def tearDown(self) -> None:
        rmtree(self.temp_dir)

    @pytest.fixture(autouse=True)
    def runner(self):
        self.runner = HTCondorRunner(pathlib.Path("temp/"), self.TEST_MAX_RUNTIME_VALUE, "Extra Argument")
        self.runner.exporter.export_simulation_to_file = \
                                        MagicMock(return_value = pathlib.Path("test/output/location/simulation.xlsx"))
        self.runner.exporter.export_system_to_file = \
                                            MagicMock(return_value = pathlib.Path("test/output/location/system.xlsx"))

    @pytest.fixture(autouse=True)
    def analysis(self):
        self.analysis = MagicMock()
        self.analysis.id = 10

    def test_create_system_simulation_files(self):
        """Test of the method creating system and simulation files for a given Analysis object in the directory
        specified as the argument.
        """
        simulation_path, system_path = self.runner.create_system_simulation_files(pathlib.Path("test/output/location/"),
                                                                                self.analysis)

        self.runner.exporter.export_simulation_to_file.assert_called_once()
        self.runner.exporter.export_system_to_file.assert_called_once()

        assert str(simulation_path) == str(pathlib.Path("test/output/location/simulation.xlsx"))
        assert str(system_path) == str(pathlib.Path("test/output/location/system.xlsx"))

    def test_create_jobs_bash_script(self):
        """Test of the individual job bash script creation"""
        bash_filpath = self.runner.create_jobs_bash_script(pathlib.Path(self.temp_dir),
                                                           pathlib.Path("/path/to/simulation.xlsx"),
                                                           pathlib.Path("/path/to/system.xlsx"))
        with open(bash_filpath, "r", encoding="utf-8") as file:
            saved_content = file.read()
        os.remove(bash_filpath)

        self.assertIn("python ", saved_content)
        self.assertIn("availsim4.py", saved_content)
        self.assertIn("export PYTHONNOUSERSITE=1", saved_content)
        self.assertIn(" --system " + str(pathlib.Path("/path/to/system.xlsx")), saved_content)
        self.assertIn(" --simulation " + str(pathlib.Path("/path/to/simulation.xlsx")), saved_content)
        self.assertIn(" --output_folder temp", saved_content)

    def test_create_jobs_bash_script_with_children_logic(self):
        """Test of the individual job bash script creation with the children logic file"""
        runner = HTCondorRunner(pathlib.Path("temp/"), self.TEST_MAX_RUNTIME_VALUE, "Extra Argument",
                                pathlib.Path("/path/to/children/logic.py"))
        runner.exporter.export_simulation_to_file = \
                                        MagicMock(return_value = pathlib.Path("test/output/location/simulation.xlsx"))
        runner.exporter.export_system_to_file = \
                                            MagicMock(return_value = pathlib.Path("test/output/location/system.xlsx"))
        bash_filpath = runner.create_jobs_bash_script(pathlib.Path(self.temp_dir),
                                                      pathlib.Path("/path/to/simulation.xlsx"),
                                                      pathlib.Path("/path/to/system.xlsx"))
        with open(bash_filpath, "r", encoding="utf-8") as file:
            saved_content = file.read()
        os.remove(bash_filpath)

        self.assertIn("python ", saved_content)
        self.assertIn("availsim4.py", saved_content)
        self.assertIn("export PYTHONNOUSERSITE=1", saved_content)
        self.assertIn(" --system " + str(pathlib.Path("/path/to/system.xlsx")), saved_content)
        self.assertIn(" --simulation " + str(pathlib.Path("/path/to/simulation.xlsx")), saved_content)
        self.assertIn(" --output_folder temp", saved_content)
        self.assertIn(" --children_logic " + str(pathlib.Path("/path/to/children/logic.py")), saved_content)

    def test_create_submission_script(self):
        """Test of the HTCondor submission file creation"""
        bash_filpath = "/path/to/bash_script.sh"
        submission_filepath = self.runner.create_submission_script(pathlib.Path(self.temp_dir),
                                                           pathlib.Path(bash_filpath))
        with open(submission_filepath, "r", encoding="utf-8") as file:
            saved_content = file.read()
        os.remove(submission_filepath)

        self.assertIn(f"executable = {pathlib.Path(bash_filpath)}", saved_content)
        self.assertIn("output = ", saved_content)
        self.assertIn("error = ", saved_content)
        self.assertIn("log = ", saved_content)
        self.assertIn("+MaxRuntime = ", saved_content)
        self.assertIn("queue", saved_content)
        self.assertIn("Extra Argument", saved_content)

    def test_create_analysis_folder_structure(self):
        """Test of the HTCondor input/output directory structure"""
        self.runner.create_analysis_folder_structure(self.analysis)

        # Assert that simulation and system files are copied to the directory
        self.runner.exporter.export_simulation_to_file.assert_called_once()
        self.runner.exporter.export_system_to_file.assert_called_once()

        # Check if the directory run___*__$1 is created properly
        self.assertTrue(len(glob.glob(str(self.runner.root_output_folder / "run___*_10/"))) == 1)

        # check if .sh and .sub files exist
        self.assertTrue(len(glob.glob(str(self.runner.root_output_folder / "run___*/*.sh"))) == 1)
        self.assertTrue(len(glob.glob(str(self.runner.root_output_folder / "run___*/*.sub"))) == 1)

    def test_create_master_bash_file(self):
        """Test of master bash script creation for HTCondor jobs"""
        master_bash_filename = self.runner.create_master_bash_file()
        with open(master_bash_filename, "r", encoding="utf-8") as file:
            saved_content = file.read()
        os.remove(master_bash_filename)

        self.assertIn("source ./run.sh", saved_content)
        self.assertIn("cd ", saved_content)
        self.assertIn("$1", saved_content)


    def test_create_master_submission_file(self):
        """Test of the master HTCondor submission file creation"""
        master_bash_filename = "temp/master_bash.sh"
        master_submission_filename = self.runner.create_master_submission_file(master_bash_filename, 10)
        with open(master_submission_filename, "r", encoding="utf-8") as file:
            saved_content = file.read()
        os.remove(master_submission_filename)

        self.assertIn(f"executable = {master_bash_filename}", saved_content)
        self.assertIn("output = ", saved_content)
        self.assertIn("error = ", saved_content)
        self.assertIn("log = ", saved_content)
        self.assertIn(f"+MaxRuntime = {int(self.TEST_MAX_RUNTIME_VALUE*1.1+10)}", saved_content)
        self.assertIn("queue 10", saved_content)
        self.assertIn("Extra Argument", saved_content)

    @unittest.mock.patch('os.system')
    def test_submit_request_to_htcondor(self, os_system):
        """Tests that function submitting to the HTCondor scheduler invokes command entering the root directory and
        submits the file specified as an argument"""
        self.runner.submit_request_to_htcondor("master_submission_test_file_name.sub")
        self.assertTrue(os_system.call_args.args[0].endswith("condor_submit master_submission_test_file_name.sub"))
