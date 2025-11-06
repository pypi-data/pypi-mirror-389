# SPDX-License-Identifier: GPL-3.0-only
# (C) Copyright CERN 2021. All rights not expressly granted are reserved.

"""
Module for a factory of Failure objects
"""

import logging

from availsim4core.src.context.system.failure import Failure, FailureType
from availsim4core.src.context.system.system_utils import SystemUtils


class FailureFactoryError(Exception):
    """
    Error thrown when the type of a failure defined by the user does not match any failure name listed in the framework
    """


def build(failure_mode_type_of_failure: str) -> Failure:
    """
    This function returns a new Failure object of the type defined as the 1st argument
    """
    failure_mode = SystemUtils.extract_name_of_function_from_string(failure_mode_type_of_failure)
    if failure_mode in [f.value for f in FailureType]:
        return Failure(FailureType[failure_mode])

    message = f"Wrong type of failure : {failure_mode_type_of_failure} not found"
    logging.exception(message)
    raise FailureFactoryError(message)
