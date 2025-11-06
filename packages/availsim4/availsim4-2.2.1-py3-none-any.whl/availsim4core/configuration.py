# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Code concerned with reading and parsing configuration options provided to AvailSim4.
"""

from __future__ import annotations

import argparse
import logging
import logging.config
import os
import pathlib
from typing import Dict, Optional

from importlib.metadata import version

LOGGING_CONFIG_FILE = pathlib.Path('logging/logging.conf')


def logger_config(debug: bool, output_folder: pathlib.Path) -> str:
    """
    Loads the configuration from the `LOGGING_CONFIG_FILE`.
    :param debug: If set the root logger level is set to debug
    :param output_folder: the output folder where the log will be written.
    :return: The path of the first `FileHandler` where the logs are written.
    """
    code_path = pathlib.Path(__file__).parent.absolute()
    logging.config.fileConfig(code_path / LOGGING_CONFIG_FILE, defaults={ 'output_folder': str(output_folder) })
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    return next((handler.baseFilename
                 for handler in logging.getLogger().handlers
                 if isinstance(handler, logging.FileHandler)), "")

def _check_number_of_stages(value):
    ival = int(value)
    if ival < 1:
        raise argparse.ArgumentTypeError("%s is an invalid argument. Number of stages has to be an"\
                                         "integer larger than 0.")
    return ival


def parser_config():
    """
    Read arguments provided by the user in the commandline
    """
    parser = argparse.ArgumentParser(description="running AvailSim4 -")

    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {version("availsim4")}')

    parser.add_argument('--simulation', type=str, required=True,
                        help='parameters of the algorithm')

    parser.add_argument('--system', type=str, required=True,
                        help='system file to simulate')

    parser.add_argument('--sensitivity_analysis', type=str, required=False,
                        help='sensitivity analysis file to explore',
                        default="")

    parser.add_argument('--children_logic', type=str, required=False,
                        help='python file defining a custom children logic',
                        default="")

    parser.add_argument('--HTCondor', default=False, action='store_true',
                        help='if the flag is present, then HTCondor is used to '
                             'run the different jobs of the sensitivity analysis')

    parser.add_argument('--HTCondor_extra_argument', type=str, required=False, default="",
                        help='possible extra argument used when submitting jobs '
                             'most likely a group/quota definition such as: '
                             '+AccountingGroup="group_u_XX.XXX"')

    parser.add_argument('--nb_processes', type=int, required=False,
                        help='number of processes used in the parallel part of the code '
                             '(over the sensitivity analysis when HTCondor is not used)',
                        default=1)

    parser.add_argument('--output_folder', type=str, required=True,
                        help='folder in which the results are exported')

    parser.add_argument('--debug', default=False, action='store_true',
                        help='if the flag is present, then debug mode is used in the logging file')

    parser.add_argument('--stages_number', type=_check_number_of_stages, default=1, required=False,
                        help='Number of stages in which sequential execution divides the overall' \
                             'workload, allowing for periodic exports.')


    return parser.parse_args()

def parse_user_paths(user_paths: Dict) -> Dict:
    """
    Parsing strings provided by a user to the pathlib.Path objects for better versatility of
    the paths handling across different operating systems.
    """
    paths: Dict[str, Optional[pathlib.Path]] = {}
    for name, path in user_paths.items():
        if path is not None and path != "":
            paths[name] = pathlib.Path(path)
        else:
            paths[name] = None
    return paths

def init():
    """
    Parse the command arguments and loads the logging configuration.
    :return tuple coming from given argument
    simulation_path, system_path, sensitivity_analysis_path, output_folder, HTCondor, nb_process
    """
    args = parser_config()

    os.makedirs(args.output_folder, exist_ok=True)

    log_file_path = logger_config(args.debug, pathlib.Path(args.output_folder))

    logging.info("- Availsim4 - version: %s", version("availsim4"))
    logging.info("- Init configuration -")

    if args.debug:
        if log_file_path == "":
            logging.error("DEBUG mode activated but logging file not defined or misconfigured.")
        logging.info("DEBUG mode activated -> Check: %s", log_file_path)

    logging.debug("Arguments: \nsimulation: %s - system: %s - sensitivity analysis: %s - "
                  "output_folder: %s - HTCondor: %s - HTCondor_extra_argument: %s - "
                  "nb_processes: %s - children_logic: %s - stages_number: %s", args.simulation, args.system,
                  args.sensitivity_analysis, args.output_folder, args.HTCondor,
                  args.HTCondor_extra_argument, args.nb_processes, args.children_logic, args.stages_number)

    return (args.simulation,
            args.system,
            args.sensitivity_analysis,
            args.output_folder,
            args.HTCondor,
            args.HTCondor_extra_argument,
            args.nb_processes,
            args.children_logic,
            args.stages_number)
