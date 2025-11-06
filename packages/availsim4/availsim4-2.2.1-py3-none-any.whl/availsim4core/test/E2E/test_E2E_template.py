# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

import glob
import os
import random
import shutil
import unittest

from availsim4core import main
from availsim4core.src.reader.xlsx.system_template_reader import SystemTemplateReader


class test_template(unittest.TestCase):
    param_scenario = [
        ["./availsim4core/test/E2E/input/template/simulation.xlsx",
         "./availsim4core/test/E2E/input/template/system.xlsx"],
    ]

    def test_runner(self):
        # randomize the order of the test execution to detect hidden dependencies
        random.shuffle(self.param_scenario)
        for simulation_file, system_file in self.param_scenario:
            with self.subTest():
                self._runner_E2E(simulation_file,
                                 system_file)

    def _runner_E2E(self,
                    simulation_file,
                    system_file):

        output_folder = "./availsim4core/test/E2E/output/template/"

        # Clean folder
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)

        # Run the main process
        main.start(simulation_file, system_file, output_folder)

        result_simulation_file_list = glob.glob(output_folder + "/*.xlsx")

        # read both file and then compare?
        input_system_template = SystemTemplateReader().read(system_file)
        output_system_template = SystemTemplateReader().read(result_simulation_file_list[0])

        self.assertEqual(input_system_template,output_system_template)

if __name__ == '__main__':
    unittest.main()
